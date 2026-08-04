"""BEG WG/NWG — systemische Sanierung (Effizienzhaus/-gebäude-
Komplettsanierung, Kredit mit Tilgungszuschuss / kommunaler Investitions-
zuschuss).

Werte kommen aus `konditionen_store.DEFAULT_KONDITIONEN["beg_systemisch"]`
(1:1 aus `beg-em-foerderung/references/systemisch-wg-nwg.md`, im
Settings-Tab „Konditionen" editierbar). NICHT mit BEG EM kombinierbar
(eigenes Programm). Antragsstart nach den NEUEN Bedingungen laut
KfW-Kommunikation erst ca. Ende September 2026 — das steht nicht im
Richtlinientext, wird hier aber als Hinweis mitgegeben.

Für das ALT-Regime (2022er Richtlinien) sind nur die Tilgungszuschuss-Sätze
je Stufe bekannt (Vergleichstabelle im Skill); Boni/EE-Klasse-Bonus des
Altrechts sind hier NICHT nachgebildet — bei Bestandsprojekten im Zweifel
Original-KfW-Bescheid heranziehen.
"""

from __future__ import annotations

from .konditionen_store import DEFAULT_KONDITIONEN
from .models import EffizienzhausStufe, Gebaeude, GebaeudeTyp, Regime, SystemischeSanierung


def berechne_systemisch(
    sanierung: SystemischeSanierung, gebaeude: Gebaeude, regime: Regime,
    k: dict = DEFAULT_KONDITIONEN,
) -> dict:
    ks = k["beg_systemisch"]
    rechenweg: list[str] = []
    stufe = sanierung.stufe

    if regime == Regime.ALT:
        alt_saetze = ks["tilgungszuschuss_alt"]
        if stufe.value not in alt_saetze:
            rechenweg.append(
                f"ALT-Regime: für Stufe {stufe.value} liegt keine belastbare "
                f"Alt-Konditionen-Referenz vor — bitte KfW-Bescheid/-Merkblatt prüfen."
            )
            satz = 0.0
        else:
            satz = alt_saetze[stufe.value]
            rechenweg.append(f"Tilgungszuschuss ALT (Stufe {stufe.value}): {satz:.0%}")
    else:
        if sanierung.kommunal:
            satz = ks["kommunaler_zuschuss_neu"][stufe.value]
            rechenweg.append(
                f"Kommunaler Investitionszuschuss NEU (Stufe {stufe.value}): {satz:.0%}"
            )
        else:
            satz = ks["tilgungszuschuss_neu"][stufe.value]
            rechenweg.append(f"Tilgungszuschuss NEU (Stufe {stufe.value}): {satz:.0%}")

        moegliche_boni = ks["boni_neu"].get(stufe.value, {})
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

    hoechstgrenze, hoechstgrenze_erklaerung = hoechstgrenze_systemisch(gebaeude, k)
    foerderfaehige_kosten = min(sanierung.kosten, hoechstgrenze)
    gedeckelt = sanierung.kosten > hoechstgrenze
    if gedeckelt:
        rechenweg.append(
            f"Kosten {sanierung.kosten:,.0f} € über Höchstgrenze "
            f"{hoechstgrenze:,.0f} € gedeckelt"
        )

    betrag = foerderfaehige_kosten * satz

    fachplanung_hoechstgrenze, fp_erklaerung = hoechstgrenze_fachplanung_systemisch(gebaeude, k)
    fp_foerderfaehig = min(sanierung.fachplanung_kosten, fachplanung_hoechstgrenze)
    fp_betrag = fp_foerderfaehig * ks["fachplanung_satz"]

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


def hoechstgrenze_systemisch(
    gebaeude: Gebaeude, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    ks = k["beg_systemisch"]
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        je_m2, maximum = ks["hoechstgrenze_nwg_je_m2"], ks["hoechstgrenze_nwg_max"]
        grenze = min(flaeche * je_m2, maximum)
        return grenze, f"NWG: min({je_m2:,.0f} €/m² × {flaeche:,.0f} m², {maximum:,.0f} €)"
    je_we = ks["hoechstgrenze_wg_je_we"]
    grenze = gebaeude.anzahl_we * je_we
    return grenze, f"WG: {gebaeude.anzahl_we} WE × {je_we:,.0f} €"


def hoechstgrenze_fachplanung_systemisch(
    gebaeude: Gebaeude, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    ks = k["beg_systemisch"]
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        je_m2, maximum = ks["fachplanung_nwg_je_m2"], ks["fachplanung_nwg_max"]
        grenze = min(flaeche * je_m2, maximum)
        return grenze, f"NWG: min({je_m2:,.0f} €/m² × {flaeche:,.0f} m², {maximum:,.0f} €)"
    if gebaeude.anzahl_we <= 2:
        betrag = ks["fachplanung_efh_zfh"]
        return betrag, f"EFH/ZFH: {betrag:,.0f} € pauschal"
    je_we, maximum = ks["fachplanung_je_we_mfh"], ks["fachplanung_mfh_max"]
    grenze = min(gebaeude.anzahl_we * je_we, maximum)
    return grenze, f"MFH: min({gebaeude.anzahl_we} WE × {je_we:,.0f} €, {maximum:,.0f} €)"
