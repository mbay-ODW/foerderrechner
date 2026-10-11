from app.calc.isfp_erstellung import berechne_isfp_erstellung
from app.calc.models import Gebaeude, GebaeudeTyp, ISFPErstellung

EFH = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=1)
MFH = Gebaeude(typ=GebaeudeTyp.WG, anzahl_we=5)


def test_efh_650_deckel():
    assert berechne_isfp_erstellung(ISFPErstellung(kosten=2_500), EFH)["betrag"] == 650


def test_ab_3_we_850_deckel():
    assert berechne_isfp_erstellung(ISFPErstellung(kosten=2_500), MFH)["betrag"] == 850


def test_unter_deckel_50_prozent():
    assert berechne_isfp_erstellung(ISFPErstellung(kosten=1_000), EFH)["betrag"] == 500


def test_weg_erlaeuterung_250_je_weg_nicht_je_sitzung():
    erg = berechne_isfp_erstellung(
        ISFPErstellung(kosten=2_500, weg_erlaeuterung_kosten=1_200), MFH
    )
    assert erg["betrag_weg_erlaeuterung"] == 250  # Deckel je WEG
    assert erg["betrag"] == 1_100


def test_weg_erlaeuterung_unter_deckel():
    erg = berechne_isfp_erstellung(
        ISFPErstellung(kosten=2_500, weg_erlaeuterung_kosten=300), MFH
    )
    assert erg["betrag_weg_erlaeuterung"] == 150


def test_weg_erlaeuterung_bei_efh_ignoriert():
    erg = berechne_isfp_erstellung(
        ISFPErstellung(kosten=2_500, weg_erlaeuterung_kosten=300), EFH
    )
    assert erg["betrag_weg_erlaeuterung"] == 0
