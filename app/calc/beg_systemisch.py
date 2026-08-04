"""BEG WG/NWG — systemische Sanierung (Effizienzhaus/-gebäude-
Komplettsanierung, Kredit mit Tilgungszuschuss / kommunaler Investitions-
zuschuss).

Werte 1:1 aus `beg-em-foerderung/references/systemisch-wg-nwg.md`. NICHT mit
BEG EM kombinierbar (eigenes Programm). Antragsstart nach den NEUEN
Bedingungen laut KfW-Kommunikation erst ca. Ende September 2026 — das steht
nicht im Richtlinientext, wird hier aber als Hinweis mitgegeben.

Für das ALT-Regime (2022er Richtlinien) sind nur die Tilgungszuschuss-Sätze
je Stufe bekannt (Vergleichstabelle im Skill); Boni/EE-Klasse-Bonus des
Altrechts sind hier NICHT nachgebildet — bei Bestandsprojekten im Zweifel
Original-KfW-Bescheid heranziehen.
"""

from __future__ import annotations

from .models import EffizienzhausStufe, Gebaeude, GebaeudeTyp, Regime, SystemischeSanierung

# NEU-Regime — Tilgungszuschuss (Kredit) je Stufe.
TILGUNGSZUSCHUSS_NEU = {
    EffizienzhausStufe.DENKMAL_EE: 0.05,
    EffizienzhausStufe.EH85_EE: 0.00,
    EffizienzhausStufe.EH70_EE: 0.00,
    EffizienzhausStufe.EH55_EE: 0.05,
    EffizienzhausStufe.EH40_EE: 0.10,
}

# NEU-Regime — kommunaler Investitionszuschuss je Stufe.
KOMMUNALER_ZUSCHUSS_NEU = {
    EffizienzhausStufe.DENKMAL_EE: 0.10,
    EffizienzhausStufe.EH85_EE: 0.10,
    EffizienzhausStufe.EH70_EE: 0.15,
    EffizienzhausStufe.EH55_EE: 0.20,
    EffizienzhausStufe.EH40_EE: 0.25,
}

# Welche Boni sind je Stufe überhaupt möglich (WPB/SerSan/NH), mit Prozentpunkten.
BONI_NEU = {
    EffizienzhausStufe.DENKMAL_EE: {"nh": 0.05},
    EffizienzhausStufe.EH85_EE: {"nh": 0.05},
    EffizienzhausStufe.EH70_EE: {"wpb": 0.10, "sersan": 0.05, "nh": 0.05},
    EffizienzhausStufe.EH55_EE: {"wpb": 0.10, "sersan": 0.15, "nh": 0.05},
    EffizienzhausStufe.EH40_EE: {"wpb": 0.10, "sersan": 0.15, "nh": 0.05},
}

# ALT-Regime (2022er Richtlinien) — nur Tilgungszuschuss-Vergleichswerte
# bekannt, keine Denkmal-Stufe im Skill dokumentiert.
TILGUNGSZUSCHUSS_ALT = {
    EffizienzhausStufe.EH40_EE: 0.20,
    EffizienzhausStufe.EH55_EE: 0.15,
    EffizienzhausStufe.EH70_EE: 0.10,
    EffizienzhausStufe.EH85_EE: 0.05,
}

HOECHSTGRENZE_WG_JE_WE = 150_000.0
HOECHSTGRENZE_NWG_JE_M2 = 2_000.0
HOECHSTGRENZE_NWG_MAX = 10_000_000.0

FACHPLANUNG_SATZ = 0.50
FACHPLANUNG_EFH_ZFH = 10_000.0
FACHPLANUNG_JE_WE_MFH = 4_000.0
FACHPLANUNG_MFH_MAX = 40_000.0
FACHPLANUNG_NWG_JE_M2 = 10.0
FACHPLANUNG_NWG_MAX = 40_000.0


