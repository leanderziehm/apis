import os
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from apis import apis
from context import AppContext
from datetime import datetime, timezone

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL",None)

if DATABASE_URL == None:
    exit("Missing DATABASE_URL in .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

context = AppContext(
    app=app,
    engine=engine,
    SessionLocal=SessionLocal,
    Base=Base,
)

apis.register_all(context)

Base.metadata.create_all(bind=engine)



@app.get("/health")
def health():
    now_utc = datetime.now(timezone.utc)

    return {
        "status": "ok",
        "time-utc": now_utc.strftime("%d-%m-%Y-%H:%M:%S")
    }