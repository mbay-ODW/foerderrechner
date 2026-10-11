"""Editierbare Förderkonditionen: alle Sätze/Boni/Höchstgrenzen/Stichtage aus
den `calc/*.py`-Modulen an einer Stelle als JSON-fähige Struktur, persistiert
unter `DATA_DIR/konditionen.json` (analog `settings_store.py`).

`DEFAULT_KONDITIONEN` ist die Quelle der Wahrheit für die Werte aus den
Skill-Referenzen (`beg-em-foerderung/references/*.md`) — die Unit-Tests in
`tests/` prüfen explizit gegen diese Defaults (Funktionsaufrufe ohne
`k`-Parameter fallen automatisch auf `DEFAULT_KONDITIONEN` zurück), damit ein
versehentlich falsch editierter Wert im Settings-Tab nie die Testgrundlage
verfälscht.

Datumswerte sind als ISO-Strings (YYYY-MM-DD) gespeichert (JSON kennt keine
date-Objekte); die Lade-Helfer wandeln sie beim Zugriff in `datetime.date`.
"""

from __future__ import annotations

import copy
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_KONDITIONEN: dict[str, Any] = {
    "regime": {
        "stichtag_alt_neu": "2026-07-20",
        "q1_2027_stichtag": "2027-02-01",
        "degression_heizung_we1": [
            ["2026-07-21", 28000],
            ["2027-02-01", 27250],
            ["2027-08-01", 26500],
            ["2028-02-01", 25750],
            ["2028-08-01", 25000],
            ["2029-02-01", 24250],
            ["2029-08-01", 23500],
            ["2030-02-01", 22750],
            ["2030-08-01", 22000],
        ],
        "degression_kgb": [
            ["2026-07-21", 0.16],
            ["2027-02-01", 0.12],
            ["2027-08-01", 0.08],
            ["2028-02-01", 0.04],
            ["2028-08-01", 0.0],
        ],
    },
    "beg_em": {
        "basissatz": {
            "huelle": 0.15,
            "anlagentechnik": 0.15,
            "heizungsopt_eff": 0.15,
            "heizungsopt_em": 0.50,
            "fachplanung": 0.50,
        },
        "isfp_bonus": 0.05,
        "wpb_bonus": 0.05,
        "isfp_neu_mindestinvest": 30000.0,
        "fachplanung_hoechstgrenze_efh_zfh": 5000.0,
        "fachplanung_hoechstgrenze_je_we_mfh": 2000.0,
        "fachplanung_hoechstgrenze_max": 20000.0,
        "fachplanung_hoechstgrenze_nwg_je_m2": 5.0,
        "fachplanung_hoechstgrenze_nwg_max": 20000.0,
        "hoechstgrenze_nwg_je_m2": 500.0,
    },
    "beg_heizung": {
        "grundfoerderung": 0.30,
        "effizienzbonus_wp_alt": 0.05,
        "emissionsminderung_biomasse_alt": 2500.0,
        "kgb_alt": 0.20,
        "einkommensbonus_alt": 0.30,
        "einkommensbonus_alt_schwelle_zve": 40000.0,
        "max_foerdersatz_alt": 0.70,
        "wp_grundfoerderung_neu_ab_q1_2027": 0.15,
        "wp_wertschoepfungsbonus_eu": 0.15,
        "max_foerdersatz_neu_erhoeht": 0.80,
        "max_foerdersatz_neu_standard": 0.70,
        "einkommensbonus_neu_familienzuschlag": 10000.0,
        "ee_ersatz_vor_2008_faktor": 0.25,
        "hoechstbetrag_we_2_6": 15000.0,
        "hoechstbetrag_ab_we_7": 8000.0,
        "hoechstbetrag_erste_we_alt": 30000.0,
        "nwg_pauschal_bis_150qm": 30000.0,
        "nwg_satz_150_400_je_m2": 200.0,
        "nwg_satz_400_1000_je_m2": 120.0,
        "nwg_satz_ueber_1000_je_m2": 80.0,
    },
    "beg_systemisch": {
        "tilgungszuschuss_neu": {
            "denkmal_ee": 0.05, "eh85_ee": 0.00, "eh70_ee": 0.00,
            "eh55_ee": 0.05, "eh40_ee": 0.10,
        },
        "kommunaler_zuschuss_neu": {
            "denkmal_ee": 0.10, "eh85_ee": 0.10, "eh70_ee": 0.15,
            "eh55_ee": 0.20, "eh40_ee": 0.25,
        },
        "boni_neu": {
            "denkmal_ee": {"nh": 0.05},
            "eh85_ee": {"nh": 0.05},
            "eh70_ee": {"wpb": 0.10, "sersan": 0.05, "nh": 0.05},
            "eh55_ee": {"wpb": 0.10, "sersan": 0.15, "nh": 0.05},
            "eh40_ee": {"wpb": 0.10, "sersan": 0.15, "nh": 0.05},
        },
        "tilgungszuschuss_alt": {
            "eh40_ee": 0.20, "eh55_ee": 0.15, "eh70_ee": 0.10, "eh85_ee": 0.05,
        },
        "hoechstgrenze_wg_je_we": 150000.0,
        "hoechstgrenze_nwg_je_m2": 2000.0,
        "hoechstgrenze_nwg_max": 10000000.0,
        "fachplanung_satz": 0.50,
        "fachplanung_efh_zfh": 10000.0,
        "fachplanung_je_we_mfh": 4000.0,
        "fachplanung_mfh_max": 40000.0,
        "fachplanung_nwg_je_m2": 10.0,
        "fachplanung_nwg_max": 40000.0,
    },
    "steuerbonus_35c": {
        "satz_gesamt": 0.20,
        "hoechstgrenze_je_objekt": 40000.0,
        "jahresstaffelung": [[1, 0.07, 14000.0], [2, 0.07, 14000.0], [3, 0.06, 12000.0]],
    },
    "kfw_nebenprogramme": {
        "jung_kauft_alt_kredit_je_kinderzahl": {"1": 100000.0, "2": 150000.0, "3": 200000.0},
        "jung_kauft_alt_einkommensgrenze_basis": 90000.0,
        "jung_kauft_alt_einkommensgrenze_je_weiteres_kind": 10000.0,
        "wohneigentumsprogramm_kredit_max": 100000.0,
        "altersgerecht_umbauen_kredit_max_je_we": 50000.0,
    },
    "isfp_erstellung": {
        "satz": 0.50,
        "hoechstbetrag_efh_zfh": 650.0,
        "hoechstbetrag_ab_3_we": 850.0,
        "weg_erlaeuterung_satz": 0.50,
        "weg_erlaeuterung_hoechstbetrag_je_weg": 250.0,
    },
}


