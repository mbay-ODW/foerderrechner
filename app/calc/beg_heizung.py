"""BEG-Heizungsförderung (5.3 / KfW 458).

Werte kommen aus `konditionen_store.DEFAULT_KONDITIONEN["beg_heizung"]` (1:1
aus `beg-em-foerderung/references/konditionen-alt.md` und `konditionen-neu.md`
Abschnitt „Heizungsförderung", im Settings-Tab „Konditionen" editierbar).
Fördersätze werden pro Maßnahme berechnet, die Höchstgrenze der förderfähigen
Ausgaben gilt pro Gebäude gesamt (WE-Staffel) und wird in
`hoechstbetrag_heizung_gesamt` aggregiert.
"""

from __future__ import annotations

from datetime import date

from .konditionen_store import DEFAULT_KONDITIONEN
from .models import Gebaeude, GebaeudeTyp, HeizungMassnahme, Regime, Waermequelle
from .regime import (
    heizung_hoechstbetrag_erste_we,
    ist_ab_q1_2027,
    klimageschwindigkeitsbonus_satz,
)


def einkommensbonus_satz_neu(
    zve: float | None, familienzuschlag: bool, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    if zve is None:
        return 0.0, "Kein Einkommensbonus (zvE nicht angegeben)"
    familienzuschlag_betrag = k["beg_heizung"]["einkommensbonus_neu_familienzuschlag"]
    effektives_zve = zve - familienzuschlag_betrag if familienzuschlag else zve
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
        f"{f' inkl. Familienzuschlag -{familienzuschlag_betrag:,.0f} €' if familienzuschlag else ''}"
        f"): +{satz:.0%}"
    )
    return satz, erklaerung


