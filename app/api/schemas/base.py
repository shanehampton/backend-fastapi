from pydantic import BaseModel
from typing import Any, TypeVar, Generic

from app.util.sentinel import Sentinel, MISSING


class BaseSchema(BaseModel):
    pass


SchemaType = TypeVar('SchemaType', bound=BaseSchema)


class Partial(BaseSchema):
    """Schema for partial definitions, i.e. PATCH requests"""
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        for field in cls.model_fields.values():
            # Extend the field to be optional and support a MISSING sentinel
            # MISSING allows us to differentiate an unsupplied value from an explicit None
            field.annotation = field.annotation | Sentinel
            field.default = MISSING
        # Rebuild the model to apply changes
        cls.model_rebuild(force=True)


class PaginatedResponse(BaseSchema, Generic[SchemaType]):
    """Generic paginated response"""
    content: list[SchemaType]
    content_size: int
    total_records: int
    page_number: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