def _data_dir() -> Path:
    import os
    return Path(os.environ.get("DATA_DIR", "/data"))


def _path() -> Path:
    return _data_dir() / "konditionen.json"


def ensure_bootstrap() -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    if not _path().exists():
        _write(DEFAULT_KONDITIONEN)


def _merge_known(base: dict, overlay: dict) -> dict:
    """Defaults als Schema: fehlende Schlüssel kommen aus `base`, unbekannte
    (z. B. nach Umbauten verwaiste oder vertippte) Schlüssel aus `overlay`
    werden verworfen, damit der Editor nie Felder ohne Wirkung zeigt."""
    result: dict = {}
    for key, bval in base.items():
        if key in overlay:
            oval = overlay[key]
            result[key] = _merge_known(bval, oval) if isinstance(bval, dict) and isinstance(oval, dict) else oval
        else:
            result[key] = copy.deepcopy(bval)
    return result


def load_konditionen() -> dict[str, Any]:
    """Aktuelle (ggf. editierte) Konditionen, fehlende Schlüssel werden aus
    den Defaults ergänzt (Upgrade-sicher bei neuen Feldern)."""
    if not _path().exists():
        return copy.deepcopy(DEFAULT_KONDITIONEN)
    try:
        saved = json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        log.exception("konditionen.json korrupt, verwende Defaults")
        return copy.deepcopy(DEFAULT_KONDITIONEN)
    return _merge_known(DEFAULT_KONDITIONEN, saved)


def save_konditionen(data: dict[str, Any]) -> dict[str, Any]:
    merged = _merge_known(DEFAULT_KONDITIONEN, data)
    _write(merged)
    return merged


def reset_konditionen() -> dict[str, Any]:
    _write(DEFAULT_KONDITIONEN)
    return copy.deepcopy(DEFAULT_KONDITIONEN)


def _write(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def parse_date_pairs(pairs: list[list]) -> list[tuple[date, float]]:
    """['2026-07-21', 28000] -> (date(2026,7,21), 28000.0), sortiert."""
    parsed = [(date.fromisoformat(d), float(v)) for d, v in pairs]
    return sorted(parsed, key=lambda t: t[0])
