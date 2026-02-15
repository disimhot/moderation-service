import os
import uuid
from fastapi import APIRouter, HTTPException, Request
from . import schemas
from ..tasks import classify_texts
from ..database.core import SessionFactory
from ..models import ClassificationTask, TaskStatus

CLASSIFIER_URL = os.getenv("CLASSIFIER_URL", "http://classifier:8090")

router = APIRouter()


@router.post(
    "/classify",
    summary="Submit classification task",
    description="Отправляет тексты на классификацию (асинхронно через очередь)",
)
def submit_classification(request: schemas.PredictRequest):
    """Producer: кладёт задачу в очередь, сразу возвращает task_id."""
    task_id = str(uuid.uuid4())

    # 1. Сохраняем запись в БД со статусом PENDING
    session = SessionFactory()
    try:
        db_task = ClassificationTask(
            task_id=task_id,
            status=TaskStatus.PENDING,
            texts=request.texts,
        )
        session.add(db_task)
        session.commit()
    finally:
        session.close()

    # 2. Отправляем задачу в RabbitMQ (НЕ ждём результат)
    classify_texts.apply_async(args=[request.texts], task_id=task_id)

    # 3. Сразу возвращаем task_id клиенту
    return {"task_id": task_id, "status": "PENDING"}


@router.get(
    "/tasks/{task_id}",
    summary="Get task status",
    description="Получить статус и результат задачи по ID",
)
def get_task_status(task_id: str):
    """Backend спрашивает статус — не ждёт результата."""
    session = SessionFactory()
    try:
        task = session.get(ClassificationTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task.task_id,
            "status": task.status,
            "texts": task.texts,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    finally:
        session.close()


@router.get(
    "/tasks",
    summary="List all tasks",
    description="Получить список всех задач",
)
def list_tasks():
    session = SessionFactory()
    try:
        tasks = (
            session.query(ClassificationTask)
            .order_by(ClassificationTask.created_at.desc())
            .limit(50)
            .all()
        )

        return [
            {
                "task_id": t.task_id,
                "status": t.status,
                "created_at": t.created_at,
            }
            for t in tasks
        ]
    finally:
        session.close()


@router.get(
    "/models",
    response_model=schemas.ModelsInfoResponse,
    summary="Get model info",
    description="Get information about available model and classes",
)
async def models_info(req: Request):
    """Get information about available model and classes."""
    client = req.app.state.http_client
    try:
        response = await client.get(f"{CLASSIFIER_URL}/models")
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    return response.json()
