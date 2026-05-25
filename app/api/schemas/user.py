from datetime import datetime
from pydantic import UUID4, SecretStr

from app.api.schemas.base import BaseSchema, Partial


class UserPostRequest(BaseSchema):
    email: str
    password: str
    is_active: bool = True


class UserPatchRequest(UserPostRequest, Partial):
    pass


class UserResponse(BaseSchema):
    id: UUID4
    email: str
    password: SecretStr
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
