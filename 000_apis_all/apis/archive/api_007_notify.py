import os
import httpx

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from context import AppContext


def register(ctx: AppContext):
    app = ctx.app

    # -------------------------------------------------
    # Env config
    # -------------------------------------------------
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    if not CHAT_ID:
        raise RuntimeError("TELEGRAM_CHAT_ID is not set")

    TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # -------------------------------------------------
    # Schema
    # -------------------------------------------------
    class MessageIn(BaseModel):
        text: str

    # -------------------------------------------------
    # Router
    # -------------------------------------------------
    router = APIRouter()

    @router.post("/notify/me")
    async def send_message(payload: MessageIn):
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                TELEGRAM_URL,
                json={
                    "chat_id": CHAT_ID,
                    "text": payload.text,
                },
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=response.text,
            )

        return {"ok": True}

    # -------------------------------------------------
    # Register router
    # -------------------------------------------------
    app.include_router(router)