def berechne_systemisch(
    sanierung: SystemischeSanierung, gebaeude: Gebaeude, regime: Regime,
) -> dict:
    rechenweg: list[str] = []
    stufe = sanierung.stufe

    if regime == Regime.ALT:
        if stufe not in TILGUNGSZUSCHUSS_ALT:
            rechenweg.append(
                f"ALT-Regime: für Stufe {stufe.value} liegt keine belastbare "
                f"Alt-Konditionen-Referenz vor — bitte KfW-Bescheid/-Merkblatt prüfen."
            )
            satz = 0.0
        else:
            satz = TILGUNGSZUSCHUSS_ALT[stufe]
            rechenweg.append(f"Tilgungszuschuss ALT (Stufe {stufe.value}): {satz:.0%}")
    else:
        if sanierung.kommunal:
            satz = KOMMUNALER_ZUSCHUSS_NEU[stufe]
            rechenweg.append(
                f"Kommunaler Investitionszuschuss NEU (Stufe {stufe.value}): {satz:.0%}"
            )
        else:
            satz = TILGUNGSZUSCHUSS_NEU[stufe]
            rechenweg.append(f"Tilgungszuschuss NEU (Stufe {stufe.value}): {satz:.0%}")

        moegliche_boni = BONI_NEU.get(stufe, {})
        for flag, key, label in (
            (sanierung.wpb_bonus, "wpb", "WPB-Bonus"),
            (sanierung.sersan_bonus, "sersan", "SerSan-Bonus (serielle Sanierung)"),
            (sanierung.nh_bonus, "nh", "NH-Bonus (Nachhaltigkeit)"),
        ):
            if flag and key in moegliche_boni:
                bonus = moegliche_boni[key]
                satz += bonus
                rechenweg.append(f"{label}: +{bonus:.0%}")
            elif flag and key not in moegliche_boni:
                rechenweg.append(f"{label}: für Stufe {stufe.value} nicht verfügbar — ignoriert")

    hoechstgrenze, hoechstgrenze_erklaerung = hoechstgrenze_systemisch(gebaeude)
    foerderfaehige_kosten = min(sanierung.kosten, hoechstgrenze)
    gedeckelt = sanierung.kosten > hoechstgrenze
    if gedeckelt:
        rechenweg.append(
            f"Kosten {sanierung.kosten:,.0f} € über Höchstgrenze "
            f"{hoechstgrenze:,.0f} € gedeckelt"
        )

    betrag = foerderfaehige_kosten * satz

    fachplanung_hoechstgrenze, fp_erklaerung = hoechstgrenze_fachplanung_systemisch(gebaeude)
    fp_foerderfaehig = min(sanierung.fachplanung_kosten, fachplanung_hoechstgrenze)
    fp_betrag = fp_foerderfaehig * FACHPLANUNG_SATZ

    return {
        "stufe": stufe.value,
        "kosten": sanierung.kosten,
        "foerderfaehige_kosten": round(foerderfaehige_kosten, 2),
        "satz_prozentual": round(satz, 4),
        "betrag": round(betrag, 2),
        "hoechstgrenze": round(hoechstgrenze, 2),
        "hoechstgrenze_erklaerung": hoechstgrenze_erklaerung,
        "gedeckelt": gedeckelt,
        "rechenweg": rechenweg,
        "fachplanung": {
            "kosten": sanierung.fachplanung_kosten,
            "foerderfaehige_kosten": round(fp_foerderfaehig, 2),
            "hoechstgrenze": round(fachplanung_hoechstgrenze, 2),
            "hoechstgrenze_erklaerung": fp_erklaerung,
            "betrag": round(fp_betrag, 2),
        },
        "zuschuss_gesamt": round(betrag + fp_betrag, 2),
    }


def hoechstgrenze_systemisch(gebaeude: Gebaeude) -> tuple[float, str]:
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        grenze = min(flaeche * HOECHSTGRENZE_NWG_JE_M2, HOECHSTGRENZE_NWG_MAX)
        return grenze, (
            f"NWG: min({HOECHSTGRENZE_NWG_JE_M2:,.0f} €/m² × {flaeche:,.0f} m², "
            f"{HOECHSTGRENZE_NWG_MAX:,.0f} €)"
        )
    grenze = gebaeude.anzahl_we * HOECHSTGRENZE_WG_JE_WE
    return grenze, f"WG: {gebaeude.anzahl_we} WE × {HOECHSTGRENZE_WG_JE_WE:,.0f} €"


def hoechstgrenze_fachplanung_systemisch(gebaeude: Gebaeude) -> tuple[float, str]:
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        grenze = min(flaeche * FACHPLANUNG_NWG_JE_M2, FACHPLANUNG_NWG_MAX)
        return grenze, (
            f"NWG: min({FACHPLANUNG_NWG_JE_M2:,.0f} €/m² × {flaeche:,.0f} m², "
            f"{FACHPLANUNG_NWG_MAX:,.0f} €)"
        )
    if gebaeude.anzahl_we <= 2:
        return FACHPLANUNG_EFH_ZFH, "EFH/ZFH: 10.000 € pauschal"
    grenze = min(gebaeude.anzahl_we * FACHPLANUNG_JE_WE_MFH, FACHPLANUNG_MFH_MAX)
    return grenze, (
        f"MFH: min({gebaeude.anzahl_we} WE × {FACHPLANUNG_JE_WE_MFH:,.0f} €, "
        f"{FACHPLANUNG_MFH_MAX:,.0f} €)"
    )
