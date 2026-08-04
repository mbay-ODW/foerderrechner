"""Alt/Neu-Weiche nach Skill `beg-em-foerderung`, Abschnitt 1 + references/uebergang.md.

Vereinfachung ggü. dem vollen Entscheidungsbaum: dieser Rechner kennt nur das
Antragsdatum, nicht ob bereits ein Zuwendungsbescheid vorliegt oder eine
TPB/BzA vor dem Stichtag erstellt wurde. Für Bestandsprojekte mit Bescheid
MUSS das Regime daher explizit auf ALT gesetzt werden (nicht AUTO) — der
Rechner kann das aus dem Antragsdatum allein nicht sicher ableiten.
"""

from __future__ import annotations

from datetime import date

from .models import Regime

# Stichtag Altkonditionen: Antragstellung bis 20.07.2026 (BAFA 23:59 Uhr) →
# ALT. Ab 21.07.2026 gilt die neue Richtlinie. Quelle: uebergang.md.
STICHTAG_ALT_NEU = date(2026, 7, 20)

# Degressions-/Inkrafttretens-Stichtage für "ab Quartal 1 2027"-Regelungen.
# Die Richtlinie nennt kein Tagesdatum — als Näherung wird der erste
# Degressionsstichtag der Heizungsförderung (01.02.2027) verwendet, an dem
# laut uebergang.md auch WPB-Bonus/WP-Regeln/EE-Ersatz-Ausschlüsse greifen.
Q1_2027_STICHTAG = date(2027, 2, 1)

DEGRESSIONSSTUFEN_HEIZUNG_WE1 = [
    (date(2026, 7, 21), 28000),
    (date(2027, 2, 1), 27250),
    (date(2027, 8, 1), 26500),
    (date(2028, 2, 1), 25750),
    (date(2028, 8, 1), 25000),
    (date(2029, 2, 1), 24250),
    (date(2029, 8, 1), 23500),
    (date(2030, 2, 1), 22750),
    (date(2030, 8, 1), 22000),
]

DEGRESSIONSSTUFEN_KGB = [
    (date(2026, 7, 21), 0.16),
    (date(2027, 2, 1), 0.12),
    (date(2027, 8, 1), 0.08),
    (date(2028, 2, 1), 0.04),
    (date(2028, 8, 1), 0.0),
]


def bestimme_regime(antragsdatum: date, explizit: Regime) -> Regime:
    """Regime nach Antragsdatum, sofern nicht explizit vorgegeben."""
    if explizit != Regime.AUTO:
        return explizit
    return Regime.ALT if antragsdatum <= STICHTAG_ALT_NEU else Regime.NEU


def ist_ab_q1_2027(antragsdatum: date) -> bool:
    return antragsdatum >= Q1_2027_STICHTAG


def heizung_hoechstbetrag_erste_we(antragsdatum: date) -> float:
    """Förderfähige Höchstausgaben für die 1. WE (NEU-Regime), degressiv
    nach Antragsdatum gestaffelt."""
    betrag = DEGRESSIONSSTUFEN_HEIZUNG_WE1[0][1]
    for stichtag, wert in DEGRESSIONSSTUFEN_HEIZUNG_WE1:
        if antragsdatum >= stichtag:
            betrag = wert
    return betrag


def klimageschwindigkeitsbonus_satz(antragsdatum: date) -> float:
    """KGB-Satz im NEU-Regime, degressiv ab 01.02.2027 (alle 3 Monate -4 Pp
    lt. Skill-Kurzfassung; Detailtabelle in konditionen-neu.md nennt
    01.02./01.08.-Stufen bis 0% ab 01.08.2028)."""
    satz = DEGRESSIONSSTUFEN_KGB[0][1]
    for stichtag, wert in DEGRESSIONSSTUFEN_KGB:
        if antragsdatum >= stichtag:
            satz = wert
    return satz
