from typing import Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

DataT = TypeVar("DataT")

class ApiResponse(GenericModel, Generic[DataT]):
    success: bool = True
    data: DataT | None = None
    error: str | None = None
