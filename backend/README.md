# Backend API

## Обзор

Минимальный FastAPI backend с базовой структурой. Авторизация и модуль users временно отключены (будут добавлены позже).

## Структура проекта

```
├── alembic/                # Миграции базы данных
│   ├── versions/           # Файлы миграций
│   ├── env.py              # Конфигурация Alembic
│   └── script.py.mako      # Шаблон миграций
├── app/
│   ├── auth/               # Авторизация (временно отключена)
│   ├── classifier/         # Модуль классификатора (в разработке)
│   ├── database/
│   │   ├── core.py         # Подключение к БД, сессии
│   │   └── seed.py         # Начальные данные
│   ├── config.py           # Настройки (из .env)
│   ├── dependencies.py     # Зависимости FastAPI
│   ├── main.py             # Точка входа приложения
│   ├── models.py           # Базовые модели SQLAlchemy
│   └── schemas.py          # Базовые Pydantic схемы
├── scripts/
│   └── prestart.sh         # Скрипт инициализации
├── tests/                  # Тесты
├── alembic.ini             # Конфиг Alembic
├── pyproject.toml          # Зависимости проекта
└── .env                    # Переменные окружения (создать вручную)
```

## Быстрый старт (локально на Mac)

### 1. Установить PostgreSQL

```bash
brew install postgresql@16
brew services start postgresql@16
```

### 2. Создать базу данных

```bash
createdb db
```

Или через GUI-клиент (DBeaver, TablePlus, Postico).

### 3. Создать файл `.env` в корне проекта

```env
PROJECT_NAME=MyProject
PG_HOST=localhost
PG_PORT=5432
PG_USER=твой_mac_username
PG_PASSWORD=
PG_DB=mydb
ENVIRONMENT=dev
```

Узнать username: `whoami`

### 4. Установить зависимости

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить зависимости через uv (быстрее)
pip install uv

uv sync
```

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Или:
```bash
python -m app.main
```

### 6. Открыть документацию

- Swagger UI: http://localhost:8080/api/v1/docs
- ReDoc: http://localhost:8080/api/v1/redoc

## Команды PostgreSQL

```bash
# Запустить
brew services start postgresql@16

# Остановить
brew services stop postgresql@16

# Перезапустить
brew services restart postgresql@16

# Статус
brew services list

# Список баз данных
psql -l

# Подключиться к базе
psql mydb
```

## Миграции (Alembic)

```bash
# Применить все миграции
alembic upgrade head

# Создать новую миграцию
alembic revision -m "описание изменений"

# Откатить последнюю миграцию
alembic downgrade -1
```

## Что отключено (TODO)

- [ ] Модуль `users` (модели, схемы, CRUD)
- [ ] Авторизация (`auth` router)
- [ ] Зависимости `get_current_user`, `get_current_active_user`
- [ ] Superuser seed

Эти модули будут добавлены позже при необходимости.

## Конфигурация

Все настройки в `app/config.py`. Переменные окружения загружаются из `.env`.

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PROJECT_NAME` | Название проекта | обязательно |
| `PG_HOST` | Хост PostgreSQL | обязательно |
| `PG_PORT` | Порт PostgreSQL | 5432 |
| `PG_USER` | Пользователь БД | обязательно |
| `PG_PASSWORD` | Пароль БД | пусто |
| `PG_DB` | Имя базы данных | обязательно |
| `ENVIRONMENT` | dev / test / prod | dev |
| `HOST` | Хост сервера | 0.0.0.0 |
| `PORT` | Порт сервера | 8080 |

## Добавление нового модуля

1. Создать папку `app/название_модуля/`
2. Добавить файлы:
   - `models.py` — SQLAlchemy модели
   - `schemas.py` — Pydantic схемы
   - `service.py` — бизнес-логика
   - `router.py` — эндпоинты
3. Подключить router в `app/main.py`
4. Создать миграцию: `alembic revision -m "Add название_модуля"`