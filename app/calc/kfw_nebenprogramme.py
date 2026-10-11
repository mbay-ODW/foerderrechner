"""BETA — KfW-Nebenprogramme.

WICHTIG: Anders als `beg_em.py`/`beg_heizung.py`/`beg_systemisch.py` sind
diese Werte NICHT aus einer geladenen, stand-verifizierten Skill-Referenz
übernommen — für Jung kauft Alt, Wohneigentumsprogramm, Altersgerecht
Umbauen, Gewerbe zu Wohnen existiert keine
entsprechende Referenz in `beg-em-foerderung`/`gebaeudeenergierecht`. Die
Zahlen hier sind Best-Effort-Strukturdaten (Kreditobergrenzen, grobe Sätze,
im Settings-Tab „Konditionen" editierbar) — vor jeder Kundenberatung MUSS das
aktuelle KfW-/BAFA-Merkblatt geprüft werden. Jedes Ergebnis trägt deshalb
`verifiziert: False` und einen Prüfhinweis; die UI zeigt das als Beta-Badge.
"""

from __future__ import annotations

from .konditionen_store import DEFAULT_KONDITIONEN

PRUEFHINWEIS = (
    "Beta — Konditionen nicht durch die geladenen Skill-Referenzen "
    "abgesichert. Vor Kundenberatung aktuelles KfW-/BAFA-Merkblatt prüfen."
)


def jung_kauft_alt(
    anzahl_kinder: int, zve_haushalt: float | None, k: dict = DEFAULT_KONDITIONEN,
) -> dict:
    kn = k["kfw_nebenprogramme"]
    kinder_gedeckelt = min(max(anzahl_kinder, 1), 3)
    kredit = kn["jung_kauft_alt_kredit_je_kinderzahl"][str(kinder_gedeckelt)]
    einkommensgrenze = kn["jung_kauft_alt_einkommensgrenze_basis"] + max(
        0, anzahl_kinder - 1
    ) * kn["jung_kauft_alt_einkommensgrenze_je_weiteres_kind"]

    berechtigt = zve_haushalt is None or zve_haushalt <= einkommensgrenze
    return {
        "programm": "Jung kauft Alt (KfW 308)",
        "kredit_max": kredit,
        "einkommensgrenze": einkommensgrenze,
        "vermutlich_berechtigt": berechtigt,
        "hinweis": (
            "Zinsverbilligter Kredit für junge Familien beim Kauf + Sanierung "
            "einer Bestandsimmobilie auf mind. EH 70 EE binnen 4 Jahren."
        ),
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }


def wohneigentumsprogramm(k: dict = DEFAULT_KONDITIONEN) -> dict:
    return {
        "programm": "Wohneigentumsprogramm (KfW 124)",
        "kredit_max": k["kfw_nebenprogramme"]["wohneigentumsprogramm_kredit_max"],
        "hinweis": (
            "Zinsgünstiger Kredit für Neubau/Ersterwerb selbstgenutzten "
            "Wohneigentums, ohne besondere energetische Vorgabe."
        ),
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }


def altersgerecht_umbauen(anzahl_we: int, k: dict = DEFAULT_KONDITIONEN) -> dict:
    je_we = k["kfw_nebenprogramme"]["altersgerecht_umbauen_kredit_max_je_we"]
    return {
        "programm": "Altersgerecht Umbauen (KfW 159)",
        "kredit_max": je_we * max(anzahl_we, 1),
        "hinweis": "Kredit zur Barrierereduzierung (Bad, Zugänge, Türbreiten etc.).",
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }


def gewerbe_zu_wohnen() -> dict:
    return {
        "programm": "Gewerbe zu Wohnen",
        "kredit_max": None,
        "hinweis": (
            "Förderung der Umnutzung leerstehender Gewerbeimmobilien zu "
            "Wohnraum — Konditionen konnten hier nicht zuverlässig "
            "hinterlegt werden. Bitte direkt beim KfW-Merkblatt nachsehen."
        ),
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }

