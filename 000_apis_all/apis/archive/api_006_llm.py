import time
from typing import List, Dict, Optional
import os
import httpx

from fastapi import APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Float, UniqueConstraint
from sqlalchemy.orm import Session

from context import AppContext


def register(ctx: AppContext):
    Base = ctx.Base
    SessionLocal = ctx.SessionLocal
    app = ctx.app

    # -------------------------------------------------
    # CORS
    # -------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------
    # Config
    # -------------------------------------------------
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    # -------------------------------------------------
    # DB Model
    # -------------------------------------------------
    class ChatCache(Base):
        __tablename__ = "chat_cache"

        id = Column(Integer, primary_key=True, index=True)
        model = Column(String, index=True)
        system_prompt = Column(Text, nullable=True)
        message = Column(Text, nullable=False)
        response = Column(Text, nullable=False)
        timestamp = Column(Float, default=time.time)

        __table_args__ = (
            UniqueConstraint("model", "system_prompt", "message", name="uq_cache"),
        )

    Base.metadata.create_all(bind=ctx.engine)

    # -------------------------------------------------
    # DB Dependency
    # -------------------------------------------------
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # -------------------------------------------------
    # Model Pool
    # -------------------------------------------------
    class ModelState:
        def __init__(self, model_id: str):
            self.model_id = model_id
            self.disabled_until: Optional[float] = None

        def is_available(self) -> bool:
            if self.disabled_until is None:
                return True
            if time.time() >= self.disabled_until:
                self.disabled_until = None
                return True
            return False

        def disable(self, retry_after: int):
            self.disabled_until = time.time() + retry_after

    class ModelPool:
        def __init__(self, models: List[str]):
            self.models_order = models.copy()
            self.models = {m: ModelState(m) for m in models}

        def get_available_models(self):
            return [m for m in self.models_order if self.models[m].is_available()]

        def reorder(self, new_order: List[str]):
            filtered = [m for m in new_order if m in self.models]
            remaining = [m for m in self.models_order if m not in filtered]
            self.models_order = filtered + remaining

    all_models = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b",
        "llama-3.1-8b-instant",
    ]

    model_pool = ModelPool(all_models)

    # -------------------------------------------------
    # Groq Client
    # -------------------------------------------------
    class RateLimitError(Exception):
        def __init__(self, retry_after: int):
            self.retry_after = retry_after

    class GroqClient:
        def __init__(self, pool: ModelPool):
            self.pool = pool

        def chat(self, messages: List[dict], model: Optional[str] = None):
            system_prompt = next((m["content"] for m in messages if m["role"] == "system"), None)
            user_message = next((m["content"] for m in messages if m["role"] == "user"), None)

            # cache lookup
            with SessionLocal() as db:
                cached = db.query(ChatCache).filter_by(
                    model=model or self.pool.get_available_models()[0],
                    system_prompt=system_prompt,
                    message=user_message,
                ).first()

                if cached:
                    return {
                        "model": cached.model,
                        "choices": [{"message": {"content": cached.response}}],
                    }

            models_to_try = [model] if model else self.pool.get_available_models()
            if not models_to_try:
                raise HTTPException(status_code=503, detail="No models available")

            for model_id in models_to_try:
                try:
                    response = self._call(model_id, messages)

                    # cache write
                    with SessionLocal() as db:
                        db.add(ChatCache(
                            model=model_id,
                            system_prompt=system_prompt,
                            message=user_message,
                            response=response["choices"][0]["message"]["content"],
                            timestamp=time.time()
                        ))
                        db.commit()

                    return response

                except RateLimitError as e:
                    self.pool.models[model_id].disable(e.retry_after)

            raise HTTPException(status_code=429, detail="All models rate limited")

        def _call(self, model_id: str, messages: List[dict]):
            payload = {"model": model_id, "messages": messages}

            with httpx.Client(timeout=30) as client:
                r = client.post(GROQ_API_URL, headers=HEADERS, json=payload)

            if r.status_code == 429:
                raise RateLimitError(int(r.headers.get("retry-after", 5)))

            if r.status_code >= 400:
                raise HTTPException(status_code=r.status_code, detail=r.text)

            return r.json()

    groq_client = GroqClient(model_pool)

    # -------------------------------------------------
    # Schemas
    # -------------------------------------------------
    class ChatRequestAuto(BaseModel):
        message: str
        system_prompt: Optional[str]

    class ChatRequestManual(BaseModel):
        message: str
        model: str
        system_prompt: Optional[str]

    class ReorderRequest(BaseModel):
        new_order: List[str]

    # -------------------------------------------------
    # Docs
    # -------------------------------------------------
    @app.get("/", include_in_schema=False)
    async def docs():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

    # -------------------------------------------------
    # Routes
    # -------------------------------------------------
    router = APIRouter()

    @router.get("/models/available")
    def available():
        return {"available_models": model_pool.get_available_models()}

    @router.post("/chat/auto")
    def chat_auto(req: ChatRequestAuto):
        messages = [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.message},
        ]
        res = groq_client.chat(messages)
        return {
            "model_used": res["model"],
            "response": res["choices"][0]["message"]["content"],
        }

    @router.post("/chat/manual")
    def chat_manual(req: ChatRequestManual):
        messages = [
            {"role": "system", "content": req.system_prompt},
            {"role": "user", "content": req.message},
        ]
        res = groq_client.chat(messages, model=req.model)
        return {
            "model_used": res["model"],
            "response": res["choices"][0]["message"]["content"],
        }

    @router.post("/models/reorder")
    def reorder(req: ReorderRequest):
        model_pool.reorder(req.new_order)
        return {"new_order": model_pool.models_order}

    @router.get("/models/best")
    def best():
        if not model_pool.models_order:
            return {"error": "no models"}
        m = model_pool.models_order[0]
        return {"model": m, "available": model_pool.models[m].is_available()}

    @router.get("/models/best-available")
    def best_available():
        available = model_pool.get_available_models()
        if not available:
            return {"error": "none available"}
        return {"model": available[0], "available": True}

    # -------------------------------------------------
    # Register router
    # -------------------------------------------------
    app.include_router(router)