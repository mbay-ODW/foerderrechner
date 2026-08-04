"""BEG-Heizungsförderung (5.3 / KfW 458).

Werte 1:1 aus `beg-em-foerderung/references/konditionen-alt.md` und
`konditionen-neu.md` (Abschnitt „Heizungsförderung"). Fördersätze werden pro
Maßnahme berechnet, die Höchstgrenze der förderfähigen Ausgaben gilt pro
Gebäude gesamt (WE-Staffel) und wird in `hoechstbetrag_heizung_gesamt`
aggregiert.
"""

from __future__ import annotations

from datetime import date

from .models import Gebaeude, GebaeudeTyp, HeizungMassnahme, Regime, Waermequelle
from .regime import (
    heizung_hoechstbetrag_erste_we,
    ist_ab_q1_2027,
    klimageschwindigkeitsbonus_satz,
)

GRUNDFOERDERUNG = 0.30
EFFIZIENZBONUS_WP_ALT = 0.05  # nur ALT — Wasser/Erdreich/Abwasser-Quelle oder natürl. Kältemittel
EMISSIONSMINDERUNG_BIOMASSE_ALT = 2_500.0  # Pauschalbetrag, nur ALT
KGB_ALT = 0.20
EINKOMMENSBONUS_ALT = 0.30
EINKOMMENSBONUS_ALT_SCHWELLE_ZVE = 40_000.0
MAX_FOERDERSATZ_ALT = 0.70

# NEU: Wärmepumpen-Wertschöpfungsbonus ab Quartal 1 2027
WP_GRUNDFOERDERUNG_NEU_AB_Q1_2027 = 0.15
WP_WERTSCHOEPFUNGSBONUS_EU = 0.15  # → 30% gesamt bei EU-Ursprung
MAX_FOERDERSATZ_NEU_ERHOEHT = 0.80
MAX_FOERDERSATZ_NEU_STANDARD = 0.70
EINKOMMENSBONUS_NEU_FAMILIENZUSCHLAG = 10_000.0

# Ersatz einer EE-Anlage vor 2008 (NEU, ab Q1/2027): nur 25% der Kosten foerderfaehig
EE_ERSATZ_VOR_2008_FAKTOR = 0.25

HOECHSTBETRAG_WE_2_6 = 15_000.0
HOECHSTBETRAG_AB_WE_7 = 8_000.0
HOECHSTBETRAG_ERSTE_WE_ALT = 30_000.0


def einkommensbonus_satz_neu(zve: float | None, familienzuschlag: bool) -> tuple[float, str]:
    if zve is None:
        return 0.0, "Kein Einkommensbonus (zvE nicht angegeben)"
    effektives_zve = zve - EINKOMMENSBONUS_NEU_FAMILIENZUSCHLAG if familienzuschlag else zve
    if effektives_zve <= 30_000:
        satz = 0.40
    elif effektives_zve <= 40_000:
        satz = 0.30
    elif effektives_zve <= 50_000:
        satz = 0.10
    else:
        satz = 0.0
    erklaerung = (
        f"Einkommensbonus (NEU, zvE {effektives_zve:,.0f} €"
        f"{' inkl. Familienzuschlag -10.000 €' if familienzuschlag else ''}): +{satz:.0%}"
    )
    return satz, erklaerung


