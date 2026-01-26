# SMS Classification API

REST API для классификации SMS-сообщений с использованием BERT модели.

## Структура проекта

```
├── app/
│   ├── __init__.py
│   ├── config.py              # Настройки приложения
│   ├── main.py                # FastAPI app
│   │
│   ├── api/                   # API слой
│   │   ├── __init__.py
│   │   ├── router.py          # Эндпоинты
│   │   ├── schemas.py         # Pydantic схемы
│   │   └── service.py         # Бизнес-логика API
│   │
│   ├── predict/               # Предсказания (для API)
│   │   ├── __init__.py
│   │   └── predictor.py       # Класс Predictor
│   │
│   ├── infer/                 # Инференс на тестовом датасете
│   │   ├── __init__.py
│   │   └── infer.py           # Оценка модели
│   │
│   ├── train/                 # Обучение модели
│   │   ├── __init__.py
│   │   └── train.py           # Тренировка
│   │
│   ├── models/                # ML модели
│   │   ├── __init__.py
│   │   ├── bert.py            # BERT классификатор
│   │   ├── loss.py            # Функции потерь
│   │   └── module.py          # PyTorch Lightning модуль
│   │
│   └── data/                  # Работа с данными
│       ├── __init__.py
│       └── dataset.py         # Загрузка и подготовка данных
│
├── data/                      # Данные
│   ├── train.csv
│   ├── val.csv
│   ├── test.csv
│   └── label_encoder.json
│
├── weights/                   # Веса модели
│   └── bert.pt
│
├── main.py                    # Точка входа
├── pyproject.toml
├── .env.example
└── README.md
```

## Быстрый старт

### 1. Установить зависимости

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 2. Подготовить данные

Положить CSV файлы в папку `data/`:
- `train.csv` — обучающая выборка
- `val.csv` — валидационная выборка
- `test.csv` — тестовая выборка

Формат CSV:
```csv
text,result
"Текст сообщения","категория"
```

### 3. Создать `.env` файл

```bash
cp .env.example .env
```

### 4. Обучить модель

```bash
python -m app.train
```

После обучения появятся:
- `weights/bert.pt` — веса модели
- `data/label_encoder.json` — маппинг классов

### 5. Оценить модель на тесте

```bash
python -m app.infer
```

### 6. Запустить API

```bash
uvicorn app.main:app --reload
```

### 7. Открыть документацию

- Swagger UI: http://localhost:8090/docs
- ReDoc: http://localhost:8090/redoc

## API Эндпоинты

### Health Check
```
GET /health
```

### Model Info
```
GET /api/v1/models
```

### Predict
```
POST /api/v1/predict
```

Request:
```json
{
  "texts": [
    "Скидка 50% на все товары!",
    "Привет, как дела?"
  ]
}
```

Response:
```json
{
  "predictions": [
    {
      "text": "Скидка 50% на все товары!",
      "label": "promo",
      "label_id": 2,
      "confidence": 0.9823,
      "probabilities": {"spam": 0.01, "ham": 0.007, "promo": 0.982}
    }
  ]
}
```

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PROJECT_NAME` | Название проекта | SMS Classification API |
| `ENVIRONMENT` | dev / test / prod | dev |
| `PORT` | Порт сервера | 8080 |
| `DATA_DIR` | Папка с данными | data |
| `MODEL_PATH` | Путь к весам | weights/bert.pt |
| `PRETRAINED_MODEL` | HuggingFace модель | ai-forever/ruModernBERT-base |
| `MAX_LENGTH` | Макс. длина токенов | 256 |
| `BATCH_SIZE` | Размер батча | 32 |
| `MAX_EPOCHS` | Макс. эпох | 10 |
| `LEARNING_RATE` | Learning rate | 2e-5 |

## Разработка

```bash
# Форматирование
ruff format .

# Линтинг
ruff check .

# Запуск с hot-reload
uvicorn app.main:app --reload --port 8090
```

## Команды

```bash
# Обучение
python -m app.train

# Инференс на тесте
python -m app.infer

# Запуск API
python main.py
```
