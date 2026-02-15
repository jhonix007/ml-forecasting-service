# Lesson 04 — REST API + Auth + Wallet + Predictions

## Что реализовано
- JWT-аутентификация:
  - `POST /auth/register` — регистрация, возвращает `access_token`
  - `POST /auth/login` — логин, возвращает `access_token`
- Баланс пользователя:
  - `GET /balance` — показывает баланс текущего пользователя
- Предикт:
  - `POST /predict` — валидирует данные, списывает кредиты, делает forecast, сохраняет результат в БД и возвращает `task_id`
- История предиктов:
  - `GET /predictions` — список всех предиктов текущего пользователя
  - `GET /predictions/{id}` — конкретный предикт по id

## Как запустить
```bash
docker compose up -d --build

Проверка здоровья:
Invoke-RestMethod -Method Get -Uri "http://localhost/health"


Auth (JWT):
Регистрация:
$body = @{ email="u1@gmail.com"; password="123456" } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost/auth/register" -ContentType "application/json" -Body $body).access_token
$headers = @{ Authorization = "Bearer $token" }

Логин:
$body = @{ email="u1@gmail.com"; password="123456" } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost/auth/login" -ContentType "application/json" -Body $body).access_token
$headers = @{ Authorization = "Bearer $token" }

Получить model_id (из seed):
$modelId = (docker compose exec -T app python -c "from sqlalchemy import select; from app.infrastructure.db.session import get_session; from app.infrastructure.db.orm_models import MLModelORM; s=next(get_session()); m=s.scalar(select(MLModelORM)); print(m.id)").Trim()
$modelId


A7 Проверка руками:
POST /predict:
$payload = @{ model_id=$modelId; horizon=5; values=@(10,12,11,13,15,14) } | ConvertTo-Json -Depth 5
$pred = Invoke-RestMethod -Method Post -Uri "http://localhost/predict" -ContentType "application/json" -Headers $headers -Body $payload
$pred | ConvertTo-Json -Depth 10

GET /predictions:
Invoke-RestMethod -Method Get -Uri "http://localhost/predictions" -Headers $headers | ConvertTo-Json -Depth 20

GET /predictions/{id}:
$taskId = $pred.task_id
Invoke-RestMethod -Method Get -Uri "http://localhost/predictions/$taskId" -Headers $headers | ConvertTo
