from app.calc.steuerbonus_35c import berechne_35c


def test_20_prozent_unter_deckel():
    erg = berechne_35c(50_000)
    assert erg["betrag_gesamt"] == 10_000
    assert erg["gedeckelt"] is False


def test_deckel_40000_je_objekt():
    erg = berechne_35c(300_000)  # 20% davon wären 60.000 -> Deckel greift
    assert erg["betrag_gesamt"] == 40_000
    assert erg["gedeckelt"] is True


def test_jahresstaffelung_summiert_sich_zum_gesamtbetrag():
    erg = berechne_35c(100_000)
    jahressumme = sum(j["betrag"] for j in erg["jahresstaffelung"])
    assert round(jahressumme, 2) == erg["betrag_gesamt"]
    assert erg["jahresstaffelung"] == [
        {"jahr": 1, "satz": 0.07, "betrag": 7_000.0},
        {"jahr": 2, "satz": 0.07, "betrag": 7_000.0},
        {"jahr": 3, "satz": 0.06, "betrag": 6_000.0},
    ]
