import os
from fastapi import FastAPI

from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine, SessionLocal
from app.infrastructure.db import orm_models  # noqa: F401 (регистрация моделей)
from app.infrastructure.db.seed import seed_data

app = FastAPI(title="ML Forecasting Service (Lesson 03 ORM)")

@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok", "db_host": os.getenv("DB_HOST"), "rabbitmq_host": os.getenv("RABBITMQ_HOST")}
