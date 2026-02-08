FROM python:3.12-slim

WORKDIR /app

# Минимум для запуска приложения (заглушка)
RUN pip install --no-cache-dir fastapi uvicorn

EXPOSE 8000

# Пакет app лежит в /app/app (volume монтирует ./app/src -> /app)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]