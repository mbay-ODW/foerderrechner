from app.calc.beg_systemisch import berechne_systemisch, hoechstgrenze_systemisch
from app.calc.models import EffizienzhausStufe, Gebaeude, GebaeudeTyp, Regime, SystemischeSanierung


def test_eh40_alle_boni_kumulierbar():
    """Skill: 'WPB + SerSan + NH sind ALLE untereinander kumulierbar → bis
    +30 Pp (kein Deckel im Text)'."""
    s = SystemischeSanierung(
        stufe=EffizienzhausStufe.EH40_EE, kosten=100_000,
        wpb_bonus=True, sersan_bonus=True, nh_bonus=True,
    )
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    erg = berechne_systemisch(s, gebaeude, Regime.NEU)
    # 10% Grund + 10% WPB + 15% SerSan + 5% NH = 40%
    assert erg["satz_prozentual"] == 0.40
    assert erg["betrag"] == 40_000


def test_eh70_nur_die_dort_verfuegbaren_boni_zaehlen():
    s = SystemischeSanierung(
        stufe=EffizienzhausStufe.EH70_EE, kosten=100_000,
        wpb_bonus=True, sersan_bonus=True, nh_bonus=True,
    )
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    erg = berechne_systemisch(s, gebaeude, Regime.NEU)
    # 0% Grund + 10% WPB + 5% SerSan + 5% NH = 20%
    assert erg["satz_prozentual"] == 0.20


def test_eh85_ist_null_prozent_tilgungszuschuss():
    s = SystemischeSanierung(stufe=EffizienzhausStufe.EH85_EE, kosten=50_000)
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    erg = berechne_systemisch(s, gebaeude, Regime.NEU)
    assert erg["satz_prozentual"] == 0.0
    assert erg["betrag"] == 0.0


def test_kommunaler_zuschuss_statt_tilgungszuschuss():
    s = SystemischeSanierung(stufe=EffizienzhausStufe.EH40_EE, kosten=100_000, kommunal=True)
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    erg = berechne_systemisch(s, gebaeude, Regime.NEU)
    assert erg["satz_prozentual"] == 0.25


def test_hoechstgrenze_wg_150000_je_we():
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=3)
    grenze, _ = hoechstgrenze_systemisch(gebaeude)
    assert grenze == 450_000


def test_deckelung_bei_ueberschreitung_der_hoechstgrenze():
    s = SystemischeSanierung(stufe=EffizienzhausStufe.EH40_EE, kosten=200_000)
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)  # Grenze 150.000
    erg = berechne_systemisch(s, gebaeude, Regime.NEU)
    assert erg["gedeckelt"] is True
    assert erg["foerderfaehige_kosten"] == 150_000
    assert erg["betrag"] == 15_000  # 10% von 150.000, nicht von 200.000


def test_alt_regime_tilgungszuschuss_vergleichswerte():
    s = SystemischeSanierung(stufe=EffizienzhausStufe.EH40_EE, kosten=100_000)
    gebaeude = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
    erg = berechne_systemisch(s, gebaeude, Regime.ALT)
    assert erg["satz_prozentual"] == 0.20
