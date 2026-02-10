# Moderation Service

Микросервисная система модерации контента с автоматической классификацией.

## Обзор

Moderation Service — это платформа для автоматической и ручной модерации
контента, состоящая из нескольких микросервисов:

- **Backend** — основной API-сервис на FastAPI для управления модерацией
- **Classifier** — сервис ML-классификации контента
- **PostgreSQL** — хранение данных

## Архитектура

```
┌─────────────────┐     ┌─────────────────┐
│     Client      │────▶│     Backend     │
└─────────────────┘     │   (port 8080)   │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
           ┌───────────┐  ┌───────────┐  ┌───────────┐
           │ Classifier│  │ PostgreSQL│  │   ...     │
           │(port 8090)│  │(port 5432)│  │           │
           └───────────┘  └───────────┘  └───────────┘
```

## Быстрый старт

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
docker-compose up -d

# Проверить статус
docker-compose ps
```

### Проверка работоспособности

```bash
# Backend
curl http://localhost:8080/health

# Classifier
curl http://localhost:8090/health
```

### Локальная разработка

```bash
# Установка pre-commit через uv (рекомендуется)
uv tool install pre-commit

# Инициализация хуков (запускать в корне репозитория)
pre-commit install
```

## Структура проекта

```
moderation-service/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API роутеры
│   │   ├── database/       # Работа с БД
│   │   ├── config.py       # Конфигурация
│   │   ├── main.py         # Точка входа
│   │   ├── models.py       # SQLAlchemy модели
│   │   └── schemas.py      # Pydantic схемы
│   ├── alembic/            # Миграции БД
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
├── classifier/              # Сервис классификации
│   ├── Dockerfile
│   └── README.md
├── docker-compose.yml       # Оркестрация сервисов
└── README.md               # Этот файл
```

## Сервисы

| Сервис     | Порт | Описание                  |
| ---------- | ---- | ------------------------- |
| backend    | 8080 | REST API для модерации    |
| classifier | 8090 | ML-классификация контента |
| db         | 5432 | PostgreSQL база данных    |

## Docker Compose

### Команды

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск конкретного сервиса
docker-compose up -d backend

# Остановка всех сервисов
docker-compose down

# Остановка с удалением данных
docker-compose down -v

# Пересборка образов
docker-compose build

# Просмотр логов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
```

### Health Checks

Все сервисы настроены с проверками работоспособности:

- **db**: `pg_isready` каждые 10 секунд
- **backend**: HTTP GET `/health` каждые 30 секунд
- **classifier**: зависит от здоровья backend

## API документация

После запуска доступна интерактивная документация:

- **Swagger UI**: http://localhost:8080/api/v1/docs
- **ReDoc**: http://localhost:8080/api/v1/redoc
- **Swagger Classifier**: http://localhost:8090/docs

## Миграции БД

```bash
# Применить все миграции
docker-compose exec backend alembic upgrade head

# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "описание"

# Откатить миграцию
docker-compose exec backend alembic downgrade -1
```
