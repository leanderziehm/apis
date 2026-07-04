from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum as PyEnum

from context import AppContext


router = APIRouter(prefix="/timers", tags=["timers"])


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

    class TimerAction(str, PyEnum):
        START = "START"
        END = "END"

    class TimerEvent(Base):
        __tablename__ = "timer_events"
        id = Column(Integer, primary_key=True)
        text = Column(String, index=True)
        action = Column(Enum(TimerAction, name="timer_action"))
        created_at = Column(DateTime, default=datetime.utcnow)

    class TimerCreate(BaseModel):
        text: str
        action: TimerAction

    class TimerRead(TimerCreate):
        id: int
        created_at: datetime

        class Config:
            from_attributes = True

    @router.post("/", response_model=TimerRead)
    def create_timer(data: TimerCreate, db: Session = Depends(get_db)):
        obj = TimerEvent(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/", response_model=list[TimerRead])
    def list_timers(db: Session = Depends(get_db)):
        return db.query(TimerEvent).order_by(TimerEvent.created_at.desc()).all()

    app.include_router(router)