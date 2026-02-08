# Lesson 02 — Structure + Docker Compose

## Цель
Подготовить воспроизводимый старт инфраструктуры проекта и базовую структуру backend-приложения.

## Что реализовано
В `docker-compose.yml` описаны 4 сервиса:

1. **app** — backend-приложение  
   - конфигурация через `env_file: ./app/.env`  
   - исходники подключаются через `volumes`  
   - порты наружу не пробрасываются (доступ только через web-proxy)

2. **web-proxy** — Nginx reverse proxy  
   - `depends_on: app`  
   - проброс портов `80:80` и `443:443`  
   - проксирование запросов на `app:8000` (конфиг в `web-proxy/nginx.conf`)

3. **rabbitmq** — брокер сообщений (RabbitMQ Management)  
   - проброс портов `5672` (AMQP) и `15672` (UI)  
   - включён автоперезапуск при сбоях: `restart: on-failure`  
   - данные сохраняются в volume (persist очередей)

4. **database** — PostgreSQL  
   - конфигурация через переменные окружения  
   - данные сохраняются в volume (persist БД)

> Примечание (Windows + Docker Desktop): для RabbitMQ/Postgres используются **named volumes** (из-за проблем с правами файлов при bind-mount на Windows, например `.erlang.cookie`).

## Структура проекта
- `app/` — Dockerfile, .env, исходники приложения (`app/src/app/...`)
- `web-proxy/` — Dockerfile и конфигурация Nginx
- `docker-compose.yml` — описание инфраструктуры
- `docs/lesson-02-structure-docker/` — документация по заданию

## Запуск
```bash
docker compose up --build


## Проверка
- http://localhost/health
- http://localhost:15672 (guest/guest)