# Moderation Service

Микросервисная система модерации контента с автоматической классификацией.

## Обзор

Moderation Service — это платформа для автоматической и ручной модерации
контента, состоящая из нескольких микросервисов:

- **Nginx** — reverse proxy, раздача статики, единая точка входа
- **Backend** — основной API-сервис на FastAPI для управления модерацией
- **Classifier** — сервис ML-классификации контента на основе BERT
- **Celery Worker** — обработка фоновых задач
- **RabbitMQ** — брокер сообщений для очередей задач
- **PostgreSQL** — хранение данных

## Архитектура

```
                        ┌──────────────────────────────────────────────┐
                        │              Docker Network                  │
                        │                                              │
┌────────┐   :80   ┌────────┐         ┌───────────┐                   │
│ Client │────────▶│  Nginx │────────▶│  Backend  │                   │
└────────┘         │        │ /api/*  │  (8080)   │                   │
                   │        │         └─────┬─────┘                   │
                   │        │               │                         │
                   │        │  /static/*    ┌┴──────────┬─────────┐   │
                   │        │──▶ файлы     │           │         │   │
                   └────────┘              ▼           ▼         ▼   │
                        │           ┌───────────┐ ┌────────┐ ┌────┐ │
                        │           │Classifier │ │RabbitMQ│ │ DB │ │
                        │           │  (8090)   │ │ (5672) │ │5432│ │
                        │           └───────────┘ └───┬────┘ └────┘ │
                        │                             │              │
                        │                        ┌────▼─────┐       │
                        │                        │  Celery   │       │
                        │                        │  Worker   │       │
                        │                        └──────────┘       │
                        └──────────────────────────────────────────────┘
```

Наружу открыт только порт 80 (nginx). Все остальные сервисы доступны только
внутри Docker-сети.

### Требования

- Docker
- Docker Compose

### Запуск

```bash
# Клонировать репозиторий
git clone
cd moderation-service

# Создать файлы окружения
cp .env.example .env
cp backend/.env.example backend/.env
cp classifier/.env.example classifier/.env

# Запустить все сервисы
docker compose up -d --build

# Проверить статус
docker compose ps
```

### Проверка работоспособности

```bash
# Через nginx (единая точка входа)
curl http://localhost/health

# Статика
curl http://localhost/static/css/style.css

# API
curl http://localhost/api/v1/models

# Классификация
curl -X POST http://localhost/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Скидка 50% на все услуги"]}'
```

### Локальная разработка

```bash
# Установка pre-commit через uv
uv tool install pre-commit

# Инициализация хуков
pre-commit install
```

## Структура проекта

```
moderation-service/
├── docker-compose.yaml
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html
│   ├── 50x.html
│   └── static/
│       └── css/
│           └── style.css
├── backend/
│   ├── Dockerfile
│   ├── app/
│   ├── alembic/
│   └── pyproject.toml
└── classifier/
    ├── Dockerfile
    ├── app/
    ├── weights/
    └── pyproject.toml
```

## Сервисы

| Сервис        | Порт внутренний | Порт наружу  | Описание                    |
| ------------- | --------------- | ------------ | --------------------------- |
| nginx         | 80              | 80           | Reverse proxy, статика      |
| backend       | 8080            | —            | REST API для модерации      |
| classifier    | 8090            | —            | BERT-классификация контента |
| celery_worker | —               | —            | Фоновая обработка задач     |
| db            | 5432            | —            | PostgreSQL                  |
| rabbitmq      | 5672 / 15672    | 5672 / 15672 | Брокер сообщений + панель   |

## Docker Compose

### Команды

```bash
# Запуск всех сервисов
docker compose up -d --build

# Запуск конкретного сервиса
docker compose up -d backend

# Остановка всех сервисов
docker compose down

# Остановка с удалением данных
docker compose down -v

# Пересборка образов
docker compose build --no-cache

# Просмотр логов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f classifier
docker compose logs -f nginx
```

## Nginx

Nginx выполняет три задачи:

- **Раздача статики** — файлы из `/static/` отдаются напрямую без проксирования
- **Reverse proxy** — запросы `/api/*` и `/health` проксируются на backend
- **Лендинг** — `http://localhost/` отдаёт страницу с описанием API

Конфигурация находится в `nginx/nginx.conf`.

## API документация

После запуска доступна интерактивная документация:

- **Лендинг**: http://localhost
- **Swagger UI**: http://localhost/api/v1/docs
- **ReDoc**: http://localhost/api/v1/redoc

## Миграции БД

```bash
# Применить все миграции
docker compose exec backend uv run alembic upgrade head

# Создать новую миграцию
docker compose exec backend uv run alembic revision --autogenerate -m "описание"

# Откатить миграцию
docker compose exec backend uv run alembic downgrade -1
```
