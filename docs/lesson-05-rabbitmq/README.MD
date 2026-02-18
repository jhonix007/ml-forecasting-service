# Lesson 05 — RabbitMQ + HF Workers

## Ветка
Если ветки ещё нет, создай:
```powershell
git checkout -b lesson-05-rabbitmq
```

## Запуск
Полный перезапуск:
```powershell
docker compose down -v
docker compose up -d --build --scale worker=2
docker compose ps
```

## Проверка Health
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost/health"
```
Ожидаемо:
```json
{"status":"ok"}
```

## RabbitMQ UI
Адрес: `http://localhost:15672`  
Логин/пароль: `guest / guest`

Проверь:
- очередь `ml_tasks` существует
- подключены consumers (минимум 2)

## Тестовый запрос (POST /predict)
```powershell
$payload = @{
  model = "hf-timeseries"
  features = @{
    series = @(10,12,11,13,15,14)
    horizon = 5
  }
  timestamp = (Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6

$r = Invoke-RestMethod -Method Post -Uri "http://localhost/predict" `
  -ContentType "application/json" -Body $payload
$r.task_id
```

## Проверка результата (GET /predictions/{task_id})
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost/predictions/$($r.task_id)" | ConvertTo-Json -Depth 10
```
Ожидаемо:
```json
{
  "task_id": "...",
  "status": "SUCCESS",
  "prediction": [ ... ],
  "worker_id": "...",
  "error": null,
  "created_at": "..."
}
```

## Проверка результата в БД
```powershell
docker compose exec database psql -U postgres -d postgres -c "select task_id, model, status, worker_id, prediction, created_at from ml_task_results order by created_at desc limit 10;"
```

## Round-robin между воркерами
Отправь 10 задач и проверь, что `worker_id` чередуются:
```powershell
1..10 | ForEach-Object {
  $payload = @{
    model = "hf-timeseries"
    features = @{ series = @(10,12,11,13,15,14); horizon = 5 }
    timestamp = (Get-Date).ToString("o")
  } | ConvertTo-Json -Depth 6

  $r = Invoke-RestMethod -Method Post -Uri "http://localhost/predict" `
    -ContentType "application/json" -Body $payload
  Start-Sleep -Milliseconds 200
  Invoke-RestMethod -Method Get -Uri "http://localhost/predictions/$($r.task_id)"
}
```

## Логи воркеров
```powershell
docker compose logs -f worker
```
