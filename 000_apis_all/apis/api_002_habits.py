from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from datetime import datetime

from context import AppContext


router = APIRouter(prefix="/habits", tags=["habits"])


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

    class Habit(Base):
        __tablename__ = "habits"
        id = Column(Integer, primary_key=True)
        type = Column(String, index=True)
        description = Column(String, index=True)
        when = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)

    class HabitCreate(BaseModel):
        type: str
        description: str
        when: str

    class HabitRead(HabitCreate):
        id: int
        created_at: datetime

        class Config:
            from_attributes = True

    @router.post("/", response_model=HabitRead)
    def create(data: HabitCreate, db: Session = Depends(get_db)):
        obj = Habit(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/", response_model=List[HabitRead])
    def list(db: Session = Depends(get_db)):
        return db.query(Habit).order_by(Habit.created_at.desc()).all()

    app.include_router(router)