"""BEG Einzelmaßnahmen: Gebäudehülle (5.1), Anlagentechnik (5.2),
Heizungsoptimierung (5.4a/b), Fachplanung & Baubegleitung (5.5).

Werte 1:1 aus den Skill-Referenzen `beg-em-foerderung/references/konditionen-
alt.md` und `konditionen-neu.md` übernommen. Heizungsförderung (5.3) ist ein
eigenes Modul (`beg_heizung.py`), ebenso die Höchstgrenzen-Deckelung über
alle EM-Maßnahmen eines Gebäudes (`hoechstgrenze_em`), die außerhalb einzelner
Maßnahmen liegt.
"""

from __future__ import annotations

from .models import EMKategorie, EMMassnahme, Gebaeude, GebaeudeTyp, Regime
from .regime import ist_ab_q1_2027

# Basissätze — identisch in ALT und NEU für die EM-Kategorien.
BASISSATZ = {
    EMKategorie.HUELLE: 0.15,
    EMKategorie.ANLAGENTECHNIK: 0.15,
    EMKategorie.HEIZUNGSOPT_EFFIZIENZ: 0.15,
    EMKategorie.HEIZUNGSOPT_EMISSION: 0.50,
    EMKategorie.FACHPLANUNG: 0.50,
}

# Kategorien, auf die iSFP- bzw. WPB-Bonus grundsätzlich anwendbar sind.
ISFP_FAEHIGE_KATEGORIEN = {
    EMKategorie.HUELLE, EMKategorie.ANLAGENTECHNIK, EMKategorie.HEIZUNGSOPT_EFFIZIENZ,
}

ISFP_BONUS = 0.05
WPB_BONUS = 0.05

# NEU-Regime: iSFP-Bonus nur bei Mindestinvest >= 30.000 € (1. WE), Bonus nur
# auf den 30.000 € übersteigenden Anteil. Quelle: konditionen-neu.md
# Rechenbeispiel „Dach 50.000 € förderfähig, iSFP vorhanden: 15%×50.000 +
# 5%×(50.000−30.000) = 8.500 €".
ISFP_NEU_MINDESTINVEST = 30_000.0
ISFP_NEU_SCHWELLE = 30_000.0

FACHPLANUNG_HOECHSTGRENZE_EFH_ZFH = 5_000.0
FACHPLANUNG_HOECHSTGRENZE_JE_WE_MFH = 2_000.0
FACHPLANUNG_HOECHSTGRENZE_MAX = 20_000.0
FACHPLANUNG_HOECHSTGRENZE_NWG_JE_M2 = 5.0
FACHPLANUNG_HOECHSTGRENZE_NWG_MAX = 20_000.0

