from __future__ import annotations

from fastapi import FastAPI

from app.infrastructure.db.session import engine, SessionLocal
from app.infrastructure.db.base import Base
from app.infrastructure.db import orm_models  # noqa: F401
from app.infrastructure.db.seed import seed_data

from app.routes.auth import router as auth_router
from app.routes.balance import router as balance_router
from app.routes.history import router as history_router
from app.routes.predict import router as predict_router

app = FastAPI(title="ML Forecasting Service", version="0.1")

app.include_router(auth_router)
app.include_router(balance_router)
app.include_router(history_router)
app.include_router(predict_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_data(db)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}