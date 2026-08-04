"""BEG Einzelmaßnahmen: Gebäudehülle (5.1), Anlagentechnik (5.2),
Heizungsoptimierung (5.4a/b), Fachplanung & Baubegleitung (5.5).

Werte kommen aus `konditionen_store.DEFAULT_KONDITIONEN["beg_em"]` (1:1 aus
den Skill-Referenzen `beg-em-foerderung/references/konditionen-alt.md` und
`konditionen-neu.md` übernommen, im Settings-Tab „Konditionen" editierbar).
Heizungsförderung (5.3) ist ein eigenes Modul (`beg_heizung.py`), ebenso die
Höchstgrenzen-Deckelung über alle EM-Maßnahmen eines Gebäudes
(`hoechstgrenze_em`), die außerhalb einzelner Maßnahmen liegt.
"""

from __future__ import annotations

from .konditionen_store import DEFAULT_KONDITIONEN
from .models import EMKategorie, EMMassnahme, Gebaeude, GebaeudeTyp, Regime
from .regime import ist_ab_q1_2027

# Kategorien, auf die iSFP- bzw. WPB-Bonus grundsätzlich anwendbar sind
# (strukturell fix — keine Konditionen-Kennzahl, sondern welche Ri.-Nummern
# überhaupt bonusfähig sind).
ISFP_FAEHIGE_KATEGORIEN = {
    EMKategorie.HUELLE, EMKategorie.ANLAGENTECHNIK, EMKategorie.HEIZUNGSOPT_EFFIZIENZ,
}


class MassnahmeErgebnis:
    def __init__(self, massnahme: EMMassnahme, satz_effektiv: float, betrag: float,
                 rechenweg: list[str]):
        self.massnahme = massnahme
        self.satz_effektiv = satz_effektiv
        self.betrag = betrag
        self.rechenweg = rechenweg

    def to_dict(self) -> dict:
        return {
            "bezeichnung": self.massnahme.bezeichnung or self.massnahme.kategorie.value,
            "kategorie": self.massnahme.kategorie.value,
            "kosten": self.massnahme.kosten,
            "satz_effektiv": round(self.satz_effektiv, 4),
            "betrag": round(self.betrag, 2),
            "rechenweg": self.rechenweg,
        }


def berechne_em_massnahme(
    massnahme: EMMassnahme, regime: Regime, antragsdatum, k: dict = DEFAULT_KONDITIONEN,
) -> MassnahmeErgebnis:
    kem = k["beg_em"]
    basissatz = kem["basissatz"][massnahme.kategorie.value]
    isfp_bonus = kem["isfp_bonus"]
    wpb_bonus = kem["wpb_bonus"]
    rechenweg: list[str] = [f"Basissatz {massnahme.kategorie.value}: {basissatz:.0%}"]

    kann_isfp = massnahme.kategorie in ISFP_FAEHIGE_KATEGORIEN and massnahme.isfp_vorhanden
    kann_wpb = (
        massnahme.kategorie == EMKategorie.HUELLE
        and massnahme.ist_daemmung
        and massnahme.wpb_gebaeude
        and regime == Regime.NEU
        and ist_ab_q1_2027(antragsdatum, k)
    )

    if regime == Regime.ALT:
        if kann_isfp:
            satz = basissatz + isfp_bonus
            betrag = massnahme.kosten * satz
            rechenweg.append(
                f"iSFP-Bonus (ALT, ab 1. Maßnahme, auf Gesamtsumme): +{isfp_bonus:.0%} "
                f"→ Satz {satz:.0%}"
            )
        else:
            satz = basissatz
            betrag = massnahme.kosten * satz
        return MassnahmeErgebnis(massnahme, satz, betrag, rechenweg)

    # NEU-Regime
    mindestinvest = kem["isfp_neu_mindestinvest"]
    schwelle = kem["isfp_neu_schwelle"]

    grundbetrag = massnahme.kosten * basissatz
    betrag = grundbetrag
    isfp_betrag = 0.0
    if kann_isfp and massnahme.kosten >= mindestinvest:
        ueberschuss = max(0.0, massnahme.kosten - schwelle)
        isfp_betrag = ueberschuss * isfp_bonus
        betrag += isfp_betrag
        rechenweg.append(
            f"iSFP-Bonus (NEU, nur auf Anteil > {schwelle:,.0f} €): "
            f"+{isfp_bonus:.0%} × ({massnahme.kosten:,.0f} − {schwelle:,.0f} €) "
            f"= {isfp_betrag:,.2f} €"
        )
    elif kann_isfp:
        rechenweg.append(
            f"iSFP-Bonus entfällt: Mindestinvest {mindestinvest:,.0f} € "
            f"nicht erreicht (Kosten {massnahme.kosten:,.0f} €)"
        )

    wpb_betrag = 0.0
    if kann_wpb:
        wpb_betrag = massnahme.kosten * wpb_bonus
        betrag += wpb_betrag
        rechenweg.append(
            f"WPB-Bonus (NEU, ab Quartal 1 2027, nur Dämmung 5.1a): "
            f"+{wpb_bonus:.0%} = {wpb_betrag:,.2f} €"
        )

    satz_effektiv = betrag / massnahme.kosten if massnahme.kosten else 0.0
    return MassnahmeErgebnis(massnahme, satz_effektiv, betrag, rechenweg)


