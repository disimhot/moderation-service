import datetime
from sqlalchemy import Column, String, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClassificationTask(Base):
    __tablename__ = "classification_tasks"

    task_id = Column(String, primary_key=True)  # Celery task ID
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    texts = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
