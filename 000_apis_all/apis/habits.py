from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from context import AppContext

router = APIRouter(prefix="/habits", tags=["habits"])


def register(ctx: AppContext):
    Base = ctx.Base
    SessionLocal = ctx.SessionLocal
    app = ctx.app

    class Habit(Base):
        __tablename__ = "habits"

        id = Column(Integer, primary_key=True)
        name = Column(String)

    class HabitCreate(BaseModel):
        name: str

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @router.post("/")
    def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
        obj = Habit(name=habit.name)
        db.add(obj)
        db.commit()
        return obj

    @router.get("/")
    def list_habits(db: Session = Depends(get_db)):
        return db.query(Habit).all()

    app.include_router(router)