def berechne_heizung_massnahme(
    m: HeizungMassnahme, regime: Regime, antragsdatum: date, zve: float | None,
    selbstnutzer: bool, familienzuschlag: bool,
) -> dict:
    rechenweg: list[str] = []
    ausgeschlossen = False
    foerderfaehige_kosten = m.kosten

    kgb_voraussetzung = (
        m.ersatz_funktionstuechtige_oel_kohle_gasetagen_nachtspeicher
        or m.ersatz_gas_biomasse_ab_20_jahre
    )

    if regime == Regime.ALT:
        satz = GRUNDFOERDERUNG
        rechenweg.append(f"Grundförderung: {GRUNDFOERDERUNG:.0%}")

        if m.waermequelle == Waermequelle.WP_EU or m.waermequelle == Waermequelle.WP_NICHT_EU:
            satz += EFFIZIENZBONUS_WP_ALT
            rechenweg.append(
                f"Effizienzbonus WP (ALT, Wasser/Erdreich/Abwasser oder natürl. "
                f"Kältemittel): +{EFFIZIENZBONUS_WP_ALT:.0%}"
            )

        zuschlag_pauschal = 0.0
        if m.waermequelle == Waermequelle.BIOMASSE:
            zuschlag_pauschal = EMISSIONSMINDERUNG_BIOMASSE_ALT
            rechenweg.append(
                f"Emissionsminderungszuschlag Biomasse (ALT, Staub ≤2,5 mg/m³): "
                f"+{zuschlag_pauschal:,.0f} € pauschal"
            )

        if selbstnutzer and kgb_voraussetzung:
            satz += KGB_ALT
            rechenweg.append(f"Klimageschwindigkeitsbonus (ALT, Selbstnutzer): +{KGB_ALT:.0%}")

        if selbstnutzer and zve is not None and zve <= EINKOMMENSBONUS_ALT_SCHWELLE_ZVE:
            satz += EINKOMMENSBONUS_ALT
            rechenweg.append(
                f"Einkommensbonus (ALT, zvE ≤ {EINKOMMENSBONUS_ALT_SCHWELLE_ZVE:,.0f} €): "
                f"+{EINKOMMENSBONUS_ALT:.0%}"
            )

        satz_gedeckelt = min(satz, MAX_FOERDERSATZ_ALT)
        if satz_gedeckelt < satz:
            rechenweg.append(f"Deckel {MAX_FOERDERSATZ_ALT:.0%} greift (ungedeckelt {satz:.0%})")
        satz = satz_gedeckelt

        betrag = foerderfaehige_kosten * satz + zuschlag_pauschal
        return {
            "bezeichnung": m.bezeichnung, "kosten": m.kosten,
            "foerderfaehige_kosten": foerderfaehige_kosten,
            "satz_prozentual": round(satz, 4), "zuschlag_pauschal": zuschlag_pauschal,
            "betrag": round(betrag, 2), "rechenweg": rechenweg, "ausgeschlossen": False,
        }

    # ---------- NEU-Regime ----------
    q1_2027 = ist_ab_q1_2027(antragsdatum)

    if q1_2027 and m.ersatz_ee_anlage_baujahr_ab_2008:
        return {
            "bezeichnung": m.bezeichnung, "kosten": m.kosten, "foerderfaehige_kosten": 0.0,
            "satz_prozentual": 0.0, "zuschlag_pauschal": 0.0, "betrag": 0.0,
            "rechenweg": [
                "Ausgeschlossen (NEU, ab Quartal 1 2027): Gebäude hat bereits eine "
                "EE-Anlage mit Inbetriebnahme ab 01.01.2008 bzw. ist an ein Wärme-/"
                "Gebäudenetz angeschlossen."
            ],
            "ausgeschlossen": True,
        }

    if q1_2027 and m.ersatz_ee_anlage_vor_2008:
        foerderfaehige_kosten = m.kosten * EE_ERSATZ_VOR_2008_FAKTOR
        rechenweg.append(
            f"Ersatz einer EE-Anlage vor 2008 (NEU, ab Quartal 1 2027): nur "
            f"{EE_ERSATZ_VOR_2008_FAKTOR:.0%} der Kosten förderfähig "
            f"({m.kosten:,.0f} € → {foerderfaehige_kosten:,.0f} €)"
        )

    if m.waermequelle in (Waermequelle.WP_EU, Waermequelle.WP_NICHT_EU) and q1_2027:
        satz = WP_GRUNDFOERDERUNG_NEU_AB_Q1_2027
        rechenweg.append(
            f"Grundförderung Wärmepumpe (NEU, ab Quartal 1 2027): {satz:.0%}"
        )
        if m.waermequelle == Waermequelle.WP_EU:
            satz += WP_WERTSCHOEPFUNGSBONUS_EU
            rechenweg.append(
                f"EU-Wertschöpfungsbonus (Herkunft EU/assoziierte Märkte): "
                f"+{WP_WERTSCHOEPFUNGSBONUS_EU:.0%} → {satz:.0%}"
            )
        else:
            rechenweg.append("Kein Wertschöpfungsbonus: Wärmepumpe nicht EU-Ursprung")
    else:
        satz = GRUNDFOERDERUNG
        rechenweg.append(f"Grundförderung: {GRUNDFOERDERUNG:.0%}")

    if selbstnutzer and kgb_voraussetzung:
        kgb = klimageschwindigkeitsbonus_satz(antragsdatum)
        if kgb > 0:
            satz += kgb
            rechenweg.append(
                f"Klimageschwindigkeitsbonus (NEU, Selbstnutzer, Stand {antragsdatum}): "
                f"+{kgb:.0%}"
            )

    if selbstnutzer:
        eb_satz, eb_text = einkommensbonus_satz_neu(zve, familienzuschlag)
        if eb_satz > 0:
            satz += eb_satz
            rechenweg.append(eb_text)

    zve_fuer_deckel = zve
    if zve_fuer_deckel is not None and familienzuschlag:
        zve_fuer_deckel -= EINKOMMENSBONUS_NEU_FAMILIENZUSCHLAG
    max_satz = (
        MAX_FOERDERSATZ_NEU_ERHOEHT
        if zve_fuer_deckel is not None and zve_fuer_deckel <= 40_000
        else MAX_FOERDERSATZ_NEU_STANDARD
    )
    satz_gedeckelt = min(satz, max_satz)
    if satz_gedeckelt < satz:
        rechenweg.append(f"Deckel {max_satz:.0%} greift (ungedeckelt {satz:.0%})")
    satz = satz_gedeckelt

    betrag = foerderfaehige_kosten * satz
    return {
        "bezeichnung": m.bezeichnung, "kosten": m.kosten,
        "foerderfaehige_kosten": foerderfaehige_kosten,
        "satz_prozentual": round(satz, 4), "zuschlag_pauschal": 0.0,
        "betrag": round(betrag, 2), "rechenweg": rechenweg, "ausgeschlossen": False,
    }


