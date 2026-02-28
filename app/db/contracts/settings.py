"""Abstract repository contract for teacher settings and rules."""

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models import Rules, TeacherSettings


class AbstractSettingsRepository(ABC):

    @abstractmethod
    async def get_teacher_settings(self, teacher_id: int) -> TeacherSettings:
        ...

    @abstractmethod
    async def save_teacher_settings(self, settings: TeacherSettings) -> None:
        ...

    @abstractmethod
    async def get_rules(self) -> Rules:
        ...

    @abstractmethod
    async def save_rules(self, rules: Rules) -> None:
        ...
