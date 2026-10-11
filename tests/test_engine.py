from datetime import date

from app.calc.engine import berechne
from app.calc.models import (
    Antragsteller,
    CalcInput,
    EMKategorie,
    EMMassnahme,
    Gebaeude,
    GebaeudeTyp,
    Regime,
)


def _base_input(**kwargs):
    defaults = dict(
        regime=Regime.NEU,
        antragsdatum=date(2026, 9, 1),
        gebaeude=Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1),
        antragsteller=Antragsteller(selbstnutzer=True),
        em_massnahmen=[],
        heizung_massnahmen=[],
    )
    defaults.update(kwargs)
    return CalcInput(**defaults)


def test_massnahme_mit_steuerbonus_flag_landet_nicht_im_beg_zuschuss():
    m = EMMassnahme(
        kategorie=EMKategorie.HUELLE, kosten=20_000, steuerbonus_statt_zuschuss=True,
    )
    result = berechne(_base_input(em_massnahmen=[m]))
    assert result["beg_em"]["zuschuss"] == 0
    assert result["beg_em"]["massnahmen"] == []
    assert result["steuerbonus_35c"] is not None
    assert result["steuerbonus_35c"]["betrag_gesamt"] == 20_000 * 0.20


def test_gemischte_massnahmen_beg_und_steuerbonus_getrennt():
    m1 = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=10_000)  # BEG-Zuschuss
    m2 = EMMassnahme(
        kategorie=EMKategorie.ANLAGENTECHNIK, kosten=10_000, steuerbonus_statt_zuschuss=True,
    )
    result = berechne(_base_input(em_massnahmen=[m1, m2]))
    assert len(result["beg_em"]["massnahmen"]) == 1
    assert result["beg_em"]["zuschuss"] == 10_000 * 0.15
    assert result["steuerbonus_35c"]["betrag_gesamt"] == 10_000 * 0.20
    assert result["gesamtvorteil_inkl_steuerbonus"] == round(
        result["zuschuss_gesamt"] + result["steuerbonus_35c"]["betrag_gesamt"], 2
    )


def test_ohne_steuerbonus_massnahmen_ist_35c_block_none():
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=10_000)
    result = berechne(_base_input(em_massnahmen=[m]))
    assert result["steuerbonus_35c"] is None


def test_isfp_bonus_neu_engine_170000_efh():
    """Gemeldeter Fall: früher 5 % × (170.000 − 30.000) = 7.000 € angezeigt."""
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=170_000, isfp_vorhanden=True)
    result = berechne(_base_input(em_massnahmen=[m]))
    # förderfähig 60.000 × 15 % = 9.000 + Bonus 5 % × 30.000 = 1.500
    assert result["beg_em"]["zuschuss"] == 10_500
    assert result["beg_em"]["hoechstgrenze"] == 60_000
    assert not any("7,000" in z for z in result["beg_em"]["massnahmen"][0]["rechenweg"])


def test_isfp_bonus_neu_engine_dach_50000():
    m = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=50_000, isfp_vorhanden=True)
    result = berechne(_base_input(em_massnahmen=[m]))
    assert result["beg_em"]["zuschuss"] == 8_500


def test_isfp_erstellung_fliesst_in_gesamtzuschuss():
    from app.calc.models import ISFPErstellung
    result = berechne(_base_input(isfp_erstellung=ISFPErstellung(kosten=2_000)))
    assert result["isfp_erstellung"]["betrag"] == 650
    assert result["zuschuss_gesamt"] == 650


def test_einzelzeilen_summieren_sich_zum_gedeckelten_blockzuschuss():
    m1 = EMMassnahme(kategorie=EMKategorie.HUELLE, kosten=40_000)
    m2 = EMMassnahme(kategorie=EMKategorie.ANLAGENTECHNIK, kosten=20_000)  # 60.000 > 30.000
    result = berechne(_base_input(em_massnahmen=[m1, m2]))
    zeilen = sum(m["betrag"] for m in result["beg_em"]["massnahmen"])
    assert result["beg_em"]["zuschuss"] == 4_500  # 30.000 × 15 %
    assert round(zeilen, 2) == result["beg_em"]["zuschuss"]
