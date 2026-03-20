"""Base repository with common CRUD operations."""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository providing standard CRUD for any ORM model.

    Subclasses set `model` to their specific SQLAlchemy model class.
    """

    model: type[T]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> T | None:
        """Fetch a single record by primary key."""
        return await self._session.get(self.model, id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Fetch all records with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Insert a new record and return it."""
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, **kwargs) -> T | None:
        """Update fields on an existing record."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete a record by primary key. Returns True if found and deleted."""
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True