# Höchstgrenzen Effizienzmaßnahmen NWG (beide Regime identisch: 500 €/m² NRF)
HOECHSTGRENZE_NWG_JE_M2 = 500.0


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
    massnahme: EMMassnahme, regime: Regime, antragsdatum,
) -> MassnahmeErgebnis:
    basissatz = BASISSATZ[massnahme.kategorie]
    rechenweg: list[str] = [f"Basissatz {massnahme.kategorie.value}: {basissatz:.0%}"]

    kann_isfp = massnahme.kategorie in ISFP_FAEHIGE_KATEGORIEN and massnahme.isfp_vorhanden
    kann_wpb = (
        massnahme.kategorie == EMKategorie.HUELLE
        and massnahme.ist_daemmung
        and massnahme.wpb_gebaeude
        and regime == Regime.NEU
        and ist_ab_q1_2027(antragsdatum)
    )

    if regime == Regime.ALT:
        if kann_isfp:
            satz = basissatz + ISFP_BONUS
            betrag = massnahme.kosten * satz
            rechenweg.append(
                f"iSFP-Bonus (ALT, ab 1. Maßnahme, auf Gesamtsumme): +{ISFP_BONUS:.0%} "
                f"→ Satz {satz:.0%}"
            )
        else:
            satz = basissatz
            betrag = massnahme.kosten * satz
        return MassnahmeErgebnis(massnahme, satz, betrag, rechenweg)

    # NEU-Regime
    grundbetrag = massnahme.kosten * basissatz
    betrag = grundbetrag
    isfp_betrag = 0.0
    if kann_isfp and massnahme.kosten >= ISFP_NEU_MINDESTINVEST:
        ueberschuss = max(0.0, massnahme.kosten - ISFP_NEU_SCHWELLE)
        isfp_betrag = ueberschuss * ISFP_BONUS
        betrag += isfp_betrag
        rechenweg.append(
            f"iSFP-Bonus (NEU, nur auf Anteil > {ISFP_NEU_SCHWELLE:,.0f} €): "
            f"+{ISFP_BONUS:.0%} × ({massnahme.kosten:,.0f} − {ISFP_NEU_SCHWELLE:,.0f} €) "
            f"= {isfp_betrag:,.2f} €"
        )
    elif kann_isfp:
        rechenweg.append(
            f"iSFP-Bonus entfällt: Mindestinvest {ISFP_NEU_MINDESTINVEST:,.0f} € "
            f"nicht erreicht (Kosten {massnahme.kosten:,.0f} €)"
        )

    wpb_betrag = 0.0
    if kann_wpb:
        wpb_betrag = massnahme.kosten * WPB_BONUS
        betrag += wpb_betrag
        rechenweg.append(
            f"WPB-Bonus (NEU, ab Quartal 1 2027, nur Dämmung 5.1a): "
            f"+{WPB_BONUS:.0%} = {wpb_betrag:,.2f} €"
        )

    satz_effektiv = betrag / massnahme.kosten if massnahme.kosten else 0.0
    return MassnahmeErgebnis(massnahme, satz_effektiv, betrag, rechenweg)


def hoechstgrenze_em(gebaeude: Gebaeude, regime: Regime, isfp_aktiv: bool) -> tuple[float, str]:
    """Höchstgrenze der förderfähigen Ausgaben für Hülle+Anlagentechnik+
    Heizungsoptimierung zusammen (OHNE Fachplanung), pro Gebäude und
    Kalenderjahr. Gibt (Grenze, Erklärung) zurück."""
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        grenze = flaeche * HOECHSTGRENZE_NWG_JE_M2
        return grenze, f"NWG: {HOECHSTGRENZE_NWG_JE_M2:,.0f} €/m² × {flaeche:,.0f} m²"

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


def hoechstgrenze_fachplanung(gebaeude: Gebaeude) -> tuple[float, str]:
    if gebaeude.typ == GebaeudeTyp.NWG:
        flaeche = gebaeude.nwg_flaeche_m2 or 0.0
        grenze = min(
            flaeche * FACHPLANUNG_HOECHSTGRENZE_NWG_JE_M2,
            FACHPLANUNG_HOECHSTGRENZE_NWG_MAX,
        )
        return grenze, (
            f"NWG: min({FACHPLANUNG_HOECHSTGRENZE_NWG_JE_M2:,.0f} €/m² × {flaeche:,.0f} m², "
            f"{FACHPLANUNG_HOECHSTGRENZE_NWG_MAX:,.0f} €)"
        )
    if gebaeude.anzahl_we <= 2:
        return FACHPLANUNG_HOECHSTGRENZE_EFH_ZFH, "EFH/ZFH: 5.000 € pauschal"
    grenze = min(
        gebaeude.anzahl_we * FACHPLANUNG_HOECHSTGRENZE_JE_WE_MFH,
        FACHPLANUNG_HOECHSTGRENZE_MAX,
    )
    return grenze, (
        f"MFH: min({gebaeude.anzahl_we} WE × {FACHPLANUNG_HOECHSTGRENZE_JE_WE_MFH:,.0f} €, "
        f"{FACHPLANUNG_HOECHSTGRENZE_MAX:,.0f} €)"
    )
