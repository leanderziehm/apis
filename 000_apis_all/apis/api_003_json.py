from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import Session
from datetime import datetime

from context import AppContext


router = APIRouter(prefix="/json", tags=["json"])


def register(ctx: AppContext):
    Base = ctx.Base
    SessionLocal = ctx.SessionLocal
    app = ctx.app

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    class Json(Base):
        __tablename__ = "json"
        id = Column(Integer, primary_key=True)
        text = Column(String, index=True)
        body = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)

    class JsonCreate(BaseModel):
        text: str
        body: dict

    class JsonRead(JsonCreate):
        id: int
        created_at: datetime

        class Config:
            from_attributes = True

    @router.post("/", response_model=JsonRead)
    def create(data: JsonCreate, db: Session = Depends(get_db)):
        obj = Json(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/", response_model=List[JsonRead])
    def list(db: Session = Depends(get_db)):
        return db.query(Json).order_by(Json.created_at.desc()).all()

    app.include_router(router)