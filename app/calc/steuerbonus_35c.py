"""§ 35c EStG — Steuerbonus für energetische Sanierungsmaßnahmen am
selbstgenutzten Wohngebäude, als Alternative zur BEG-Förderung.

Kernwerte aus dem Skill `beg-em-foerderung` (references/uebergang.md,
Beratungshinweise): „20 % über 3 Jahre, max. 40.000 €/Objekt; nicht mit
BEG-Zuschuss/Kredit kumulierbar" — stabil, unabhängig von der BEG-Reform
2026 (§ 35c ist unverändert seit Einführung 2020). Die gesetzliche
Jahresstaffelung (7 % / 7 % / 6 %, BMF-Anwendungsschreiben zu § 35c EStG) ist
etabliertes, langjährig stabiles Steuerrecht — NICHT Teil der geladenen
BEG-Skill-Referenzen, hier als informative Aufteilung des Gesamtbetrags
ergänzt.

Die 40.000-€-Deckelung gilt PRO OBJEKT (gesamtes Gebäude), nicht pro
Einzelmaßnahme — alle Maßnahmen, die über § 35c statt als BEG-Zuschuss
beantragt werden, teilen sich diesen einen Deckel.
"""

from __future__ import annotations

from .konditionen_store import DEFAULT_KONDITIONEN


def berechne_35c(kosten_summe: float, k: dict = DEFAULT_KONDITIONEN) -> dict:
    k35c = k["steuerbonus_35c"]
    satz_gesamt = k35c["satz_gesamt"]
    hoechstgrenze = k35c["hoechstgrenze_je_objekt"]

    foerderfaehige_kosten = min(kosten_summe, hoechstgrenze / satz_gesamt)
    gedeckelt = kosten_summe > foerderfaehige_kosten
    gesamtbetrag = foerderfaehige_kosten * satz_gesamt

    jahre = []
    for jahr, satz, max_betrag in k35c["jahresstaffelung"]:
        betrag = min(foerderfaehige_kosten * satz, max_betrag)
        jahre.append({"jahr": jahr, "satz": satz, "betrag": round(betrag, 2)})

    rechenweg = [
        f"§ 35c EStG: {satz_gesamt:.0%} der Kosten über 3 Jahre, Deckel "
        f"{hoechstgrenze:,.0f} €/Objekt",
    ]
    if gedeckelt:
        rechenweg.append(
            f"Kosten {kosten_summe:,.0f} € übersteigen die für den Deckel "
            f"maßgebliche Grenze ({foerderfaehige_kosten:,.0f} €) — gedeckelt"
        )
    rechenweg.append(
        "Jahresstaffelung: 7 % (Jahr 1) + 7 % (Jahr 2) + 6 % (Jahr 3), "
        "je max. 14.000 €/14.000 €/12.000 €"
    )

    return {
        "kosten_summe": round(kosten_summe, 2),
        "foerderfaehige_kosten": round(foerderfaehige_kosten, 2),
        "hoechstgrenze": hoechstgrenze,
        "gedeckelt": gedeckelt,
        "betrag_gesamt": round(gesamtbetrag, 2),
        "jahresstaffelung": jahre,
        "rechenweg": rechenweg,
    }
