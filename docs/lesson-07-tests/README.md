# Lesson 07 - Сквозные тесты

## Локальный запуск
```powershell
pip install -r app/requirements.txt -r requirements-test.txt
set PYTHONPATH=app/src
pytest -q
```

## Запуск через Docker Compose
```powershell
docker compose up -d --build
docker compose run --rm -v ${PWD}:/workspace app bash -lc "pip install -r /workspace/app/requirements.txt -r /workspace/requirements-test.txt && PYTHONPATH=/workspace/app/src pytest -q /workspace/tests"
```

## Что покрыто тестами
- регистрация пользователя
- логин / повторный логин / неверный пароль
- получение баланса
- пополнение баланса
- predict при достаточном балансе (списание + история)
- predict при недостаточном балансе (без списаний)
- predict с невалидным payload (422, без списаний)
- история транзакций и история задач