def hoechstbetrag_heizung_gesamt(
    gebaeude: Gebaeude, regime: Regime, antragsdatum: date,
) -> tuple[float, str]:
    """Höchstgrenze der förderfähigen Ausgaben für die Heizungsförderung,
    pro Gebäude GESAMT (nicht pro Kalenderjahr wie bei den EM)."""
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        if flaeche <= 150:
            grenze = 30_000.0
        elif flaeche <= 400:
            grenze = 200.0 * flaeche
        elif flaeche <= 1000:
            grenze = 200 * 400 + 120 * (flaeche - 400)
        else:
            grenze = 200 * 400 + 120 * 600 + 80 * (flaeche - 1000)
        return grenze, f"NWG-Staffel nach Nettoraumfläche ({flaeche:,.0f} m²)"

    we = gebaeude.anzahl_we
    erste_we = (
        HOECHSTBETRAG_ERSTE_WE_ALT if regime == Regime.ALT
        else heizung_hoechstbetrag_erste_we(antragsdatum)
    )
    grenze = erste_we
    erklaerung = f"1. WE {erste_we:,.0f} €"
    if we > 1:
        n2 = min(we, 6) - 1
        grenze += n2 * HOECHSTBETRAG_WE_2_6
        erklaerung += f" + {n2} × {HOECHSTBETRAG_WE_2_6:,.0f} € (WE 2–6)"
    if we > 6:
        n3 = we - 6
        grenze += n3 * HOECHSTBETRAG_AB_WE_7
        erklaerung += f" + {n3} × {HOECHSTBETRAG_AB_WE_7:,.0f} € (ab WE 7)"
    return grenze, erklaerung
