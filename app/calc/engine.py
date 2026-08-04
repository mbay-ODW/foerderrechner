"""Orchestriert die Förderberechnung über alle Programme eines Antrags.

BEG Einzelmaßnahmen, BEG-Heizungsförderung, BEG WG/NWG systemische Sanierung
und § 35c EStG (als mitgerechnete Alternative pro Maßnahme). Jede EM-/
Heizungsmaßnahme kann per `steuerbonus_statt_zuschuss` statt als BEG-Zuschuss
über § 35c beantragt werden — deren Kosten fließen dann NICHT in die BEG-
Höchstgrenzen/-Summen, sondern in den gemeinsamen § 35c-Objekt-Deckel.
"""

from __future__ import annotations

from .beg_em import (
    berechne_em_massnahme,
    hoechstgrenze_em,
    hoechstgrenze_fachplanung,
)
from .beg_heizung import berechne_heizung_massnahme, hoechstbetrag_heizung_gesamt
from .beg_systemisch import berechne_systemisch
from .models import CalcInput, EMKategorie
from .regime import bestimme_regime
from .steuerbonus_35c import berechne_35c


def _kappe(summe_foerderfaehig: float, summe_zuschuss: float, grenze: float) -> tuple[float, bool]:
    gedeckelt = summe_foerderfaehig > grenze
    if gedeckelt and summe_foerderfaehig > 0:
        return summe_zuschuss * (grenze / summe_foerderfaehig), True
    return summe_zuschuss, False


