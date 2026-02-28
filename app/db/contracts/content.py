"""Abstract repository contract for content items."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Category, ContentItem


class AbstractContentRepository(ABC):
    """Contract for all content item storage backends."""

    @abstractmethod
    async def get_by_id(self, item_id: int) -> Optional[ContentItem]:
        ...

    @abstractmethod
    async def list_all(
        self,
        category: Optional[Category] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ContentItem]:
        ...

    @abstractmethod
    async def create(
        self,
        title: str,
        category: Category,
        image_url: Optional[str],
        source_url: Optional[str],
    ) -> ContentItem:
        ...

    @abstractmethod
    async def update(
        self,
        item_id: int,
        title: Optional[str] = None,
        category: Optional[Category] = None,
        image_url: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Optional[ContentItem]:
        ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        ...

    @abstractmethod
    async def count(self, category: Optional[Category] = None) -> int:
        ...
