"""Pure domain models — no DB imports allowed here."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Category(str, Enum):
    ACTIVITY = "activity"
    CRAFT = "craft"
    LOGIC = "logic"


class Layout(str, Enum):
    A4_2X2 = "a4_2x2"
    A4_2X3 = "a4_2x3"
    A4_1COL = "a4_1col"


class ContentItem(BaseModel):
    """A single educational content item."""

    id: int
    title: str
    category: Category
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    source: str = "local"          # "local" | "pinterest" — discriminator per SPEC
    tags_json: Optional[str] = None  # free-form JSON string
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    difficulty: Optional[str] = None  # e.g. "easy", "medium", "hard"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Pack(BaseModel):
    """An active or saved collection of content items for a teacher."""

    id: int
    teacher_id: int
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PackItem(BaseModel):
    """An ordered item inside a pack."""

    id: int
    pack_id: int
    content_item_id: int
    position: int


class TeacherSettings(BaseModel):
    """Per-teacher persistent settings."""

    teacher_id: int
    active_pack_id: Optional[int] = None
    current_group: str = "group_a"
    preferred_layout: Layout = Layout.A4_2X2


class Rules(BaseModel):
    """Configurable anti-repeat windows and thresholds."""

    seen_window: int = Field(20, description="Number of recent seen items to avoid")
    exported_window: int = Field(
        10, description="Number of recent exported items per group to avoid"
    )
    max_pack_size: int = Field(12, description="Maximum items allowed in a pack")
    default_layout: Layout = Layout.A4_2X2
    page_size: int = Field(20, description="Number of items per page in UI")
    pdf_footer_show_source: bool = Field(True, description="Show source URL in PDF footer")


class SeenItem(BaseModel):
    teacher_id: int
    content_item_id: int
    seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HiddenItem(BaseModel):
    teacher_id: int
    content_item_id: int
    hidden_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportedItem(BaseModel):
    teacher_id: int
    group_id: str
    content_item_id: int
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
