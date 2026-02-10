# Moderation Service Classifier

Сервис классификации контента для системы модерации.

## Описание

Classifier — это микросервис, отвечающий за автоматическую классификацию и
анализ контента. Работает в связке с основным backend-сервисом модерации,
обрабатывая запросы на классификацию текстов, изображений или других типов
контента.

## Архитектура

Сервис спроектирован как независимый микросервис, который:

- Получает запросы на классификацию от backend
- Применяет ML-модели или правила для категоризации контента
- Возвращает результаты классификации с уровнями уверенности

## Запуск

### Через Docker (рекомендуется)

Classifier запускается в составе общего docker-compose из корня проекта:

```bash
docker-compose up -d classifier
```

Сервис автоматически дождётся готовности backend перед запуском.

### Локальная разработка

```bash
# 1. Перейдите в директорию сервиса
cd classifier

# 2. Установка зависимостей (используя uv)
uv sync

# 3. Настройка окружения
cp .env.example .env

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
=======
# 4. Запуск классификатора
uv run main.py
>>>>>>> 10b0842 ([checkpoint-1] - cope)
```

## Конфигурация

### Переменные окружения

Настройте в файле `.env`:

| Переменная    | Описание            | По умолчанию          |
| ------------- | ------------------- | --------------------- |
| `HOST`        | Хост сервера        | `0.0.0.0`             |
| `PORT`        | Порт сервера        | `8090`                |
| `BACKEND_URL` | URL backend-сервиса | `http://backend:8080` |
| `MODEL_PATH`  | Путь к ML-модели    | —                     |
| `LOG_LEVEL`   | Уровень логирования | `INFO`                |

## API

### Эндпоинты

| Метод  | Путь          | Описание                   |
| ------ | ------------- | -------------------------- |
| `POST` | `/classify`   | Классификация контента     |
| `GET`  | `/health`     | Проверка работоспособности |
| `GET`  | `/categories` | Список доступных категорий |

### Пример запроса

```bash
curl -X POST http://localhost:8090/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Текст для классификации"}'
```

### Пример ответа

```json
{
  "category": "safe",
  "confidence": 0.95,
  "labels": [
    { "name": "safe", "score": 0.95 },
    { "name": "spam", "score": 0.03 },
    { "name": "toxic", "score": 0.02 }
  ]
}
```

## Docker

### Dockerfile

Сервис собирается из собственного Dockerfile в директории `classifier/`.

### Логирование

Настроено JSON-логирование с ротацией:

- Максимальный размер файла: 10MB
- Хранится до 5 файлов

## Интеграция с Backend

Classifier регистрируется в docker-compose с зависимостью от backend:

```yaml
classifier:
  depends_on:
    backend:
      condition: service_healthy
```

Это гарантирует, что classifier запустится только после успешной инициализации
backend.

## Мониторинг

### Health Check

```bash
curl http://localhost:8090/health
```

Ожидаемый ответ:

```json
{
  "status": "ok",
  "model_loaded": true
}
```
