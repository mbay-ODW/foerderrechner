"""Testfälle direkt aus den Skill-Referenzen `beg-em-foerderung/references/
konditionen-alt.md` und `konditionen-neu.md` nachgerechnet — verhindert
stille Rechenfehler bei Boni-Kombinationen."""

from datetime import date

from app.calc.beg_em import berechne_em_massnahme, hoechstgrenze_em, isfp_bonus_neu
from app.calc.models import EMKategorie, EMMassnahme, Gebaeude, GebaeudeTyp, Regime

ANTRAGSDATUM_ALT = date(2026, 6, 1)
ANTRAGSDATUM_NEU = date(2026, 9, 1)
ANTRAGSDATUM_NEU_Q1_2027 = date(2027, 3, 1)


def test_alt_huelle_ohne_isfp():
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=10_000)
    erg = berechne_em_massnahme(m, Regime.ALT, ANTRAGSDATUM_ALT)
    assert erg.satz_effektiv == 0.15
    assert erg.betrag == 1_500


def test_alt_huelle_mit_isfp_ist_20_prozent():
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=10_000, isfp_vorhanden=True)
    erg = berechne_em_massnahme(m, Regime.ALT, ANTRAGSDATUM_ALT)
    assert erg.satz_effektiv == 0.20
    assert erg.betrag == 2_000


EFH = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)


def test_neu_isfp_rechenbeispiel_dach_50000():
    """konditionen-neu.md: 'Dach 50.000 € förderfähig, iSFP vorhanden:
    15% × 50.000 = 7.500 € + 5% × (50.000 − 30.000) = 1.000 € → 8.500 €'"""
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=50_000, isfp_vorhanden=True)
    grund = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU)
    bonus = isfp_bonus_neu(50_000, 50_000, EFH)
    assert grund.betrag == 7_500
    assert bonus["basis"] == 20_000
    assert bonus["betrag"] == 1_000


def test_neu_isfp_bonus_nur_auf_durch_isfp_zusaetzlich_foerderfaehigen_teil():
    """170.000 € bei EFH: förderfähig nur bis iSFP-Höchstgrenze 60.000 €, davon
    30.000 € über der Normal-Höchstgrenze → Bonus 5 % × 30.000 = 1.500 €
    (NICHT 5 % × (170.000 − 30.000) = 7.000 €)."""
    bonus = isfp_bonus_neu(170_000, 170_000, EFH)
    assert bonus["basis"] == 30_000
    assert bonus["betrag"] == 1_500


def test_neu_isfp_bonus_mfh_4we():
    # Normal 30k + 3×15k = 75k, mit iSFP 60k + 3×30k = 150k → Differenz 75k
    mfh = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=4)
    bonus = isfp_bonus_neu(170_000, 170_000, mfh)
    assert bonus["basis"] == 75_000
    assert bonus["betrag"] == 3_750


def test_neu_isfp_bonus_begrenzt_auf_kosten_der_isfp_massnahmen():
    # 100.000 € gesamt, aber nur 40.000 € davon iSFP-Maßnahmen: Basis max. 40.000
    bonus = isfp_bonus_neu(100_000, 40_000, EFH)
    assert bonus["basis"] == 30_000  # förderfähig 60k − 30k, kleiner als 40k
    bonus = isfp_bonus_neu(100_000, 35_000, Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=3))
    # 3 WE: normal 60k, iSFP 120k → förderfähig 100k, Differenz 40k, begrenzt auf 35k
    assert bonus["basis"] == 35_000


def test_neu_isfp_bonus_entfaellt_unter_mindestinvest():
    bonus = isfp_bonus_neu(20_000, 20_000, EFH)
    assert bonus["aktiv"] is False
    assert bonus["betrag"] == 0


def test_neu_wpb_bonus_nur_ab_q1_2027_und_nur_daemmung():
    m = EMMassnahme(
        kategorie=EMKategorie.HUELLE, kosten=10_000,
        ist_daemmung=True, wpb_gebaeude=True,
    )
    vor_q1 = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU)
    assert vor_q1.betrag == 10_000 * 0.15  # WPB-Bonus greift noch nicht

    ab_q1 = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU_Q1_2027)
    assert ab_q1.betrag == 10_000 * 0.20  # 15% + 5% WPB-Bonus


def test_heizungsoptimierung_emission_50_prozent_ohne_bonus():
    m = EMMassnahme(
        kategorie=EMKategorie.HEIZUNGSOPT_EMISSION, kosten=5_000, isfp_vorhanden=True,
    )
    erg_alt = berechne_em_massnahme(m, Regime.ALT, ANTRAGSDATUM_ALT)
    erg_neu = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU)
    assert erg_alt.betrag == 2_500
    assert erg_neu.betrag == 2_500  # kein iSFP-Bonus auf 5.4b


def test_hoechstgrenze_neu_10we_mfh_ohne_isfp():
    """konditionen-neu.md: '10-WE-MFH ohne iSFP: 30.000 + 5×15.000 + 4×8.000
    = 137.000 € (alt: 300.000 €!)'"""
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=10)
    grenze_neu, _ = hoechstgrenze_em(gebaeude, Regime.NEU, isfp_aktiv=False)
    assert grenze_neu == 137_000

    grenze_alt, _ = hoechstgrenze_em(gebaeude, Regime.ALT, isfp_aktiv=False)
    assert grenze_alt == 300_000


def test_hoechstgrenze_alt_mit_isfp_verdoppelt_je_we():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=3)
    grenze, _ = hoechstgrenze_em(gebaeude, Regime.ALT, isfp_aktiv=True)
    assert grenze == 180_000  # 3 × 60.000


def test_hoechstgrenze_neu_efh_mit_isfp():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    grenze, _ = hoechstgrenze_em(gebaeude, Regime.NEU, isfp_aktiv=True)
    assert grenze == 60_000


def test_neu_isfp_bonus_mfh_10we_schwelle_ist_volle_we_staffel():
    """10 WE: Ohne-iSFP-Höchstgrenze 30k + 5×15k + 4×8k = 137.000 €, mit iSFP
    60k + 5×30k + 4×15k = 270.000 €. Bei 170.000 € Kosten: Bonus nur auf die
    33.000 € oberhalb von 137.000 € → 1.650 € (nicht 5 % × (170.000 − 30.000))."""
    mfh10 = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=10)
    assert hoechstgrenze_em(mfh10, Regime.NEU, False)[0] == 137_000
    assert hoechstgrenze_em(mfh10, Regime.NEU, True)[0] == 270_000
    bonus = isfp_bonus_neu(170_000, 170_000, mfh10)
    assert bonus["basis"] == 33_000
    assert bonus["betrag"] == 1_650
