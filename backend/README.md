# Moderation Service Backend

FastAPI backend для сервиса модерации контента с поддержкой PostgreSQL и
миграциями через Alembic.

## Описание

Backend-часть системы модерации, предоставляющая REST API для обработки и
управления контентом. Сервис выступает центральным компонентом, координирующим
работу с базой данных и взаимодействие с сервисом классификации.

## Технологии

- **Python 3.12+**
- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0** — ORM
- **Alembic** — миграции БД
- **Pydantic v2** — валидация данных
- **PostgreSQL 15** — база данных
- **uv** — менеджер пакетов

## Структура проекта

```
backend/
├── app/
│   ├── api/              # API роутеры
│   ├── database/
│   │   ├── core.py       # Подключение к БД, сессии
│   │   ├── check.py      # Проверка и создание БД
│   │   └── seed.py       # Инициализация данных
│   ├── config.py         # Настройки приложения (Pydantic Settings)
│   ├── main.py           # Точка входа FastAPI
│   ├── models.py         # SQLAlchemy модели
│   └── schemas.py        # Pydantic схемы
├── alembic/
│   ├── versions/         # Файлы миграций
│   └── env.py            # Конфигурация Alembic
├── alembic.ini
├── Dockerfile
├── pyproject.toml
└── .env                  # Переменные окружения (не в git)
```

## Установка и запуск

### Через Docker (рекомендуется)

Backend запускается в составе общего docker-compose из корня проекта:

```bash
docker-compose up -d backend
```

### Локальная разработка

```bash
# Установка зависимостей
pip install uv
uv sync --frozen

# Запуск PostgreSQL
docker-compose up -d db

# Настройка окружения
cp .env.example .env
# Изменить PG_HOST=localhost в .env

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Переменные окружения

| Переменная             | Описание                        | По умолчанию          |
| ---------------------- | ------------------------------- | --------------------- |
| `HOST`                 | Хост сервера                    | `0.0.0.0`             |
| `PORT`                 | Порт сервера                    | `8000`                |
| `ENVIRONMENT`          | Окружение (`dev`/`test`/`prod`) | `dev`                 |
| `API_V1_STR`           | Префикс API                     | `/api/v1`             |
| `PROJECT_NAME`         | Название проекта                | `Moderation Service`  |
| `PG_HOST`              | Хост PostgreSQL                 | `db`                  |
| `PG_PORT`              | Порт PostgreSQL                 | `5432`                |
| `PG_USER`              | Пользователь БД                 | `postgres`            |
| `PG_PASSWORD`          | Пароль БД                       | `postgres`            |
| `PG_DB`                | Имя базы данных                 | `moderation`          |
| `FRONTEND_HOST`        | URL фронтенда (CORS)            | `http://localhost:80` |
| `BACKEND_CORS_ORIGINS` | Дополнительные CORS origins     | `[]`                  |

## API Endpoints

| Метод | Путь      | Описание                   |
| ----- | --------- | -------------------------- |
| `GET` | `/`       | Информация об API          |
| `GET` | `/health` | Проверка работоспособности |

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

## Health Check

Эндпоинт `/health` используется Docker для проверки готовности сервиса:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```
