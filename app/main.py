"""FastAPI service for den BEG-EM-/gModG-Förderrechner.

Endpoints:
  GET    /api/settings         — Branding-Settings (Firma, Kontakt, Akzentfarbe)
  POST   /api/settings         — Settings patchen
  GET    /api/settings/logo    — gespeichertes Logo ausliefern
  POST   /api/settings/logo    — Logo hochladen
  DELETE /api/settings/logo    — Logo entfernen
  GET    /api/settings/logo/info

  GET    /healthz               — Liveness-Probe
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import settings_store
from .settings_store import (
    delete_logo,
    ensure_bootstrap,
    has_logo,
    load_settings,
    logo_path,
    save_logo,
    save_settings,
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("foerderrechner")

ensure_bootstrap()

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Förderrechner")


# ---------- Pydantic models ----------


class SettingsUpdate(BaseModel):
    firmenname: str | None = None
    kontakt_adresse: str | None = None
    kontakt_telefon: str | None = None
    kontakt_email: str | None = None
    akzentfarbe: str | None = None


# ---------- Settings ----------


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return load_settings()


@app.post("/api/settings")
def post_settings(req: SettingsUpdate) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    for key in (
        "firmenname", "kontakt_adresse", "kontakt_telefon",
        "kontakt_email", "akzentfarbe",
    ):
        val = getattr(req, key)
        if val is not None:
            patch[key] = val.strip()
    save_settings(patch)
    return {"ok": True}


# ---------- Logo ----------

_LOGO_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}
_MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB


@app.get("/api/settings/logo")
def get_logo():
    p = logo_path()
    if not p:
        raise HTTPException(404, "Kein Logo hochgeladen.")
    ext = p.suffix.lstrip(".")
    return Response(
        content=p.read_bytes(),
        media_type=_LOGO_MIME.get(ext, "image/png"),
    )


@app.post("/api/settings/logo")
async def post_logo(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or ""
    ext = Path(filename).suffix.lstrip(".").lower() or "png"
    if ext not in _LOGO_MIME:
        raise HTTPException(
            400,
            f"Dateiformat nicht unterstützt: .{ext}. Erlaubt: png, jpg, svg, webp",
        )
    content = await file.read()
    if len(content) > _MAX_LOGO_BYTES:
        raise HTTPException(400, "Logo zu groß (max. 2 MB).")
    save_logo(content, ext)
    return {"ok": True, "ext": ext, "size": len(content)}


@app.delete("/api/settings/logo")
def del_logo() -> dict[str, Any]:
    if not has_logo():
        raise HTTPException(404, "Kein Logo vorhanden.")
    delete_logo()
    return {"ok": True}


@app.get("/api/settings/logo/info")
def get_logo_info() -> dict[str, Any]:
    p = logo_path()
    if not p:
        return {"has_logo": False}
    return {"has_logo": True, "filename": p.name, "size": p.stat().st_size}


# ---------- Health ----------


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


class NoCacheStaticFiles(StaticFiles):
    """Serve static assets with Cache-Control: no-cache, so a redeploy never
    leaves a stale app.js/settings.js cached."""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


# Static SPA — mounted last so /api routes take precedence
app.mount("/", NoCacheStaticFiles(directory=str(STATIC_DIR), html=True), name="static")
