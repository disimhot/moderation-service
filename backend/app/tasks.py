import httpx
import os
from .celery_app import celery_app
from .database.core import SessionFactory
from .models import ClassificationTask, TaskStatus

CLASSIFIER_URL = os.getenv("CLASSIFIER_URL", "http://classifier:8090")


@celery_app.task(
    bind=True,
    autoretry_for=(httpx.RequestError, httpx.TimeoutException),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def classify_texts(self, texts: list[str]):
    """Classify texts using BERT model."""
    task_id = self.request.id
    session = SessionFactory()
    task = None

    try:
        task = session.get(ClassificationTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status == TaskStatus.COMPLETED:
            return task.result

        task.status = TaskStatus.PROCESSING
        session.commit()

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{CLASSIFIER_URL}/predict",
                json={"texts": texts},
            )
            response.raise_for_status()
            result = response.json()

        task.status = TaskStatus.COMPLETED
        task.result = result
        session.commit()

        return result

    except Exception as e:
        session.rollback()
        if task:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            session.commit()
        raise

    finally:
        session.close()