def berechne(calc_input: CalcInput) -> dict:
    regime = bestimme_regime(calc_input.antragsdatum, calc_input.regime)
    isfp_aktiv = any(m.isfp_vorhanden for m in calc_input.em_massnahmen)

    # ---------- BEG-EM (nur Maßnahmen ohne Steuerbonus-Flag) ----------
    em_ergebnisse, fachplanung_ergebnisse = [], []
    for m in calc_input.em_massnahmen:
        erg = berechne_em_massnahme(m, regime, calc_input.antragsdatum)
        if m.steuerbonus_statt_zuschuss:
            continue
        if m.kategorie == EMKategorie.FACHPLANUNG:
            fachplanung_ergebnisse.append(erg)
        else:
            em_ergebnisse.append(erg)

    em_summe_foerderfaehig = sum(m.massnahme.kosten for m in em_ergebnisse)
    em_summe_zuschuss_ungedeckelt = sum(m.betrag for m in em_ergebnisse)
    grenze_em, grenze_em_erklaerung = hoechstgrenze_em(calc_input.gebaeude, regime, isfp_aktiv)
    em_summe_zuschuss, gedeckelt = _kappe(
        em_summe_foerderfaehig, em_summe_zuschuss_ungedeckelt, grenze_em
    )

    grenze_fachplanung, grenze_fachplanung_erklaerung = hoechstgrenze_fachplanung(
        calc_input.gebaeude
    )
    fachplanung_summe_foerderfaehig = sum(m.massnahme.kosten for m in fachplanung_ergebnisse)
    fachplanung_summe_zuschuss_ungedeckelt = sum(m.betrag for m in fachplanung_ergebnisse)
    fachplanung_summe_zuschuss, fachplanung_gedeckelt = _kappe(
        fachplanung_summe_foerderfaehig, fachplanung_summe_zuschuss_ungedeckelt,
        grenze_fachplanung,
    )

    # ---------- Heizungsförderung (nur Maßnahmen ohne Steuerbonus-Flag) ----------
    heizung_ergebnisse = [
        berechne_heizung_massnahme(
            m, regime, calc_input.antragsdatum,
            zve=calc_input.antragsteller.zve,
            selbstnutzer=calc_input.antragsteller.selbstnutzer,
            familienzuschlag=calc_input.antragsteller.kind_minderjaehrig,
        )
        for m in calc_input.heizung_massnahmen if not m.steuerbonus_statt_zuschuss
    ]
    heizung_foerderfaehig_summe = sum(e["foerderfaehige_kosten"] for e in heizung_ergebnisse)
    heizung_zuschuss_ungedeckelt = sum(e["betrag"] for e in heizung_ergebnisse)
    grenze_heizung, grenze_heizung_erklaerung = hoechstbetrag_heizung_gesamt(
        calc_input.gebaeude, regime, calc_input.antragsdatum
    )
    heizung_zuschuss, heizung_gedeckelt = _kappe(
        heizung_foerderfaehig_summe, heizung_zuschuss_ungedeckelt, grenze_heizung
    )

    # ---------- § 35c EStG (Maßnahmen MIT Steuerbonus-Flag, gemeinsamer Objekt-Deckel) ----------
    kosten_35c = sum(
        m.kosten for m in calc_input.em_massnahmen
        if m.steuerbonus_statt_zuschuss and m.kategorie != EMKategorie.FACHPLANUNG
    ) + sum(m.kosten for m in calc_input.heizung_massnahmen if m.steuerbonus_statt_zuschuss)
    steuerbonus_ergebnis = berechne_35c(kosten_35c) if kosten_35c > 0 else None

    # ---------- Systemische Sanierung (eigenes, nicht kombinierbares Programm) ----------
    systemisch_ergebnis = None
    warnungen = []
    if calc_input.systemische_sanierung is not None:
        systemisch_ergebnis = berechne_systemisch(
            calc_input.systemische_sanierung, calc_input.gebaeude, regime
        )
        if calc_input.em_massnahmen or calc_input.heizung_massnahmen:
            warnungen.append(
                "BEG WG/NWG (systemische Sanierung) ist NICHT mit BEG EM/Heizungs-"
                "förderung kombinierbar — bitte nur eines der beiden Programme "
                "beantragen. Beide Ergebnisse werden hier nur zum Vergleich "
                "nebeneinander angezeigt."
            )

    zuschuss_gesamt = em_summe_zuschuss + fachplanung_summe_zuschuss + heizung_zuschuss
    steuerbonus_betrag = steuerbonus_ergebnis["betrag_gesamt"] if steuerbonus_ergebnis else 0.0

    return {
        "regime": regime.value,
        "warnungen": warnungen,
        "kunde": calc_input.kunde.model_dump() if calc_input.kunde else None,
        "beg_systemisch": systemisch_ergebnis,
        "beg_heizung": {
            "massnahmen": heizung_ergebnisse,
            "foerderfaehige_kosten_summe": round(heizung_foerderfaehig_summe, 2),
            "zuschuss_ungedeckelt": round(heizung_zuschuss_ungedeckelt, 2),
            "hoechstgrenze": round(grenze_heizung, 2),
            "hoechstgrenze_erklaerung": grenze_heizung_erklaerung,
            "gedeckelt": heizung_gedeckelt,
            "zuschuss": round(heizung_zuschuss, 2),
        },
        "beg_em": {
            "massnahmen": [m.to_dict() for m in em_ergebnisse],
            "foerderfaehige_kosten_summe": round(em_summe_foerderfaehig, 2),
            "zuschuss_ungedeckelt": round(em_summe_zuschuss_ungedeckelt, 2),
            "hoechstgrenze": round(grenze_em, 2),
            "hoechstgrenze_erklaerung": grenze_em_erklaerung,
            "gedeckelt": gedeckelt,
            "zuschuss": round(em_summe_zuschuss, 2),
        },
        "fachplanung": {
            "massnahmen": [m.to_dict() for m in fachplanung_ergebnisse],
            "foerderfaehige_kosten_summe": round(fachplanung_summe_foerderfaehig, 2),
            "zuschuss_ungedeckelt": round(fachplanung_summe_zuschuss_ungedeckelt, 2),
            "hoechstgrenze": round(grenze_fachplanung, 2),
            "hoechstgrenze_erklaerung": grenze_fachplanung_erklaerung,
            "gedeckelt": fachplanung_gedeckelt,
            "zuschuss": round(fachplanung_summe_zuschuss, 2),
        },
        "steuerbonus_35c": steuerbonus_ergebnis,
        "zuschuss_gesamt": round(zuschuss_gesamt, 2),
        "gesamtvorteil_inkl_steuerbonus": round(zuschuss_gesamt + steuerbonus_betrag, 2),
    }
