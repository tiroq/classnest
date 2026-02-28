"""Disk-based image caching using sha256 filenames."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


async def fetch_image(url: str, cache_dir: str) -> Optional[str]:
    """Return a local filesystem path for the given image URL.

    Handles two cases:
    * A regular HTTP(S) URL — downloaded and cached by sha256 filename.
    * A filesystem path (locally uploaded via admin panel) — returned as-is
      if the file exists.

    Returns None if the image is unavailable or the URL is empty.
    """
    if not url:
        return None

    # Locally uploaded images are stored as absolute filesystem paths
    if not url.startswith(("http://", "https://")):
        local = Path(url)
        return str(local) if local.exists() else None

    digest = hashlib.sha256(url.encode()).hexdigest()
    suffix = _guess_suffix(url)
    local_path = Path(cache_dir) / f"{digest}{suffix}"

    if local_path.exists():
        return str(local_path)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
        local_path.write_bytes(response.content)
        logger.debug("Cached image %s → %s", url, local_path)
        return str(local_path)
    except Exception as exc:
        logger.warning("Failed to fetch image %s: %s", url, exc)
        return None


def _guess_suffix(url: str) -> str:
    """Return a file suffix based on the URL path, defaulting to .jpg."""
    path = url.split("?")[0].rstrip("/")
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if path.lower().endswith(ext):
            return ext
    return ".jpg"
