from dataclasses import dataclass
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, DeclarativeMeta


@dataclass
class AppContext:
    app: FastAPI
    engine: Engine
    SessionLocal: sessionmaker
    Base: DeclarativeMeta