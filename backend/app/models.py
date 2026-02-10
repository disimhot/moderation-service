"""Shared models and mixins for the Dispatch application."""

from pydantic import Field, StringConstraints

from sqlalchemy.orm import declarative_base
from typing_extensions import Annotated

# pydantic type that limits the range of primary keys
PrimaryKey = Annotated[int, Field(gt=0, lt=2147483647)]
NameStr = Annotated[
    str, StringConstraints(pattern=r".*\S.*", strip_whitespace=True, min_length=3)
]
OrganizationSlug = Annotated[
    str, StringConstraints(pattern=r"^[\w]+(?:_[\w]+)*$", min_length=3)
]

Base = declarative_base()
