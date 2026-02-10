# Moscow Managing Companies API

Django REST API для курсового проекта по анализу управляющих организаций Москвы на основе открытых данных.

## Что реализовано

Обязательные endpoint'ы:

- `GET /managing-companies/`
- `GET /managing-companies/suggestions/`
- `GET /managing-companies/{id}/`
- `GET /managing-companies/{id}/history/`
- `GET /managing-companies/{id}/similar/`
- `GET /managing-companies/{id}/benchmark/`
- `GET /managing-companies/{id}/insights/`
- `POST /comparisons/`
- `GET /reference/adm-areas/`
- `GET /reference/years/`

Очень желательно:

- `GET /analytics/districts/`
- `GET /analytics/ranking/`

По желанию:

- `POST /auth/register/`
- `POST /auth/login/`
- `POST /auth/refresh/`
- `GET /auth/me/`

## Структура проекта

- `companies` — модели, аналитика по организациям, сравнение, импорт данных
- `analytics_api` — сводная аналитика по округам и ранжированию
- `users` — регистрация и профиль пользователя
- `config` — настройки Django и маршрутизация

## Быстрый запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Использование PostgreSQL

По умолчанию используется SQLite для быстрого старта. Для курсового под требования преподавателя переключи БД на PostgreSQL через `.env`:

```env
DB_ENGINE=postgresql
POSTGRES_DB=moscow_mgmt_api
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

## Импорт данных

Поддерживается импорт трех датасетов и автоматическое объединение по `INN + Year`.

```bash
python manage.py import_open_data \
  --dataset-1 path/to/dataset1.json \
  --dataset-2 path/to/dataset2.json \
  --dataset-3 path/to/dataset3.json \
  --clear
```

Команда принимает JSON-массивы, JSON-объекты с ключом `data` и JSONL.

## Примеры запросов

```bash
curl "http://127.0.0.1:8000/managing-companies/?year=2024&search=Жилищник"
curl "http://127.0.0.1:8000/managing-companies/suggestions/?query=Жилищ"
curl "http://127.0.0.1:8000/managing-companies/12/?year=2024"
curl "http://127.0.0.1:8000/managing-companies/12/history/"
curl "http://127.0.0.1:8000/managing-companies/12/similar/?year=2024&limit=5"
curl "http://127.0.0.1:8000/managing-companies/12/benchmark/?year=2024"
curl "http://127.0.0.1:8000/managing-companies/12/insights/?year=2024"
curl -X POST "http://127.0.0.1:8000/comparisons/" \
  -H "Content-Type: application/json" \
  -d '{"company_ids": [12, 45, 77], "year": 2024}'
```

## Логика аналитики

В проекте рассчитываются пользовательские метрики:

- нарушения на 1 дом
- штрафы на 1 дом
- штрафы на 1000 кв. м
- предписания на 1 дом
- протоколы на 1 дом
- расторгнутые договоры на 100 домов
- доля просроченных мероприятий
- интегральный индекс проблемности
- индекс стабильности по годам

## Технологии

- Django
- Django REST Framework
- Simple JWT
- django-cors-headers
- PostgreSQL / SQLite
