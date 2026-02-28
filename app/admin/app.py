"""FastAPI admin panel application."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.admin.auth import BasicAuthMiddleware
from app.config.settings import get_settings
from app.db.sqlite.content_repo import SQLiteContentRepository
from app.db.sqlite.settings_repo import SQLiteSettingsRepository
from app.domain.models import Category, Rules

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_admin_app() -> FastAPI:
    """Build and configure the FastAPI admin application."""
    cfg = get_settings()
    app = FastAPI(title="ClassNest Admin", docs_url=None, redoc_url=None)
    app.add_middleware(BasicAuthMiddleware, username=cfg.admin_username, password=cfg.admin_password)

    @app.get("/admin/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/admin/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        content_repo = SQLiteContentRepository()
        settings_repo = SQLiteSettingsRepository()
        total = await content_repo.count()
        by_cat = {}
        for cat in Category:
            by_cat[cat.value] = await content_repo.count(cat)
        rules = await settings_repo.get_rules()
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "total_items": total,
                "by_category": by_cat,
                "rules_json": rules.model_dump_json(indent=2),
            },
        )

    @app.get("/admin/content", response_class=HTMLResponse)
    async def content_list(
        request: Request, page: int = 1, category: Optional[str] = None
    ):
        content_repo = SQLiteContentRepository()
        per_page = 20
        offset = (page - 1) * per_page
        cat = Category(category) if category else None
        items = await content_repo.list_all(category=cat, offset=offset, limit=per_page + 1)
        has_next = len(items) > per_page
        return templates.TemplateResponse(
            "content_list.html",
            {
                "request": request,
                "items": items[:per_page],
                "page": page,
                "has_next": has_next,
                "current_category": category or "",
            },
        )

    @app.get("/admin/content/new", response_class=HTMLResponse)
    async def content_new(request: Request):
        return templates.TemplateResponse(
            "content_form.html",
            {"request": request, "item": None, "error": None, "success": None},
        )

    @app.post("/admin/content/new")
    async def content_create(
        request: Request,
        title: str = Form(...),
        category: str = Form(...),
        image_url: str = Form(""),
        source_url: str = Form(""),
        image_file: Optional[UploadFile] = File(None),
    ):
        cfg = get_settings()
        content_repo = SQLiteContentRepository()
        error = None
        try:
            cat = Category(category)
            final_image_url = image_url or None
            if image_file and image_file.filename:
                final_image_url = await _save_upload(image_file, cfg.cache_dir)
            await content_repo.create(
                title=title,
                category=cat,
                image_url=final_image_url,
                source_url=source_url or None,
            )
            return RedirectResponse("/admin/content?success=1", status_code=303)
        except Exception as exc:
            error = str(exc)
        return templates.TemplateResponse(
            "content_form.html",
            {"request": request, "item": None, "error": error, "success": None},
        )

    @app.get("/admin/content/{item_id}/edit", response_class=HTMLResponse)
    async def content_edit(request: Request, item_id: int):
        content_repo = SQLiteContentRepository()
        item = await content_repo.get_by_id(item_id)
        return templates.TemplateResponse(
            "content_form.html",
            {"request": request, "item": item, "error": None, "success": None},
        )

    @app.post("/admin/content/{item_id}/edit")
    async def content_update(
        request: Request,
        item_id: int,
        title: str = Form(...),
        category: str = Form(...),
        image_url: str = Form(""),
        source_url: str = Form(""),
        image_file: Optional[UploadFile] = File(None),
    ):
        cfg = get_settings()
        content_repo = SQLiteContentRepository()
        error = None
        try:
            cat = Category(category)
            final_image_url = image_url or None
            if image_file and image_file.filename:
                final_image_url = await _save_upload(image_file, cfg.cache_dir)
            await content_repo.update(
                item_id=item_id,
                title=title,
                category=cat,
                image_url=final_image_url,
                source_url=source_url or None,
            )
            return RedirectResponse(f"/admin/content/{item_id}/edit?success=1", status_code=303)
        except Exception as exc:
            error = str(exc)
        item = await content_repo.get_by_id(item_id)
        return templates.TemplateResponse(
            "content_form.html",
            {"request": request, "item": item, "error": error, "success": None},
        )

    @app.post("/admin/content/{item_id}/delete")
    async def content_delete(item_id: int):
        content_repo = SQLiteContentRepository()
        await content_repo.delete(item_id)
        return RedirectResponse("/admin/content", status_code=303)

    @app.get("/admin/rules", response_class=HTMLResponse)
    async def rules_get(request: Request, success: Optional[str] = None):
        settings_repo = SQLiteSettingsRepository()
        rules = await settings_repo.get_rules()
        return templates.TemplateResponse(
            "rules.html",
            {
                "request": request,
                "rules_json": rules.model_dump_json(indent=2),
                "error": None,
                "success": "Rules saved." if success else None,
            },
        )

    @app.post("/admin/rules", response_class=HTMLResponse)
    async def rules_post(request: Request, rules_json: str = Form(...)):
        settings_repo = SQLiteSettingsRepository()
        error = None
        try:
            data = json.loads(rules_json)
            rules = Rules(**data)
            await settings_repo.save_rules(rules)
            return RedirectResponse("/admin/rules?success=1", status_code=303)
        except Exception as exc:
            error = str(exc)
        return templates.TemplateResponse(
            "rules.html",
            {
                "request": request,
                "rules_json": rules_json,
                "error": error,
                "success": None,
            },
        )

    return app


async def _save_upload(upload: UploadFile, cache_dir: str) -> str:
    """Save an uploaded image file and return its URL-like path."""
    import hashlib

    content = await upload.read()
    digest = hashlib.sha256(content).hexdigest()
    suffix = Path(upload.filename or "file.jpg").suffix or ".jpg"
    dest = Path(cache_dir) / f"{digest}{suffix}"
    dest.write_bytes(content)
    return f"/static/cache/{digest}{suffix}"
