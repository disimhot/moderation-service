from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic

T = TypeVar("T")


class Message(BaseModel):
    message: str