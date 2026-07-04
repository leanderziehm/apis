from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Session
from datetime import datetime

from context import AppContext


router = APIRouter(prefix="/events", tags=["events"])


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

    class Event(Base):
        __tablename__ = "events"
        id = Column(Integer, primary_key=True)
        text = Column(String, index=True)
        created_at = Column(DateTime, default=datetime.utcnow)

    class EventCreate(BaseModel):
        text: str

    class EventRead(EventCreate):
        id: int
        created_at: datetime

        class Config:
            from_attributes = True

    @router.post("/", response_model=EventRead)
    def create_event(data: EventCreate, db: Session = Depends(get_db)):
        obj = Event(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/", response_model=list[EventRead])
    def list_events(limit: int = 100, db: Session = Depends(get_db)):
        return db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()

    app.include_router(router)