"""Domain-Modelle für den Förderrechner.

Nur Einzelgebäude (ein Förderempfänger) — keine WEG-/MEA-Aufteilungslogik.
Ein Gebäude kann trotzdem mehrere Wohneinheiten haben (Vermieter-MFH); das
beeinflusst nur die WE-Staffel der Höchstgrenzen, nicht die Antragsteller-
Struktur.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Regime(str, Enum):
    ALT = "ALT"
    NEU = "NEU"
    AUTO = "AUTO"


class GebaeudeTyp(str, Enum):
    WG = "WG"
    NWG = "NWG"


class EMKategorie(str, Enum):
    HUELLE = "huelle"                          # 5.1 — Dämmung, Fenster, Türen, Sonnenschutz
    ANLAGENTECHNIK = "anlagentechnik"           # 5.2 — Lüftung, MSR, Kälte
    HEIZUNGSOPT_EFFIZIENZ = "heizungsopt_eff"   # 5.4a
    HEIZUNGSOPT_EMISSION = "heizungsopt_em"     # 5.4b — Biomasse-Staub
    FACHPLANUNG = "fachplanung"                 # 5.5


class Waermequelle(str, Enum):
    """Für die BEG-Heizungsförderung relevante Wärmepumpen-Herkunft (EU-
    Wertschöpfungsbonus ab Quartal 1 2027)."""
    WP_EU = "wp_eu"
    WP_NICHT_EU = "wp_nicht_eu"
    BIOMASSE = "biomasse"
    SONSTIGE_EE = "sonstige_ee"


class Gebaeude(BaseModel):
    typ: GebaeudeTyp = GebaeudeTyp.WG
    anzahl_we: int = Field(default=1, ge=1)
    nwg_flaeche_m2: float | None = None  # Nettoraumfläche, nur bei NWG


class Antragsteller(BaseModel):
    selbstnutzer: bool = True
    zve: float | None = None  # zu versteuerndes Haushaltsjahreseinkommen
    kind_minderjaehrig: bool = False


class EMMassnahme(BaseModel):
    kategorie: EMKategorie
    bezeichnung: str = ""
    kosten: float = Field(gt=0)
    isfp_vorhanden: bool = False
    isfp_alter_jahre: float | None = None
    wpb_gebaeude: bool = False  # Worst Performing Building nachgewiesen
    ist_daemmung: bool = False  # 5.1a — nur relevant für HUELLE (WPB-Bonus-Voraussetzung)


class HeizungMassnahme(BaseModel):
    bezeichnung: str = ""
    kosten: float = Field(gt=0)
    waermequelle: Waermequelle = Waermequelle.SONSTIGE_EE
    ersatz_funktionstuechtige_oel_kohle_gasetagen_nachtspeicher: bool = False
    ersatz_gas_biomasse_ab_20_jahre: bool = False
    ersatz_ee_anlage_baujahr_ab_2008: bool = False  # NEU: schließt ab Q1/2027 aus
    ersatz_ee_anlage_vor_2008: bool = False          # NEU: nur 25% foerderfaehig ab Q1/2027


class CalcInput(BaseModel):
    regime: Regime = Regime.AUTO
    antragsdatum: date
    gebaeude: Gebaeude
    antragsteller: Antragsteller
    em_massnahmen: list[EMMassnahme] = []
    heizung_massnahmen: list[HeizungMassnahme] = []
