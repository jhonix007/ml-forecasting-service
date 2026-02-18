# Lesson 03 — ORM + PostgreSQL

## Что сделано
- Подключен PostgreSQL через SQLAlchemy ORM
- Таблицы: users, wallets, transactions, ml_models, predictions
- Реализованы операции:
  - создание пользователя
  - пополнение баланса (top_up)
  - списание кредитов (charge) + проверка остатка
  - получение истории транзакций
  - каталог ML моделей
- Seed (идемпотентный):
  - demo user: demo@local (balance=1000)
  - demo admin: admin@local (balance=5000)
  - базовые модели: BaselineForecastEngine 0.1, TimesFM 2.0

## Как запустить
docker compose up -d --build

## Проверка
- http://localhost/health
- CRUD/seed сценарий:
  docker compose exec app python -m app.scripts.demo_scenarios