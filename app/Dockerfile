FROM python:3.12-slim

WORKDIR /app

# Минимум для запуска приложения (заглушка)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

# Пакет app лежит в /app/app (volume монтирует ./app/src -> /app)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]