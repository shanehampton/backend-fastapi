from typing import TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, UnaryExpression, func

from app.data.models.base import BaseModel
from app.util.sentinel import MISSING
from app.core.config import get_config

config = get_config()
ModelType = TypeVar('ModelType', bound=BaseModel)


class Repository(Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        session: AsyncSession,
        order_by: UnaryExpression | None = None
    ):
        self.model = model
        self.session = session
        self.order_by = order_by or self.model.created_at.desc()

    async def create_record(self, record_data: dict, commit: bool = False) -> ModelType:
        """
        Create a new record in the database.
        Returns the created record
        """
        instance = self.model(**record_data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        if commit:
            await self.session.commit()
        return instance

    async def read_record(self, record_id: str) -> ModelType | None:
        """
        Retrieve a single record by its primary key.
        Returns None if no record is found.
        """
        query = select(self.model).where(self.model.id == record_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def read_records(
        self,
        offset: int = 0,
        limit: int = config.default_page_size,
        order_by: UnaryExpression | None = None
    ) -> list[ModelType]:
        """
        Retrieve all records with pagination.
        """
        order_by = order_by or self.order_by
        query = (
            select(self.model)
            .order_by(order_by)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_records(self) -> int:
        """
        Count the total number of records.
        """
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar()

    async def update_record(
        self,
        record_id: str,
        data: dict,
        commit: bool = False
    ) -> ModelType | None:
        """
        Update a record by ID with the provided fields.
        Only explicitly supplied values are updated.
        Returns the updated record, or None if not found.
        """
        # Filter out MISSING values to allow partial updates
        # MISSING sentinel distinguishes from None when None is a valid field value
        update_data = {k: v for k, v in data.items() if v is not MISSING}

        if not update_data:
            return await self.read_record(self.model, self.session, record_id)

        query = (
            update(self.model)
            .where(self.model.id == record_id)
            .values(**update_data)
            .returning(self.model)
        )
        result = await self.session.execute(query)
        await self.session.flush()
        if commit:
            await self.session.commit()
        return result.scalar_one_or_none()

    async def delete_record(self, record_id: str, commit: bool = False) -> bool:
        """
        Delete a record by ID.
        Returns True if a record was deleted, False otherwise.
        """
        query = delete(self.model).where(self.model.id == record_id)
        result = await self.session.execute(query)
        await self.session.flush()
        if commit:
            await self.session.commit()
        return result.rowcount > 0
