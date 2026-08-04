"""Alt/Neu-Weiche nach Skill `beg-em-foerderung`, Abschnitt 1 + references/uebergang.md.

Vereinfachung ggü. dem vollen Entscheidungsbaum: dieser Rechner kennt nur das
Antragsdatum, nicht ob bereits ein Zuwendungsbescheid vorliegt oder eine
TPB/BzA vor dem Stichtag erstellt wurde. Für Bestandsprojekte mit Bescheid
MUSS das Regime daher explizit auf ALT gesetzt werden (nicht AUTO) — der
Rechner kann das aus dem Antragsdatum allein nicht sicher ableiten.

Alle Stichtage/Degressionsstaffeln kommen aus `konditionen_store` (editierbar
im Settings-Tab „Konditionen"); ohne `k`-Parameter gelten die Defaults aus
`DEFAULT_KONDITIONEN` — genau das, was die Unit-Tests prüfen.
"""

from __future__ import annotations

from datetime import date

from .konditionen_store import DEFAULT_KONDITIONEN, parse_date_pairs
from .models import Regime


def bestimme_regime(antragsdatum: date, explizit: Regime, k: dict = DEFAULT_KONDITIONEN) -> Regime:
    """Regime nach Antragsdatum, sofern nicht explizit vorgegeben."""
    if explizit != Regime.AUTO:
        return explizit
    stichtag = date.fromisoformat(k["regime"]["stichtag_alt_neu"])
    return Regime.ALT if antragsdatum <= stichtag else Regime.NEU


def ist_ab_q1_2027(antragsdatum: date, k: dict = DEFAULT_KONDITIONEN) -> bool:
    stichtag = date.fromisoformat(k["regime"]["q1_2027_stichtag"])
    return antragsdatum >= stichtag


def heizung_hoechstbetrag_erste_we(antragsdatum: date, k: dict = DEFAULT_KONDITIONEN) -> float:
    """Förderfähige Höchstausgaben für die 1. WE (NEU-Regime), degressiv
    nach Antragsdatum gestaffelt."""
    stufen = parse_date_pairs(k["regime"]["degression_heizung_we1"])
    betrag = stufen[0][1]
    for stichtag, wert in stufen:
        if antragsdatum >= stichtag:
            betrag = wert
    return betrag


def klimageschwindigkeitsbonus_satz(antragsdatum: date, k: dict = DEFAULT_KONDITIONEN) -> float:
    """KGB-Satz im NEU-Regime, degressiv ab 01.02.2027 (alle 3 Monate -4 Pp
    lt. Skill-Kurzfassung; Detailtabelle in konditionen-neu.md nennt
    01.02./01.08.-Stufen bis 0% ab 01.08.2028)."""
    stufen = parse_date_pairs(k["regime"]["degression_kgb"])
    satz = stufen[0][1]
    for stichtag, wert in stufen:
        if antragsdatum >= stichtag:
            satz = wert
    return satz
