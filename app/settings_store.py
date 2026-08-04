"""Settings store: file-based persistence for runtime configuration.

Layout under DATA_DIR:
    settings.json   - runtime settings (Firmenname, Kontakt, Akzentfarbe, ...)
    logo.*          - Firmenlogo, für UI-Header und PDF-Export

First-run bootstrap: anything missing gets copied from the image defaults.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
SETTINGS_PATH = DATA_DIR / "settings.json"

_LOGO_EXTS = (".png", ".jpg", ".jpeg", ".svg", ".webp")

DEFAULT_SETTINGS: dict[str, Any] = {
    "firmenname": "",
    "kontakt_adresse": "",
    "kontakt_telefon": "",
    "kontakt_email": "",
    "akzentfarbe": "#0B6E7F",
}


def ensure_bootstrap() -> None:
    """Make sure all editable assets exist in DATA_DIR. Idempotent."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_PATH.exists():
        _write_json(SETTINGS_PATH, DEFAULT_SETTINGS)
        log.info("Bootstrapped %s", SETTINGS_PATH)


# ---------- Settings -------------------------------------------------------


def load_settings() -> dict[str, Any]:
    """Load settings.json, falling back to defaults for missing keys."""
    if not SETTINGS_PATH.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        log.exception("settings.json corrupt, returning defaults")
        return dict(DEFAULT_SETTINGS)
    merged = dict(DEFAULT_SETTINGS)
    merged.update(loaded)
    return merged


def save_settings(partial: dict[str, Any]) -> dict[str, Any]:
    """Patch settings.json with provided keys. Returns the full new state."""
    current = load_settings()
    current.update(partial)
    _write_json(SETTINGS_PATH, current)
    return current


def get_setting(key: str, default: Any = None) -> Any:
    return load_settings().get(key, default)


# ---------- Logo ------------------------------------------------------------


def logo_path() -> Path | None:
    for ext in _LOGO_EXTS:
        p = DATA_DIR / f"logo{ext}"
        if p.exists():
            return p
    return None


def save_logo(content: bytes, ext: str) -> Path:
    delete_logo()
    ext = ext.lower().lstrip(".")
    if ext not in [e.lstrip(".") for e in _LOGO_EXTS]:
        ext = "png"
    path = DATA_DIR / f"logo.{ext}"
    path.write_bytes(content)
    return path


def delete_logo() -> None:
    for ext in _LOGO_EXTS:
        p = DATA_DIR / f"logo{ext}"
        if p.exists():
            p.unlink()


def has_logo() -> bool:
    return logo_path() is not None


# ---------- Helpers ----------------------------------------------------------


def _write_json(path: Path, obj: Any) -> None:
    """Atomic write: tmp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    tmp.replace(path)
