"""Testfälle direkt aus den Skill-Referenzen `beg-em-foerderung/references/
konditionen-alt.md` und `konditionen-neu.md` nachgerechnet — verhindert
stille Rechenfehler bei Boni-Kombinationen."""

from datetime import date

from app.calc.beg_em import berechne_em_massnahme, hoechstgrenze_em
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


def test_neu_isfp_rechenbeispiel_dach_50000():
    """konditionen-neu.md: 'Dach 50.000 € förderfähig, iSFP vorhanden:
    15% × 50.000 = 7.500 € + 5% × (50.000 − 30.000) = 1.000 € → 8.500 €'"""
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=50_000, isfp_vorhanden=True)
    erg = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU)
    assert erg.betrag == 8_500


def test_neu_isfp_entfaellt_unter_mindestinvest():
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=20_000, isfp_vorhanden=True)
    erg = berechne_em_massnahme(m, Regime.NEU, ANTRAGSDATUM_NEU)
    assert erg.betrag == 20_000 * 0.15
    assert erg.satz_effektiv == 0.15


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
