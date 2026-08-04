# Förderrechner

Eigenständiger Förderrechner für die Wohngebäude-Sanierung: BEG Einzelmaßnahmen,
BEG-Heizungsförderung, BEG WG/NWG systemische Sanierung (Effizienzhaus/-gebäude),
§35c-EStG-Steuerbonus als mitgerechnete Alternative, iSFP-Förderung. Fachlich
gespeist aus den Skills `beg-em-foerderung` und `gebaeudeenergierecht`.

Nur Einzelgebäude (keine WEG-/MEA-Logik). Branding (Logo, Firmenname, Kontakt,
Akzentfarbe) über ein Settings-Panel zur Laufzeit konfigurierbar, PDF-Export mit
eigenem Logo.

## Stand

Live unter `https://forderrechner.bay-ram.de` (Authelia-geschützt). Fertig:

- BEG-Einzelmaßnahmen (Hülle/Anlagentechnik/Heizungsoptimierung/Fachplanung),
  ALT+NEU-Regime, iSFP-/WPB-Bonus, Höchstgrenzen-Deckelung
- BEG-Heizungsförderung (Grundförderung, KGB, Einkommensbonus, EU-Wertschöpfungsbonus,
  Familienzuschlag, Degressionsstaffeln)
- BEG WG/NWG systemische Sanierung (Effizienzhaus/-gebäude, Tilgungszuschuss/
  kommunaler Zuschuss, WPB/SerSan/NH-Boni)
- § 35c EStG-Steuerbonus als mitgerechnete Alternative pro Maßnahme
- PDF-Export mit Branding (Logo/Firmenname/Kontakt/Akzentfarbe)
- Beta: KfW-Nebenprogramme (Jung kauft Alt, Wohneigentumsprogramm, Altersgerecht
  Umbauen, Gewerbe zu Wohnen) + iSFP-Erstellungsförderung — **nicht** durch die
  Skill-Referenzen abgesichert, klar als unverifiziert gekennzeichnet
- HERO-Kundensuche (optional, analog Wärmebrücken-Tool): Kunde/Adresse per
  Live-Suche aus HERO übernehmen statt manuell einzutippen

Alle skill-gestützten Module (BEG EM/Heizung/systemisch, §35c) sind gegen die
Rechenbeispiele aus `beg-em-foerderung/references/*.md` per Unit-Test verifiziert
(`tests/`, 36 Tests).

## Lokal starten

```bash
docker compose -f docker-compose.simple.yml up --build
```

Läuft auf `http://localhost:8010`.

## Deployment

Produktivvariante mit Traefik + Authelia: `docker-compose.yml`, Domain
`forderrechner.bay-ram.de`, Portainer-Stack 58 auf TrueNAS (env 1).

**GHCR-Package ist public** (Package-Settings → Change visibility, manuell
umgestellt), `docker pull ghcr.io/mbay-odw/foerderrechner:latest` funktioniert
also grundsätzlich. Der aktuell deployte Stack läuft aber weiterhin auf einem
**lokal auf dem TrueNAS-Host gebauten Image** (`foerderrechner:latest`, kein
Registry-Pfad) — der lokale Build-Workflow ist unverändert der schnellste Weg
für Redeploys ohne CI-Wartezeit:

```bash
# Build-Kontext auf den Host kopieren (Port 5022)
tar --exclude='.git' --exclude='data' --exclude='.venv' --exclude='tests' \
  --exclude='.pytest_cache' -czf /tmp/build.tar.gz .
scp -i ~/.ssh/id_ed25519_truenas -P 5022 /tmp/build.tar.gz \
  truenas_admin@10.0.1.14:/home/truenas_admin/build.tar.gz

# Auf dem Host: entpacken + bauen (truenas_admin hat sudo docker, aber keinen
# direkten Socket-Zugriff)
ssh -i ~/.ssh/id_ed25519_truenas -p 5022 truenas_admin@10.0.1.14 \
  'rm -rf foerderrechner-build && mkdir foerderrechner-build && cd foerderrechner-build \
   && tar xzf ../build.tar.gz && rm ../build.tar.gz && sudo docker build -t foerderrechner:latest .'

# Stack redeployen (Portainer-Token liegt im portainer-mcp-Container, siehe
# reference_portainer_redeploy-Memory): PUT /api/stacks/58?endpointId=1
# mit stackFileContent aus GET /api/stacks/58/file + env aus GET /api/stacks/58
```

### HERO-Kundensuche

Optional, nur aktiv wenn `HERO_TOKEN` als Stack-Env gesetzt ist (identischer
API-Key wie `hero-mcp-server`, host-seitig aus dessen Container-Env gelesen —
Token nie im Klartext committen/loggen). Ohne Token bleibt die Suche in der UI
ausgeblendet, manuelle Kundenerfassung funktioniert immer. Env:

- `HERO_URL` — GraphQL-Endpoint, Default = offizieller HERO-Endpoint
- `HERO_TOKEN` — API-Key mit Lesezugriff auf `project_matches`

## Datenpersistenz

```
data/
├── settings.json    Firmenname, Kontakt, Akzentfarbe
└── logo.*           Firmenlogo
```
