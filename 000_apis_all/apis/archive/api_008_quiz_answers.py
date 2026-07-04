from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import Session
from datetime import datetime

import os
from dotenv import load_dotenv

from context import AppContext

load_dotenv()


def register(ctx: AppContext):
    Base = ctx.Base
    SessionLocal = ctx.SessionLocal
    app = ctx.app

    # -------------------------------------------------
    # DB Models
    # -------------------------------------------------

    class Answer(Base):
        __tablename__ = "answers"

        id = Column(Integer, primary_key=True)
        question_id = Column(String)
        username = Column(String)
        content = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Comment(Base):
        __tablename__ = "comments"

        id = Column(Integer, primary_key=True)
        question_id = Column(String)
        username = Column(String)
        content = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)

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
    # Swagger override
    # -------------------------------------------------
    @app.get("/", include_in_schema=False)
    async def docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="OCR API Docs"
        )

    # -------------------------------------------------
    # Router
    # -------------------------------------------------
    router = APIRouter()

    # =================================================
    # ANSWERS
    # =================================================

    @router.get("/answers/{question_id}")
    def get_answers(question_id: str, db: Session = next(get_db())):
        results = (
            db.query(Answer)
            .filter(Answer.question_id == question_id)
            .order_by(Answer.created_at.desc())
            .all()
        )

        return [
            {
                "username": r.username,
                "content": r.content,
                "created_at": r.created_at,
            }
            for r in results
        ]

    @router.post("/answers")
    def post_answer(payload: dict, db: Session = next(get_db())):
        obj = Answer(
            question_id=payload["question_id"],
            username=payload["username"],
            content=payload["content"],
            created_at=datetime.utcnow(),
        )

        db.add(obj)
        db.commit()
        return {"status": "ok"}

    # =================================================
    # COMMENTS
    # =================================================

    @router.get("/comments/{question_id}")
    def get_comments(question_id: str, db: Session = next(get_db())):
        results = (
            db.query(Comment)
            .filter(Comment.question_id == question_id)
            .order_by(Comment.created_at.asc())
            .all()
        )

        return [
            {
                "username": r.username,
                "content": r.content,
                "created_at": r.created_at,
            }
            for r in results
        ]

    @router.post("/comments")
    def post_comment(payload: dict, db: Session = next(get_db())):
        obj = Comment(
            question_id=payload["question_id"],
            username=payload["username"],
            content=payload["content"],
            created_at=datetime.utcnow(),
        )

        db.add(obj)
        db.commit()
        return {"status": "ok"}

    # -------------------------------------------------
    # Register router
    # -------------------------------------------------
    app.include_router(router)