def hoechstgrenze_em(
    gebaeude: Gebaeude, regime: Regime, isfp_aktiv: bool, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    """Höchstgrenze der förderfähigen Ausgaben für Hülle+Anlagentechnik+
    Heizungsoptimierung zusammen (OHNE Fachplanung), pro Gebäude und
    Kalenderjahr. Gibt (Grenze, Erklärung) zurück."""
    kem = k["beg_em"]
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        je_m2 = kem["hoechstgrenze_nwg_je_m2"]
        grenze = flaeche * je_m2
        return grenze, f"NWG: {je_m2:,.0f} €/m² × {flaeche:,.0f} m²"

    we = gebaeude.anzahl_we
    if regime == Regime.ALT:
        # Keine WE-Staffelung im ALT-Regime: jede WE zählt voll 30.000 €
        # (60.000 € mit iSFP-Bonus).
        je_we = 60_000.0 if isfp_aktiv else 30_000.0
        grenze = je_we * we
        return grenze, f"ALT: {we} WE × {je_we:,.0f} € (keine Staffelung)"

    # NEU-Regime: gestaffelte Höchstgrenzen je WE-Stufe.
    erste_we = 60_000.0 if isfp_aktiv else 30_000.0
    stufe_2_6 = 30_000.0 if isfp_aktiv else 15_000.0
    stufe_ab_7 = 15_000.0 if isfp_aktiv else 8_000.0

    grenze = erste_we
    erklaerung = f"NEU: 1. WE {erste_we:,.0f} €"
    if we > 1:
        n_stufe2 = min(we, 6) - 1
        grenze += n_stufe2 * stufe_2_6
        erklaerung += f" + {n_stufe2} × {stufe_2_6:,.0f} € (WE 2–6)"
    if we > 6:
        n_stufe3 = we - 6
        grenze += n_stufe3 * stufe_ab_7
        erklaerung += f" + {n_stufe3} × {stufe_ab_7:,.0f} € (ab WE 7)"
    return grenze, erklaerung


def hoechstgrenze_fachplanung(
    gebaeude: Gebaeude, k: dict = DEFAULT_KONDITIONEN,
) -> tuple[float, str]:
    kem = k["beg_em"]
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        je_m2 = kem["fachplanung_hoechstgrenze_nwg_je_m2"]
        maximum = kem["fachplanung_hoechstgrenze_nwg_max"]
        grenze = min(flaeche * je_m2, maximum)
        return grenze, f"NWG: min({je_m2:,.0f} €/m² × {flaeche:,.0f} m², {maximum:,.0f} €)"
    if gebaeude.anzahl_we <= 2:
        betrag = kem["fachplanung_hoechstgrenze_efh_zfh"]
        return betrag, f"EFH/ZFH: {betrag:,.0f} € pauschal"
    je_we = kem["fachplanung_hoechstgrenze_je_we_mfh"]
    maximum = kem["fachplanung_hoechstgrenze_max"]
    grenze = min(gebaeude.anzahl_we * je_we, maximum)
    return grenze, f"MFH: min({gebaeude.anzahl_we} WE × {je_we:,.0f} €, {maximum:,.0f} €)"
