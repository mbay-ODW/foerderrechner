# Förderrechner

Eigenständiger Förderrechner für die Wohngebäude-Sanierung: BEG Einzelmaßnahmen,
BEG-Heizungsförderung, BEG WG/NWG systemische Sanierung (Effizienzhaus/-gebäude),
§35c-EStG-Steuerbonus als mitgerechnete Alternative, iSFP-Förderung. Fachlich
gespeist aus den Skills `beg-em-foerderung` und `gebaeudeenergierecht`.

Nur Einzelgebäude (keine WEG-/MEA-Logik). Branding (Logo, Firmenname, Kontakt,
Akzentfarbe) über ein Settings-Panel zur Laufzeit konfigurierbar, PDF-Export mit
eigenem Logo.

## Stand

Aktuell: Infrastruktur-Skelett (FastAPI + statisches Frontend, Settings/Branding,
Deployment). Die Förderlogik wird schrittweise ergänzt (siehe Plan).

## Lokal starten

```bash
docker compose -f docker-compose.simple.yml up --build
```

Läuft auf `http://localhost:8010`.

## Deployment

Produktivvariante mit Traefik + Authelia: `docker-compose.yml`, Domain
`forderrechner.bay-ram.de`. Siehe `abnahme-service`-Repo für das identische
Deploy-Muster (Portainer-Stack, GHCR-Image via GitHub Actions).

## Datenpersistenz

```
data/
├── settings.json    Firmenname, Kontakt, Akzentfarbe
└── logo.*           Firmenlogo
```