def berechne_heizung_massnahme(
    m: HeizungMassnahme, regime: Regime, antragsdatum: date, zve: float | None,
    selbstnutzer: bool, familienzuschlag: bool, k: dict = DEFAULT_KONDITIONEN,
) -> dict:
    kh = k["beg_heizung"]
    rechenweg: list[str] = []
    foerderfaehige_kosten = m.kosten

    kgb_voraussetzung = (
        m.ersatz_funktionstuechtige_oel_kohle_gasetagen_nachtspeicher
        or m.ersatz_gas_biomasse_ab_20_jahre
    )

    if regime == Regime.ALT:
        grundfoerderung = kh["grundfoerderung"]
        satz = grundfoerderung
        rechenweg.append(f"Grundförderung: {grundfoerderung:.0%}")

        if m.waermequelle in (Waermequelle.WP_EU, Waermequelle.WP_NICHT_EU):
            bonus = kh["effizienzbonus_wp_alt"]
            satz += bonus
            rechenweg.append(
                f"Effizienzbonus WP (ALT, Wasser/Erdreich/Abwasser oder natürl. "
                f"Kältemittel): +{bonus:.0%}"
            )

        zuschlag_pauschal = 0.0
        if m.waermequelle == Waermequelle.BIOMASSE:
            zuschlag_pauschal = kh["emissionsminderung_biomasse_alt"]
            rechenweg.append(
                f"Emissionsminderungszuschlag Biomasse (ALT, Staub ≤2,5 mg/m³): "
                f"+{zuschlag_pauschal:,.0f} € pauschal"
            )

        if selbstnutzer and kgb_voraussetzung:
            kgb = kh["kgb_alt"]
            satz += kgb
            rechenweg.append(f"Klimageschwindigkeitsbonus (ALT, Selbstnutzer): +{kgb:.0%}")

        schwelle_zve = kh["einkommensbonus_alt_schwelle_zve"]
        if selbstnutzer and zve is not None and zve <= schwelle_zve:
            bonus = kh["einkommensbonus_alt"]
            satz += bonus
            rechenweg.append(f"Einkommensbonus (ALT, zvE ≤ {schwelle_zve:,.0f} €): +{bonus:.0%}")

        max_satz = kh["max_foerdersatz_alt"]
        satz_gedeckelt = min(satz, max_satz)
        if satz_gedeckelt < satz:
            rechenweg.append(f"Deckel {max_satz:.0%} greift (ungedeckelt {satz:.0%})")
        satz = satz_gedeckelt

        betrag = foerderfaehige_kosten * satz + zuschlag_pauschal
        return {
            "bezeichnung": m.bezeichnung, "kosten": m.kosten,
            "foerderfaehige_kosten": foerderfaehige_kosten,
            "satz_prozentual": round(satz, 4), "zuschlag_pauschal": zuschlag_pauschal,
            "betrag": round(betrag, 2), "rechenweg": rechenweg, "ausgeschlossen": False,
        }

    # ---------- NEU-Regime ----------
    q1_2027 = ist_ab_q1_2027(antragsdatum, k)

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
        faktor = kh["ee_ersatz_vor_2008_faktor"]
        foerderfaehige_kosten = m.kosten * faktor
        rechenweg.append(
            f"Ersatz einer EE-Anlage vor 2008 (NEU, ab Quartal 1 2027): nur "
            f"{faktor:.0%} der Kosten förderfähig "
            f"({m.kosten:,.0f} € → {foerderfaehige_kosten:,.0f} €)"
        )

    if m.waermequelle in (Waermequelle.WP_EU, Waermequelle.WP_NICHT_EU) and q1_2027:
        satz = kh["wp_grundfoerderung_neu_ab_q1_2027"]
        rechenweg.append(f"Grundförderung Wärmepumpe (NEU, ab Quartal 1 2027): {satz:.0%}")
        if m.waermequelle == Waermequelle.WP_EU:
            bonus = kh["wp_wertschoepfungsbonus_eu"]
            satz += bonus
            rechenweg.append(
                f"EU-Wertschöpfungsbonus (Herkunft EU/assoziierte Märkte): "
                f"+{bonus:.0%} → {satz:.0%}"
            )
        else:
            rechenweg.append("Kein Wertschöpfungsbonus: Wärmepumpe nicht EU-Ursprung")
    else:
        satz = kh["grundfoerderung"]
        rechenweg.append(f"Grundförderung: {satz:.0%}")

    if selbstnutzer and kgb_voraussetzung:
        kgb = klimageschwindigkeitsbonus_satz(antragsdatum, k)
        if kgb > 0:
            satz += kgb
            rechenweg.append(
                f"Klimageschwindigkeitsbonus (NEU, Selbstnutzer, Stand {antragsdatum}): "
                f"+{kgb:.0%}"
            )

    if selbstnutzer:
        eb_satz, eb_text = einkommensbonus_satz_neu(zve, familienzuschlag, k)
        if eb_satz > 0:
            satz += eb_satz
            rechenweg.append(eb_text)

    familienzuschlag_betrag = kh["einkommensbonus_neu_familienzuschlag"]
    zve_fuer_deckel = zve
    if zve_fuer_deckel is not None and familienzuschlag:
        zve_fuer_deckel -= familienzuschlag_betrag
    max_satz = (
        kh["max_foerdersatz_neu_erhoeht"]
        if zve_fuer_deckel is not None and zve_fuer_deckel <= 40_000
        else kh["max_foerdersatz_neu_standard"]
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
    gebaeude: Gebaeude, regime: Regime, antragsdatum: date, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    """Höchstgrenze der förderfähigen Ausgaben für die Heizungsförderung,
    pro Gebäude GESAMT (nicht pro Kalenderjahr wie bei den EM)."""
    kh = k["beg_heizung"]
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        pauschal = kh["nwg_pauschal_bis_150qm"]
        s1, s2, s3 = (
            kh["nwg_satz_150_400_je_m2"], kh["nwg_satz_400_1000_je_m2"],
            kh["nwg_satz_ueber_1000_je_m2"],
        )
        if flaeche <= 150:
            grenze = pauschal
        elif flaeche <= 400:
            grenze = s1 * flaeche
        elif flaeche <= 1000:
            grenze = s1 * 400 + s2 * (flaeche - 400)
        else:
            grenze = s1 * 400 + s2 * 600 + s3 * (flaeche - 1000)
        return grenze, f"NWG-Staffel nach Nettoraumfläche ({flaeche:,.0f} m²)"

    we = gebaeude.anzahl_we
    erste_we = (
        kh["hoechstbetrag_erste_we_alt"] if regime == Regime.ALT
        else heizung_hoechstbetrag_erste_we(antragsdatum, k)
    )
    stufe_2_6, stufe_ab_7 = kh["hoechstbetrag_we_2_6"], kh["hoechstbetrag_ab_we_7"]
    grenze = erste_we
    erklaerung = f"1. WE {erste_we:,.0f} €"
    if we > 1:
        n2 = min(we, 6) - 1
        grenze += n2 * stufe_2_6
        erklaerung += f" + {n2} × {stufe_2_6:,.0f} € (WE 2–6)"
    if we > 6:
        n3 = we - 6
        grenze += n3 * stufe_ab_7
        erklaerung += f" + {n3} × {stufe_ab_7:,.0f} € (ab WE 7)"
    return grenze, erklaerung
