# Förderrechner

Eigenständiger Förderrechner für die Wohngebäude-Sanierung: BEG Einzelmaßnahmen,
BEG-Heizungsförderung, BEG WG/NWG systemische Sanierung (Effizienzhaus/-gebäude),
§35c-EStG-Steuerbonus als mitgerechnete Alternative, iSFP-Förderung. Fachlich
gespeist aus den Skills `beg-em-foerderung` und `gebaeudeenergierecht`.

Nur Einzelgebäude (keine WEG-/MEA-Logik). Branding (Logo, Firmenname, Kontakt,
Akzentfarbe) über ein Settings-Panel zur Laufzeit konfigurierbar, PDF-Export mit
eigenem Logo.

## Stand

Live deployed hinter Traefik + Authelia (Host/Domain bewusst nicht in diesem
öffentlichen Repo — wird ausschließlich über die private Deploy-Umgebung
verwaltet). Fertig:

- BEG-Einzelmaßnahmen (Hülle/Anlagentechnik/Heizungsoptimierung/Fachplanung),
  ALT+NEU-Regime, iSFP-/WPB-Bonus, Höchstgrenzen-Deckelung
- BEG-Heizungsförderung (Grundförderung, KGB, Einkommensbonus, EU-Wertschöpfungsbonus,
  Familienzuschlag, Degressionsstaffeln)
- BEG WG/NWG systemische Sanierung (Effizienzhaus/-gebäude, Tilgungszuschuss/
  kommunaler Zuschuss, WPB/SerSan/NH-Boni)
- § 35c EStG-Steuerbonus als mitgerechnete Alternative pro Maßnahme
- PDF-Export mit Branding (Logo/Firmenname/Kontakt/Akzentfarbe)
- iSFP-Erstellung (BAFA-Energieberatung) als eigene Maßnahme: 50 %, max. 650 €
  (EFH/ZFH) bzw. 850 € (ab 3 WE); bei WEG zusätzlich Erläuterung in der
  Eigentümerversammlung (50 %, max. 250 € je WEG — nicht je Sitzung). Quelle:
  Förderdatenbank des Bundes, vor Antragstellung Merkblatt prüfen
- Beta: KfW-Nebenprogramme (Jung kauft Alt, Wohneigentumsprogramm, Altersgerecht
  Umbauen, Gewerbe zu Wohnen) — **nicht** durch die Skill-Referenzen
  abgesichert, klar als unverifiziert gekennzeichnet
- HERO-Kundensuche (optional, analog Wärmebrücken-Tool): Kunde/Adresse per
  Live-Suche aus HERO übernehmen statt manuell einzutippen
- Editierbarer Konditionen-Tab im Settings-Menü: alle Sätze/Boni/Höchstgrenzen/
  Stichtage als JSON, wirkt sofort auf die nächste Berechnung (kein Redeploy
  nötig, wenn sich die Förderrichtlinie ändert)

Alle skill-gestützten Module (BEG EM/Heizung/systemisch, §35c) sind gegen die
Rechenbeispiele aus `beg-em-foerderung/references/*.md` per Unit-Test verifiziert
(`tests/`).

## Lokal starten

```bash
docker compose -f docker-compose.simple.yml up --build
```

Läuft auf `http://localhost:8010`.

## Deployment

Produktivvariante mit Traefik + Authelia: `docker-compose.yml`. Der Hostname
wird bewusst NICHT im Compose-File hardcodiert, sondern per `${DOMAIN}`-Env
zur Deploy-Zeit gesetzt (Portainer-Stack-Env bzw. lokale `.env`) — Host/IP/
Stack-Details der konkreten Produktivumgebung sind absichtlich nicht Teil
dieses öffentlichen Repos, siehe private Ops-Dokumentation.

**GHCR-Package ist public** (Package-Settings → Change visibility, manuell
umgestellt), `docker pull ghcr.io/mbay-odw/foerderrechner:latest` funktioniert
also grundsätzlich. Alternativ lässt sich das Image auch lokal auf dem
Zielhost bauen (`docker build -t foerderrechner:latest .`) für einen
CI-unabhängigen Redeploy-Zyklus — Details dazu in der privaten Ops-Doku.

### HERO-Kundensuche

Optional, nur aktiv wenn `HERO_TOKEN` als Stack-Env gesetzt ist (identischer
API-Key wie `hero-mcp-server`, host-seitig aus dessen Container-Env gelesen —
Token nie im Klartext committen/loggen). Ohne Token bleibt die Suche in der UI
ausgeblendet, manuelle Kundenerfassung funktioniert immer. Env:

- `HERO_URL` — GraphQL-Endpoint, Default = offizieller HERO-Endpoint
- `HERO_TOKEN` — API-Key mit Lesezugriff auf `project_matches`

### Konditionen anpassen

Settings → Tab „Konditionen": alle Fördersätze/Boni/Höchstgrenzen/Stichtage als
JSON editierbar (`app/calc/konditionen_store.py` definiert `DEFAULT_KONDITIONEN`
als Referenz). Änderungen werden in `DATA_DIR/konditionen.json` persistiert und
überstehen Container-Updates (Volume-Mount). „Auf Original zurücksetzen" stellt
die Skill-verifizierten Ausgangswerte wieder her — bei Zweifeln an einem
editierten Wert also immer ein sicherer Ausweg. Die Unit-Tests in `tests/`
prüfen ausschließlich gegen `DEFAULT_KONDITIONEN` (Funktionsaufrufe ohne
`k`-Parameter), nie gegen editierte Laufzeitwerte.

## Datenpersistenz

```
data/
├── settings.json      Firmenname, Kontakt, Akzentfarbe
├── konditionen.json   Fördersätze/Boni/Höchstgrenzen/Stichtage (editierbar)
└── logo.*             Firmenlogo
```
