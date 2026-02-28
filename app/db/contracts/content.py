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
        description: Optional[str] = None,
        source: str = "local",
        tags_json: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        difficulty: Optional[str] = None,
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
        description: Optional[str] = None,
        source: Optional[str] = None,
        tags_json: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> Optional[ContentItem]:
        ...

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        ...

    @abstractmethod
    async def get_by_ids(self, item_ids: list[int]) -> list[ContentItem]:
        """Return all items matching the given IDs (order not guaranteed)."""
        ...

    @abstractmethod
    async def count(self, category: Optional[Category] = None) -> int:
        ...
