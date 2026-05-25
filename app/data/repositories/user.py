from sqlalchemy.ext.asyncio import AsyncSession

from app.data.repositories.base import Repository
from app.data.models.user import User


class UserRepository(Repository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
