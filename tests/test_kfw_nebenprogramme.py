from app.calc.kfw_nebenprogramme import (
    altersgerecht_umbauen,
    jung_kauft_alt,
    wohneigentumsprogramm,
)


def test_alle_ergebnisse_sind_als_unverifiziert_gekennzeichnet():
    for erg in [
        jung_kauft_alt(2, 50_000),
        wohneigentumsprogramm(),
        altersgerecht_umbauen(1),
    ]:
        assert erg["verifiziert"] is False
        assert "pruefhinweis" in erg


def test_jung_kauft_alt_kredit_staffel():
    assert jung_kauft_alt(1, None)["kredit_max"] == 100_000
    assert jung_kauft_alt(2, None)["kredit_max"] == 150_000
    assert jung_kauft_alt(3, None)["kredit_max"] == 200_000
    assert jung_kauft_alt(5, None)["kredit_max"] == 200_000  # gedeckelt bei 3

