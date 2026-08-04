"""BETA — KfW-Nebenprogramme + iSFP-/Energieberatungs-Förderung.

WICHTIG: Anders als `beg_em.py`/`beg_heizung.py`/`beg_systemisch.py` sind
diese Werte NICHT aus einer geladenen, stand-verifizierten Skill-Referenz
übernommen — für Jung kauft Alt, Wohneigentumsprogramm, Altersgerecht
Umbauen, Gewerbe zu Wohnen und die iSFP-Erstellungsförderung existiert keine
entsprechende Referenz in `beg-em-foerderung`/`gebaeudeenergierecht`. Die
Zahlen hier sind Best-Effort-Strukturdaten (Kreditobergrenzen, grobe Sätze)
— vor jeder Kundenberatung MUSS das aktuelle KfW-/BAFA-Merkblatt geprüft
werden. Jedes Ergebnis trägt deshalb `verifiziert: False` und einen
Prüfhinweis; die UI zeigt das als Beta-Badge.
"""

from __future__ import annotations

PRUEFHINWEIS = (
    "Beta — Konditionen nicht durch die geladenen Skill-Referenzen "
    "abgesichert. Vor Kundenberatung aktuelles KfW-/BAFA-Merkblatt prüfen."
)

JUNG_KAUFT_ALT_KREDIT_JE_KINDERZAHL = {1: 100_000, 2: 150_000, 3: 200_000}
JUNG_KAUFT_ALT_EINKOMMENSGRENZE_BASIS = 90_000
JUNG_KAUFT_ALT_EINKOMMENSGRENZE_JE_WEITERES_KIND = 10_000

WOHNEIGENTUMSPROGRAMM_KREDIT_MAX = 100_000

ALTERSGERECHT_UMBAUEN_KREDIT_MAX_JE_WE = 50_000

ISFP_ZUSCHUSS_SATZ = 0.50
ISFP_HOECHSTBETRAG_EFH_ZFH = 650.0
ISFP_HOECHSTBETRAG_MFH_AB_3_WE = 1_300.0


def jung_kauft_alt(anzahl_kinder: int, zve_haushalt: float | None) -> dict:
    kinder_gedeckelt = min(max(anzahl_kinder, 1), 3)
    kredit = JUNG_KAUFT_ALT_KREDIT_JE_KINDERZAHL[kinder_gedeckelt]
    einkommensgrenze = JUNG_KAUFT_ALT_EINKOMMENSGRENZE_BASIS + max(
        0, anzahl_kinder - 1
    ) * JUNG_KAUFT_ALT_EINKOMMENSGRENZE_JE_WEITERES_KIND

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


def wohneigentumsprogramm() -> dict:
    return {
        "programm": "Wohneigentumsprogramm (KfW 124)",
        "kredit_max": WOHNEIGENTUMSPROGRAMM_KREDIT_MAX,
        "hinweis": (
            "Zinsgünstiger Kredit für Neubau/Ersterwerb selbstgenutzten "
            "Wohneigentums, ohne besondere energetische Vorgabe."
        ),
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }


def altersgerecht_umbauen(anzahl_we: int) -> dict:
    return {
        "programm": "Altersgerecht Umbauen (KfW 159)",
        "kredit_max": ALTERSGERECHT_UMBAUEN_KREDIT_MAX_JE_WE * max(anzahl_we, 1),
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


def isfp_erstellungsfoerderung(kosten: float, anzahl_we: int) -> dict:
    hoechstbetrag = (
        ISFP_HOECHSTBETRAG_MFH_AB_3_WE if anzahl_we >= 3 else ISFP_HOECHSTBETRAG_EFH_ZFH
    )
    betrag = min(kosten * ISFP_ZUSCHUSS_SATZ, hoechstbetrag)
    return {
        "programm": "iSFP-/Energieberatungs-Förderung (BAFA)",
        "kosten": kosten,
        "satz": ISFP_ZUSCHUSS_SATZ,
        "hoechstbetrag": hoechstbetrag,
        "betrag": round(betrag, 2),
        "hinweis": "Zuschuss zur Erstellung des individuellen Sanierungsfahrplans selbst.",
        "verifiziert": False,
        "pruefhinweis": PRUEFHINWEIS,
    }
