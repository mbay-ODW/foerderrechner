"""Energieberatung für Wohngebäude (BAFA) — Zuschuss zur Erstellung des iSFP.

Quelle: Förderdatenbank des Bundes, Richtlinie „Energieberatung für
Wohngebäude" (Nr. 7.2): 50 % des förderfähigen Beratungshonorars, höchstens
650 € (Ein-/Zweifamilienhaus) bzw. 850 € (ab 3 Wohneinheiten, gilt auch für
WEG). Zusätzlich für die Erläuterung des Berichts in der Eigentümerversammlung
(nur WEG): höchstens 250 € PRO BERATENER WEG — nicht je Sitzung, mehrere
Versammlungen erhöhen den Deckel nicht. Stand der Recherche 2026-10-11, Laufzeit
der Richtlinie lt. Förderfibel bis 31.12.2026 — vor Beratung Merkblatt prüfen.

Dieses Programm ist von den BEG-Einzelmaßnahmen unabhängig (eigener Antrag,
eigene Deckel) und fließt deshalb additiv in den Gesamtzuschuss.
"""

from __future__ import annotations

from .konditionen_store import DEFAULT_KONDITIONEN
from .models import Gebaeude, ISFPErstellung

PRUEFHINWEIS = (
    "Quelle: BAFA-Richtlinie Energieberatung für Wohngebäude (Förderdatenbank). "
    "Laufzeit/Sätze vor Antragstellung im aktuellen Merkblatt prüfen."
)


def berechne_isfp_erstellung(
    isfp: ISFPErstellung, gebaeude: Gebaeude, k: dict = DEFAULT_KONDITIONEN,
) -> dict:
    ki = k["isfp_erstellung"]
    ab_3_we = gebaeude.anzahl_we >= 3
    satz = ki["satz"]
    hoechstbetrag = ki["hoechstbetrag_ab_3_we"] if ab_3_we else ki["hoechstbetrag_efh_zfh"]

    beratung = min(isfp.kosten * satz, hoechstbetrag)
    rechenweg = [
        f"Beratungshonorar {isfp.kosten:,.2f} € × {satz:.0%} = {isfp.kosten * satz:,.2f} €, "
        f"Höchstbetrag {'ab 3 WE' if ab_3_we else 'EFH/ZFH'}: {hoechstbetrag:,.0f} € "
        f"→ {beratung:,.2f} €"
    ]

    weg_betrag = 0.0
    if isfp.weg_erlaeuterung_kosten > 0:
        if ab_3_we:
            w_satz = ki["weg_erlaeuterung_satz"]
            w_max = ki["weg_erlaeuterung_hoechstbetrag_je_weg"]
            weg_betrag = min(isfp.weg_erlaeuterung_kosten * w_satz, w_max)
            rechenweg.append(
                f"Erläuterung Eigentümerversammlung {isfp.weg_erlaeuterung_kosten:,.2f} € × "
                f"{w_satz:.0%}, Deckel {w_max:,.0f} € je WEG (nicht je Sitzung) "
                f"→ {weg_betrag:,.2f} €"
            )
        else:
            rechenweg.append(
                "Erläuterung in der Eigentümerversammlung ist nur für WEG/ab 3 WE "
                "förderfähig — ignoriert."
            )

    return {
        "kosten": isfp.kosten,
        "weg_erlaeuterung_kosten": isfp.weg_erlaeuterung_kosten,
        "betrag_beratung": round(beratung, 2),
        "betrag_weg_erlaeuterung": round(weg_betrag, 2),
        "betrag": round(beratung + weg_betrag, 2),
        "hoechstbetrag": hoechstbetrag,
        "rechenweg": rechenweg,
        "pruefhinweis": PRUEFHINWEIS,
    }
