# Moderation Service Backend

FastAPI backend для сервиса модерации контента с асинхронной обработкой задач
через RabbitMQ + Celery и хранением результатов в PostgreSQL.

## Описание

Backend-часть системы модерации, предоставляющая REST API для обработки и
управления контентом. Сервис разделён на **Producer** (FastAPI — принимает
запросы и кладёт задачи в очередь) и **Consumer** (Celery Worker — забирает
задачи из очереди, вызывает классификатор, записывает результат в БД).

```
Клиент → Backend (Producer)  → RabbitMQ → Celery Worker (Consumer)  → Classifier
              │                                    │
              │  POST /classify → task_id          │ вызывает classifier HTTP
              │  GET /tasks/{id} → статус/результат │ пишет результат в БД
              │                                    │
              └──────── PostgreSQL ←───────────────┘
```

Backend **не ждёт** результатов классификации — он сразу возвращает `task_id`.
Результаты запрашиваются отдельно через `GET /tasks/{task_id}`.

## Технологии

- **Python 3.12+**
- **FastAPI** — веб-фреймворк (Producer)
- **Celery** — асинхронные задачи (Consumer)
- **RabbitMQ** — брокер сообщений
- **SQLAlchemy 2.0** — ORM
- **Alembic** — миграции БД
- **Pydantic v2** — валидация данных
- **PostgreSQL 15** — база данных
- **uv** — менеджер пакетов

## Структура проекта

```
backend/
├── app/
│   ├── api/
│   │   ├── router.py
│   │   └── schemas.py
│   ├── database/
│   │   ├── core.py       # Подключение к БД, сессии
│   │   ├── check.py      # Проверка и создание БД
│   │   └── seed.py
│   ├── celery_app.py     # Конфигурация Celery (брокер, сериализация)
│   ├── tasks.py          # Celery-задачи (Consumer-логика)
│   ├── config.py         # Настройки приложения (Pydantic Settings)
│   ├── main.py           # Точка входа FastAPI
│   ├── models.py
│   └── schemas.py
├── alembic
│   ├── versions/
│   └── env.py
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── .env
```

## Установка и запуск

### Через Docker (рекомендуется)

Backend запускается в составе общего docker-compose из корня проекта:

```bash
# Поднять всё: БД, RabbitMQ, Backend, Celery Worker, Classifier
docker-compose up -d

# Или отдельно backend + worker
docker-compose up -d backend celery_worker
```

Celery Worker запускается как отдельный контейнер с командой:

```bash
uv run celery -A app.celery_app worker --loglevel=info
```

### Локальная разработка

```bash
# Установка зависимостей
pip install uv
uv sync

# Запуск PostgreSQL и RabbitMQ
docker-compose up -d db rabbitmq

# Настройка окружения
cp .env.example .env
# Изменить PG_HOST=localhost и CELERY_BROKER_URL в .env

# Запуск FastAPI (Producer)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## API Endpoints

### Основные

| Метод  | Путь                      | Описание                           |
| ------ | ------------------------- | ---------------------------------- |
| `POST` | `/api/v1/classify`        | Отправить тексты на классификацию  |
| `GET`  | `/api/v1/tasks/{task_id}` | Получить статус и результат задачи |
| `GET`  | `/api/v1/tasks`           | Список всех задач                  |
| `GET`  | `/api/v1/models`          | Информация о модели и классах      |
| `GET`  | `/`                       | Информация об API                  |
| `GET`  | `/health`                 | Проверка работоспособности         |

### Примеры использования

```bash
# 1. Отправить задачу на классификацию
curl -X POST http://localhost:8080/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Скидка 50% на все услуги"]}'
# → {"task_id": "550e8400-...", "status": "PENDING"}

# 2. Проверить статус задачи
curl http://localhost:8080/api/v1/tasks/550e8400-...
# → {"task_id": "550e8400-...", "status": "COMPLETED", "result": {...}}

# 3. Список всех задач
curl http://localhost:8080/api/v1/tasks
# → [{"task_id": "...", "status": "COMPLETED", "created_at": "..."}]
```

### Жизненный цикл задачи

1. `POST /classify` — backend создаёт запись в БД (`PENDING`), кладёт задачу в
   RabbitMQ, возвращает `task_id`
2. Celery Worker забирает задачу → обновляет статус (`PROCESSING`) → вызывает
   classifier → записывает результат (`COMPLETED`)
3. `GET /tasks/{task_id}` — backend читает из БД и возвращает текущий статус +
   результат

Возможные статусы: `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED`

### Документация API

После запуска доступны:

- **Swagger UI**: http://localhost:8080/api/v1/docs
- **ReDoc**: http://localhost:8080/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8080/api/v1/openapi.json

## Миграции базы данных

```bash
# Применить все миграции
docker-compose exec backend alembic upgrade head

# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "описание изменений"

# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1

# Посмотреть текущую версию
docker-compose exec backend alembic current

# История миграций
docker-compose exec backend alembic history
```
