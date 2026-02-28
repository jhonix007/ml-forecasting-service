# ML Forecasting Service

Учебный ML-сервис прогнозирования временных рядов с личным кабинетом пользователя (Web + REST) и асинхронной обработкой задач через RabbitMQ.
Пользователь загружает временной ряд и горизонт прогноза, сервис валидирует данные, ставит задачу в очередь, воркеры считают прогноз и сохраняют результат.

**Архитектура**
- `app` — FastAPI API (auth, balance, predict, history), хранение данных в Postgres.
- `database` — PostgreSQL.
- `rabbitmq` — брокер сообщений для задач прогнозирования.
- `worker` — читает очередь, валидирует данные, выполняет прогноз, пишет результат в БД.
- `web` — React UI (статический фронтенд).
- `web-proxy` — Nginx, проксирует `/api/*` в `app`, `/` — в `web`.

**Требования**
- Docker и Docker Compose (v2).
- Для локальных тестов: Python 3.12 + pip.

**Быстрый запуск (Docker)**
1. Подготовьте env-файлы:
```powershell
Copy-Item app\.env.example app\.env
Copy-Item database.env.example database.env
```
2. Запустите стек:
```powershell
docker compose up --build
```
3. Откройте:
- Web UI: `http://localhost/`
- API docs: `http://localhost/api/docs`
- RabbitMQ UI: `http://localhost:15672` (логин/пароль `guest`/`guest`)

Примечание: схема БД создаётся автоматически на старте `app`. Если `SEED_ENABLED=true`, добавляются тестовые данные.

**Проверка работоспособности (API)**
Базовый URL через Nginx: `http://localhost/api`. Прямой доступ к API: `http://localhost:8000`.

Примеры запросов (PowerShell + curl.exe):
```powershell
# health
curl.exe -s http://localhost/api/health

# register -> access_token
curl.exe -s -X POST "http://localhost/api/auth/register" `
  -H "Content-Type: application/json" `
  -d '{"email":"user@example.com","password":"test123"}'

# login -> access_token
curl.exe -s -X POST "http://localhost/api/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"email":"user@example.com","password":"test123"}'

# balance (нужен токен)
curl.exe -s "http://localhost/api/balance" `
  -H "Authorization: Bearer <token>"

# top-up
curl.exe -s -X POST "http://localhost/api/balance/top-up" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"amount":10}'

# predict (асинхронно) -> task_id
curl.exe -s -X POST "http://localhost/api/predict" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"model":"hf-timeseries","features":{"series":[1,2,3,4,5,6,7,8],"horizon":5}}'

# task status
curl.exe -s "http://localhost/api/predictions/<task_id>" `
  -H "Authorization: Bearer <token>"

# history
curl.exe -s "http://localhost/api/history/transactions" `
  -H "Authorization: Bearer <token>"
curl.exe -s "http://localhost/api/history/predictions" `
  -H "Authorization: Bearer <token>"
```

**Запуск воркеров в несколько экземпляров**
```powershell
docker compose up -d --build --scale worker=2
```
Если сервисы уже запущены, можно выполнить:
```powershell
docker compose up -d --scale worker=2
```

**Запуск тестов (локально)**
```powershell
python -m pip install -r app\requirements.txt -r requirements-test.txt
pytest -q
```

**Troubleshooting**
- `502 Bad Gateway` от `web-proxy`: подождите сборки `web`, проверьте `docker compose ps` и логи `docker compose logs -f app web`.
- `RabbitMQ unavailable` / HTTP 503 на `/predict`: убедитесь, что `rabbitmq` в статусе `healthy`.
- `402 Insufficient balance`: пополните баланс через `/balance/top-up`.
- Воркеры не обрабатывают задачи: проверьте `docker compose logs -f worker`. Первый запуск может долго скачивать модель HuggingFace.
- `ModuleNotFoundError: app` при локальном запуске: используйте Docker или запускайте из корня с `PYTHONPATH=app/src`.
- Порт `80` занят: поменяйте порт в `docker-compose.yml` для `web-proxy`.
