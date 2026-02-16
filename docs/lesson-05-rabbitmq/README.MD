# Lesson 05 — Async ML via RabbitMQ (publisher → broker → workers)

## Цель
Реализовать асинхронное взаимодействие системы с ML-сервисом через **RabbitMQ** в режиме **один издатель → несколько слушателей**.

- REST API принимает запрос `/predict`, создаёт задачу и публикует её в очередь `ml_tasks`
- Несколько воркеров читают задачи из очереди (round-robin), валидируют данные, считают предикт (mock), сохраняют результат
- Результат можно проверить через REST `/predictions/{task_id}` и/или напрямую в БД

---

## Архитектура

**Publisher (REST API)**
- `POST /predict`
  - принимает входные данные
  - генерирует `task_id`
  - сохраняет задачу в БД со статусом `PENDING`
  - публикует сообщение в RabbitMQ (`ml_tasks`)
  - возвращает `{ task_id }`

**RabbitMQ**
- одна очередь `ml_tasks`
- несколько consumers (воркеров)

**Workers**
- подписаны на `ml_tasks`
- получают сообщение
- валидируют входной JSON
- выполняют predict (mock)
- пишут результат в БД (`SUCCESS/FAILED`, `prediction`, `worker_id`, `error`)

**Status API**
- `GET /predictions/{task_id}` возвращает статус задачи

---

## Формат сообщения в очереди

```json
{
  "task_id": "uuid",
  "features": { "x1": 1.2, "x2": 5.7 },
  "model": "demo_model",
  "timestamp": "2026-01-01T12:00:00"
}

Запуск (Docker Compose)
1) Полный перезапуск
docker compose down -v
docker compose up -d --build --scale worker=2
docker compose ps

2) Проверка health
Invoke-RestMethod -Method Get -Uri "http://localhost/health"
Ожидаемо:

json
Копировать код
{ "status": "ok" }
RabbitMQ UI
URL: http://localhost:15672

login/pass: guest / guest

Проверь:

очередь ml_tasks существует

consumers подключены (минимум 2)

Ручное тестирование через REST
Если в проекте есть авторизация — сначала получаем JWT, иначе пропусти шаг с login.

1) Получить токен (если требуется)
$body = @{ email="u1@gmail.com"; password="123456" } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost/auth/login" -ContentType "application/json" -Body $body).access_token
$headers = @{ Authorization = "Bearer $token" }

2) Создать ML-задачу (POST /predict)
$payload = @{
  model = "demo_model"
  features = @{ x1 = 1.2; x2 = 5.7 }
} | ConvertTo-Json -Depth 5

$r = Invoke-RestMethod -Method Post -Uri "http://localhost/predict" -Headers $headers -ContentType "application/json" -Body $payload
$r
Ожидаемо:

json
Копировать код
{ "task_id": "....uuid...." }

3) Проверить статус и результат (GET /predictions/{task_id})
$taskId = $r.task_id
Invoke-RestMethod -Method Get -Uri "http://localhost/predictions/$taskId" -Headers $headers | ConvertTo-Json -Depth 10
Ожидаемо сначала:

json
Копировать код
{
  "task_id": "...",
  "status": "PENDING",
  "prediction": null,
  "worker_id": null,
  "error": null
}
Через небольшой промежуток:

json
{
  "task_id": "...",
  "status": "SUCCESS",
  "prediction": 6.9,
  "worker_id": "worker-1",
  "error": null
}

Проверка round-robin между воркерами
Отправить много задач и посмотреть, что worker_id меняется:

1..10 | %{
  $payload = @{ model="demo_model"; features=@{ x1 = $_; x2 = 5.7 } } | ConvertTo-Json -Depth 5
  $r = Invoke-RestMethod -Method Post -Uri "http://localhost/predict" -Headers $headers -ContentType "application/json" -Body $payload
  Start-Sleep -Milliseconds 200
  Invoke-RestMethod -Method Get -Uri "http://localhost/predictions/$($r.task_id)" -Headers $headers
}

Логи воркеров:
docker compose logs -f worker

Проверка результата в БД (опционально)
docker compose exec database psql -U postgres -d postgres -c "select task_id, prediction, worker_id, status, created_at from ml_task_results order by created_at desc limit 20;"
Типичные проблемы
502 Bad Gateway (nginx)
Обычно означает, что app контейнер упал или nginx не может достучаться до upstream.

Проверить:
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=200 web-proxy
App падает при импорте (Could not import module app.main)

Нужно смотреть traceback:
docker compose logs -f app
Worker не может подключиться к RabbitMQ (Connection refused)
RabbitMQ ещё не поднялся — помогает depends_on + retry (в воркере) и проверка:

docker compose ps
docker compose logs -f worker
