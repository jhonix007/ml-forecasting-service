# Lesson 06 - Web UI

## Запуск
```powershell
docker compose down -v
docker compose up -d --build
```

## URLs
- Web UI: http://localhost/
- API base: http://localhost/api
- Swagger: http://localhost/api/docs

## Демо-сценарий
1. Регистрация: http://localhost/register
2. Вход: http://localhost/login
3. Проверка баланса: `/cabinet`
4. Пополнение баланса: `/cabinet`
5. Отправка прогноза: `/cabinet`
6. Просмотр истории: `/history`

## API endpoints, используемые UI
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/balance`
- `POST /api/balance/top-up`
- `POST /api/predict`
- `GET /api/predictions/{task_id}`
- `GET /api/history/transactions`
- `GET /api/history/predictions`

## Важно
- Фронтенд доступен на `/`, backend проксируется под `/api`.
- JWT хранится в localStorage (учебный проект).
- Horizon ограничен до 50 на backend. Если больше — будет автоматически уменьшен до 50.
