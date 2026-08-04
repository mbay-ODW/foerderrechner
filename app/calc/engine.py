"""Orchestriert die Förderberechnung über alle Programme eines Antrags.

Aktuell: BEG Einzelmaßnahmen (Hülle/Anlagentechnik/Heizungsoptimierung/
Fachplanung) inkl. Höchstgrenzen-Deckelung. Heizungsförderung, systemische
Sanierung, §35c und iSFP-Förderung werden in weiteren Schritten ergänzt.
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


def berechne(calc_input: CalcInput) -> dict:
    regime = bestimme_regime(calc_input.antragsdatum, calc_input.regime)

    isfp_aktiv = any(m.isfp_vorhanden for m in calc_input.em_massnahmen)

    em_ergebnisse = []
    fachplanung_ergebnisse = []
    for m in calc_input.em_massnahmen:
        erg = berechne_em_massnahme(m, regime, calc_input.antragsdatum)
        if m.kategorie == EMKategorie.FACHPLANUNG:
            fachplanung_ergebnisse.append(erg)
        else:
            em_ergebnisse.append(erg)

    em_summe_foerderfaehig = sum(m.massnahme.kosten for m in em_ergebnisse)
    em_summe_zuschuss_ungedeckelt = sum(m.betrag for m in em_ergebnisse)

    grenze_em, grenze_em_erklaerung = hoechstgrenze_em(
        calc_input.gebaeude, regime, isfp_aktiv
    )
    # Deckelung wirkt auf die förderfähigen AUSGABEN, nicht direkt auf den
    # Zuschuss — vereinfachend (da unterschiedliche Sätze je Maßnahme
    # gemischt sein können) kappen wir hier den Zuschuss anteilig am
    # Verhältnis gedeckelte/ungedeckelte förderfähige Ausgaben.
    gedeckelt = em_summe_foerderfaehig > grenze_em
    if gedeckelt and em_summe_foerderfaehig > 0:
        kappungsfaktor = grenze_em / em_summe_foerderfaehig
        em_summe_zuschuss = em_summe_zuschuss_ungedeckelt * kappungsfaktor
    else:
        kappungsfaktor = 1.0
        em_summe_zuschuss = em_summe_zuschuss_ungedeckelt

    grenze_fachplanung, grenze_fachplanung_erklaerung = hoechstgrenze_fachplanung(
        calc_input.gebaeude
    )
    fachplanung_summe_foerderfaehig = sum(m.massnahme.kosten for m in fachplanung_ergebnisse)
    fachplanung_summe_zuschuss_ungedeckelt = sum(m.betrag for m in fachplanung_ergebnisse)
    fachplanung_gedeckelt = fachplanung_summe_foerderfaehig > grenze_fachplanung
    if fachplanung_gedeckelt and fachplanung_summe_foerderfaehig > 0:
        fp_kappungsfaktor = grenze_fachplanung / fachplanung_summe_foerderfaehig
        fachplanung_summe_zuschuss = fachplanung_summe_zuschuss_ungedeckelt * fp_kappungsfaktor
    else:
        fp_kappungsfaktor = 1.0
        fachplanung_summe_zuschuss = fachplanung_summe_zuschuss_ungedeckelt

    heizung_ergebnisse = [
        berechne_heizung_massnahme(
            m, regime, calc_input.antragsdatum,
            zve=calc_input.antragsteller.zve,
            selbstnutzer=calc_input.antragsteller.selbstnutzer,
            familienzuschlag=calc_input.antragsteller.kind_minderjaehrig,
        )
        for m in calc_input.heizung_massnahmen
    ]
    heizung_foerderfaehig_summe = sum(e["foerderfaehige_kosten"] for e in heizung_ergebnisse)
    heizung_zuschuss_ungedeckelt = sum(e["betrag"] for e in heizung_ergebnisse)
    grenze_heizung, grenze_heizung_erklaerung = hoechstbetrag_heizung_gesamt(
        calc_input.gebaeude, regime, calc_input.antragsdatum
    )
    heizung_gedeckelt = heizung_foerderfaehig_summe > grenze_heizung
    if heizung_gedeckelt and heizung_foerderfaehig_summe > 0:
        heizung_kappungsfaktor = grenze_heizung / heizung_foerderfaehig_summe
        heizung_zuschuss = heizung_zuschuss_ungedeckelt * heizung_kappungsfaktor
    else:
        heizung_zuschuss = heizung_zuschuss_ungedeckelt

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

    return {
        "regime": regime.value,
        "warnungen": warnungen,
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
        "zuschuss_gesamt": round(
            em_summe_zuschuss + fachplanung_summe_zuschuss + heizung_zuschuss, 2
        ),
    }
