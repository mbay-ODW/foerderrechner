from datetime import date

from app.calc.beg_heizung import (
    berechne_heizung_massnahme,
    hoechstbetrag_heizung_gesamt,
)
from app.calc.models import Gebaeude, GebaeudeTyp, HeizungMassnahme, Regime, Waermequelle

ANTRAGSDATUM_ALT = date(2026, 6, 1)
ANTRAGSDATUM_NEU_VOR_Q1_2027 = date(2026, 9, 1)
ANTRAGSDATUM_NEU_AB_Q1_2027 = date(2027, 3, 1)


def test_alt_wp_alle_boni_wird_auf_70_prozent_gedeckelt():
    m = HeizungMassnahme(
        kosten=30_000, waermequelle=Waermequelle.WP_EU,
        ersatz_gas_biomasse_ab_20_jahre=True,
    )
    erg = berechne_heizung_massnahme(
        m, Regime.ALT, ANTRAGSDATUM_ALT, zve=30_000, selbstnutzer=True,
        familienzuschlag=False,
    )
    # 30% Grund + 5% Effizienzbonus WP + 20% KGB + 30% Einkommensbonus = 85% -> Deckel 70%
    assert erg["satz_prozentual"] == 0.70
    assert erg["betrag"] == 21_000


def test_alt_biomasse_pauschalzuschlag_addiert_sich_zum_prozentualen_betrag():
    m = HeizungMassnahme(kosten=10_000, waermequelle=Waermequelle.BIOMASSE)
    erg = berechne_heizung_massnahme(
        m, Regime.ALT, ANTRAGSDATUM_ALT, zve=None, selbstnutzer=True,
        familienzuschlag=False,
    )
    assert erg["satz_prozentual"] == 0.30
    assert erg["zuschlag_pauschal"] == 2_500
    assert erg["betrag"] == 10_000 * 0.30 + 2_500


def test_neu_vor_q1_2027_kgb_16_prozent_plus_einkommensbonus_gedeckelt_auf_80():
    m = HeizungMassnahme(
        kosten=28_000, waermequelle=Waermequelle.SONSTIGE_EE,
        ersatz_funktionstuechtige_oel_kohle_gasetagen_nachtspeicher=True,
    )
    erg = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_VOR_Q1_2027, zve=25_000, selbstnutzer=True,
        familienzuschlag=False,
    )
    # 30% + 16% KGB + 40% Einkommensbonus (zve<=30k) = 86% -> Deckel 80% (zve<=40k)
    assert erg["satz_prozentual"] == 0.80


def test_neu_einkommensbonus_staffel():
    m = HeizungMassnahme(kosten=10_000)
    for zve, erwarteter_zusatz in [(25_000, 0.40), (35_000, 0.30), (45_000, 0.10), (60_000, 0.0)]:
        erg = berechne_heizung_massnahme(
            m, Regime.NEU, ANTRAGSDATUM_NEU_VOR_Q1_2027, zve=zve, selbstnutzer=True,
            familienzuschlag=False,
        )
        # Grundförderung 30% + Einkommensbonus, kein KGB da keine KGB-Voraussetzung
        erwartet = min(0.30 + erwarteter_zusatz, 0.80 if zve <= 40_000 else 0.70)
        assert erg["satz_prozentual"] == round(erwartet, 4), zve


def test_neu_wp_ab_q1_2027_eu_ursprung_30_prozent():
    m = HeizungMassnahme(kosten=20_000, waermequelle=Waermequelle.WP_EU)
    erg = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_AB_Q1_2027, zve=None, selbstnutzer=False,
        familienzuschlag=False,
    )
    assert erg["satz_prozentual"] == 0.30  # 15% Grund + 15% EU-Wertschöpfungsbonus


def test_neu_wp_ab_q1_2027_nicht_eu_nur_15_prozent():
    m = HeizungMassnahme(kosten=20_000, waermequelle=Waermequelle.WP_NICHT_EU)
    erg = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_AB_Q1_2027, zve=None, selbstnutzer=False,
        familienzuschlag=False,
    )
    assert erg["satz_prozentual"] == 0.15


def test_neu_ausschluss_ee_anlage_ab_2008_ab_q1_2027():
    m = HeizungMassnahme(kosten=20_000, ersatz_ee_anlage_baujahr_ab_2008=True)
    erg = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_AB_Q1_2027, zve=None, selbstnutzer=False,
        familienzuschlag=False,
    )
    assert erg["ausgeschlossen"] is True
    assert erg["betrag"] == 0.0

    # Vor Quartal 1 2027 greift der Ausschluss noch nicht
    erg_vorher = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_VOR_Q1_2027, zve=None, selbstnutzer=False,
        familienzuschlag=False,
    )
    assert erg_vorher["ausgeschlossen"] is False


def test_neu_ee_ersatz_vor_2008_nur_25_prozent_foerderfaehig():
    m = HeizungMassnahme(kosten=20_000, ersatz_ee_anlage_vor_2008=True)
    erg = berechne_heizung_massnahme(
        m, Regime.NEU, ANTRAGSDATUM_NEU_AB_Q1_2027, zve=None, selbstnutzer=False,
        familienzuschlag=False,
    )
    assert erg["foerderfaehige_kosten"] == 5_000
    assert erg["betrag"] == 5_000 * 0.30


def test_hoechstbetrag_alt_efh():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    grenze, _ = hoechstbetrag_heizung_gesamt(gebaeude, Regime.ALT, ANTRAGSDATUM_ALT)
    assert grenze == 30_000


def test_hoechstbetrag_neu_degression():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    grenze_start, _ = hoechstbetrag_heizung_gesamt(
        gebaeude, Regime.NEU, date(2026, 9, 1)
    )
    assert grenze_start == 28_000
    grenze_feb27, _ = hoechstbetrag_heizung_gesamt(
        gebaeude, Regime.NEU, date(2027, 2, 1)
    )
    assert grenze_feb27 == 27_250


def test_hoechstbetrag_neu_mfh_10we():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=10)
    grenze, _ = hoechstbetrag_heizung_gesamt(gebaeude, Regime.NEU, date(2026, 9, 1))
    # 28.000 (1.WE) + 5x15.000 (WE2-6) + 4x8.000 (ab WE7)
    assert grenze == 28_000 + 5 * 15_000 + 4 * 8_000
