from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import Session
from datetime import datetime

from context import AppContext


router = APIRouter(prefix="/measurements", tags=["measurements"])


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

    class Measurement(Base):
        __tablename__ = "measurements"
        id = Column(Integer, primary_key=True)
        text = Column(String, index=True)
        value = Column(Float)
        created_at = Column(DateTime, default=datetime.utcnow)

    class MeasurementCreate(BaseModel):
        text: str
        value: float

    class MeasurementRead(MeasurementCreate):
        id: int
        created_at: datetime

        class Config:
            from_attributes = True

    @router.post("/", response_model=MeasurementRead)
    def create(data: MeasurementCreate, db: Session = Depends(get_db)):
        obj = Measurement(**data.dict())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.get("/", response_model=List[MeasurementRead])
    def list(db: Session = Depends(get_db)):
        return db.query(Measurement).order_by(Measurement.created_at.desc()).all()

    app.include_router(router)