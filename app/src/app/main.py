import os
from fastapi import FastAPI

app = FastAPI(title="ML Forecasting Service (skeleton)")

@app.get("/health")
def health():
    """
    Минимальная проверка, что сервис стартовал и видит окружение.
    Доступен снаружи через Nginx: http://localhost/health
    """
    return {
        "status": "ok",
        "db_host": os.getenv("DB_HOST"),
        "rabbitmq_host": os.getenv("RABBITMQ_HOST"),
    }