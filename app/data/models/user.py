from sqlalchemy import Column, Text, Boolean

from app.data.models.base import BaseModel


class User(BaseModel):
    __tablename__ = 'user'

    email = Column(Text, index=True)
    password = Column(Text)
    is_active = Column(Boolean, default=True)
