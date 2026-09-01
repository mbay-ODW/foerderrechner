"""FastAPI service for den BEG-EM-/gModG-Förderrechner.

Endpoints:
  POST   /api/calc              — Förderberechnung
  POST   /api/pdf/export        — PDF-Export der Berechnung

  GET    /api/konditionen       — aktuelle + Default-Konditionen (Sätze/Boni/Grenzen)
  POST   /api/konditionen       — Konditionen speichern
  POST   /api/konditionen/reset — auf Default zurücksetzen

  GET    /api/hero/status       — HERO-Integration konfiguriert?
  GET    /api/hero/projects     — HERO-Projekt-/Kundensuche

  POST   /api/beta/nebenprogramme — KfW-Beta-Programme + iSFP-Erstellungsförderung

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

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import hero_client, settings_store
from .calc import konditionen_store
from .calc.engine import berechne
from .calc.kfw_nebenprogramme import (
    altersgerecht_umbauen,
    gewerbe_zu_wohnen,
    isfp_erstellungsfoerderung,
    jung_kauft_alt,
    wohneigentumsprogramm,
)
from .calc.models import CalcInput
from .pdf_export import generate_pdf
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
konditionen_store.ensure_bootstrap()

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Förderrechner")

AUTH_REQUIRED = os.environ.get("AUTH_REQUIRED", "true").lower() == "true"
_AUTH_EXEMPT = {"/healthz"}


@app.middleware("http")
async def require_proxy_user(request: Request, call_next):
    """Second line of defence behind Authelia's forward-auth.

    Nothing here checked anything on its own -- the service depended entirely on a
    single `middlewares-authelia` entry in the Traefik labels. That matters most for
    GET /api/hero/projects: it searches HERO's customer records (name, street, postal
    code, town) using the server-side HERO token, so the caller needs no credential of
    their own. Without the proxy that is an open, tokenless search over personal data.
    Requiring the same header inside the app turns a missing middleware into a 401.

    Written as middleware rather than a router dependency so it also covers the mounted
    SPA, which a `dependencies=[...]` on FastAPI() would not reach.

    This trusts Remote-User because every router on this host runs forward-auth, so the
    proxy always overwrites whatever a client sent. Adding a route that bypasses
    Authelia would break that assumption -- the header would have to be stripped there,
    and this check taught about it.

    AUTH_REQUIRED=false is for local development without a proxy. It defaults to on, so
    a deployment that forgets the variable is closed rather than open.
    """
    if AUTH_REQUIRED and request.url.path not in _AUTH_EXEMPT:
        if not (request.headers.get("Remote-User") or request.headers.get("X-Forwarded-User")):
            return JSONResponse({"detail": "unauthenticated"}, status_code=401)
    return await call_next(request)


# ---------- Pydantic models ----------


class SettingsUpdate(BaseModel):
    firmenname: str | None = None
    kontakt_adresse: str | None = None
    kontakt_telefon: str | None = None
    kontakt_email: str | None = None
    akzentfarbe: str | None = None


# ---------- Berechnung ----------


@app.post("/api/calc")
def post_calc(req: CalcInput) -> dict[str, Any]:
    try:
        return berechne(req)
    except Exception as exc:
        log.exception("Berechnung fehlgeschlagen")
        raise HTTPException(400, f"Berechnung fehlgeschlagen: {exc}") from exc


@app.post("/api/pdf/export")
def post_pdf_export(req: CalcInput) -> Response:
    try:
        result = berechne(req)
        p = logo_path()
        logo_bytes = p.read_bytes() if p else None
        pdf_bytes = generate_pdf(result, load_settings(), logo_bytes)
    except Exception as exc:
        log.exception("PDF-Export fehlgeschlagen")
        raise HTTPException(400, f"PDF-Export fehlgeschlagen: {exc}") from exc
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="Foerderberechnung.pdf"'},
    )


# ---------- HERO-Stammdaten-Suche (read-only, optional) ----------


@app.get("/api/hero/status")
def get_hero_status() -> dict[str, Any]:
    return {"configured": hero_client.configured()}


@app.get("/api/hero/projects")
async def get_hero_projects(q: str = "") -> dict[str, Any]:
    if not hero_client.configured():
        raise HTTPException(400, "HERO ist nicht konfiguriert (HERO_TOKEN fehlt).")
    try:
        results = await hero_client.search_projects(q)
    except Exception as exc:
        log.exception("HERO-Suche fehlgeschlagen")
        raise HTTPException(502, f"HERO-Suche fehlgeschlagen: {exc}") from exc
    return {"results": results}


# ---------- Beta: KfW-Nebenprogramme + iSFP-Erstellungsförderung ----------


class BetaRequest(BaseModel):
    anzahl_kinder: int = 1
    zve_haushalt: float | None = None
    anzahl_we: int = 1
    isfp_kosten: float | None = None


@app.post("/api/beta/nebenprogramme")
def post_beta_nebenprogramme(req: BetaRequest) -> dict[str, Any]:
    k = konditionen_store.load_konditionen()
    ergebnisse = [
        jung_kauft_alt(req.anzahl_kinder, req.zve_haushalt, k),
        wohneigentumsprogramm(k),
        altersgerecht_umbauen(req.anzahl_we, k),
        gewerbe_zu_wohnen(),
    ]
    if req.isfp_kosten:
        ergebnisse.append(isfp_erstellungsfoerderung(req.isfp_kosten, req.anzahl_we, k))
    return {"programme": ergebnisse}


# ---------- Konditionen (editierbare Fördersätze/Boni/Höchstgrenzen/Stichtage) ----------


class KonditionenSave(BaseModel):
    konditionen: dict[str, Any]


@app.get("/api/konditionen")
def get_konditionen() -> dict[str, Any]:
    return {
        "current": konditionen_store.load_konditionen(),
        "default": konditionen_store.DEFAULT_KONDITIONEN,
    }


@app.post("/api/konditionen")
def post_konditionen(req: KonditionenSave) -> dict[str, Any]:
    try:
        saved = konditionen_store.save_konditionen(req.konditionen)
    except Exception as exc:
        raise HTTPException(400, f"Konditionen ungültig: {exc}") from exc
    return {"ok": True, "current": saved}


@app.post("/api/konditionen/reset")
def post_konditionen_reset() -> dict[str, Any]:
    return {"ok": True, "current": konditionen_store.reset_konditionen()}


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
