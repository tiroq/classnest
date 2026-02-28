"""Shared service dependencies for Telegram handlers."""

from __future__ import annotations

from app.db.sqlite.content_repo import SQLiteContentRepository
from app.db.sqlite.pack_repo import SQLitePackRepository
from app.db.sqlite.settings_repo import SQLiteSettingsRepository
from app.db.sqlite.tracking_repo import SQLiteTrackingRepository
from app.services.pack_service import PackService
from app.services.selector import ContentSelector
from app.services.tracking_service import TrackingService


def make_content_repo() -> SQLiteContentRepository:
    return SQLiteContentRepository()


def make_tracking_repo() -> SQLiteTrackingRepository:
    return SQLiteTrackingRepository()


def make_settings_repo() -> SQLiteSettingsRepository:
    return SQLiteSettingsRepository()


def make_pack_repo() -> SQLitePackRepository:
    return SQLitePackRepository()


def make_selector() -> ContentSelector:
    return ContentSelector(
        content_repo=make_content_repo(),
        tracking_repo=make_tracking_repo(),
        settings_repo=make_settings_repo(),
    )


def make_pack_service() -> PackService:
    return PackService(
        pack_repo=make_pack_repo(),
        content_repo=make_content_repo(),
        settings_repo=make_settings_repo(),
    )


def make_tracking_service() -> TrackingService:
    return TrackingService(tracking_repo=make_tracking_repo())
