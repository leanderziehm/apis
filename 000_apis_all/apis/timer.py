from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from context import AppContext

router = APIRouter(prefix="/timer", tags=["timer"])


def register(ctx: AppContext):
    Base = ctx.Base
    app = ctx.app

    class Timer(Base):
        __tablename__ = "timers"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        duration = Column(Integer)

    class TimerCreate(BaseModel):
        name: str
        duration: int

    @router.get("/")
    def list_timers():
        return [{"name": "study", "duration": 25}]

    @router.post("/")
    def create_timer(timer: TimerCreate):
        return timer.dict()

    app.include_router(router)