"""Abstract repository contract for anti-repeat tracking."""

from abc import ABC, abstractmethod

from app.domain.models import ExportedItem, HiddenItem, SeenItem


class AbstractTrackingRepository(ABC):

    @abstractmethod
    async def mark_seen(self, teacher_id: int, content_item_id: int) -> None:
        ...

    @abstractmethod
    async def mark_hidden(self, teacher_id: int, content_item_id: int) -> None:
        ...

    @abstractmethod
    async def unmark_hidden(self, teacher_id: int, content_item_id: int) -> None:
        ...

    @abstractmethod
    async def mark_exported(
        self, teacher_id: int, group_id: str, content_item_id: int
    ) -> None:
        ...

    @abstractmethod
    async def recent_seen(self, teacher_id: int, limit: int) -> list[SeenItem]:
        ...

    @abstractmethod
    async def recent_exported(
        self, teacher_id: int, group_id: str, limit: int
    ) -> list[ExportedItem]:
        ...

    @abstractmethod
    async def is_hidden(self, teacher_id: int, content_item_id: int) -> bool:
        ...

    @abstractmethod
    async def hidden_ids(self, teacher_id: int) -> set[int]:
        ...
