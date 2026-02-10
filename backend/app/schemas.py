from pydantic import BaseModel
from typing import TypeVar

T = TypeVar("T")


class Message(BaseModel):
    message: str
