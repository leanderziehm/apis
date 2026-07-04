from fastapi import FastAPI


from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
import os

# from sqlalchemy import create_engine
# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise RuntimeError("DATABASE_URL not set in .env")

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)
# Base = declarative_base()

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

numb = 1

@app.get("/", include_in_schema=False)
async def d():
    global numb
    numb += 1
    print(numb)
    return numb



@app.get("/d", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="OCR API Docs")


