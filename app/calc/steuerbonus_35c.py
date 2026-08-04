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

SATZ_GESAMT = 0.20
HOECHSTGRENZE_JE_OBJEKT = 40_000.0

JAHRESSTAFFELUNG = [
    (1, 0.07, 14_000.0),
    (2, 0.07, 14_000.0),
    (3, 0.06, 12_000.0),
]


def berechne_35c(kosten_summe: float) -> dict:
    foerderfaehige_kosten = min(kosten_summe, HOECHSTGRENZE_JE_OBJEKT / SATZ_GESAMT)
    gedeckelt = kosten_summe > foerderfaehige_kosten
    gesamtbetrag = foerderfaehige_kosten * SATZ_GESAMT

    jahre = []
    for jahr, satz, max_betrag in JAHRESSTAFFELUNG:
        betrag = min(foerderfaehige_kosten * satz, max_betrag)
        jahre.append({"jahr": jahr, "satz": satz, "betrag": round(betrag, 2)})

    rechenweg = [
        f"§ 35c EStG: {SATZ_GESAMT:.0%} der Kosten über 3 Jahre, Deckel "
        f"{HOECHSTGRENZE_JE_OBJEKT:,.0f} €/Objekt",
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
        "hoechstgrenze": HOECHSTGRENZE_JE_OBJEKT,
        "gedeckelt": gedeckelt,
        "betrag_gesamt": round(gesamtbetrag, 2),
        "jahresstaffelung": jahre,
        "rechenweg": rechenweg,
    }
