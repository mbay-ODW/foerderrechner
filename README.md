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
`forderrechner.bay-ram.de`, Portainer-Stack 58 auf TrueNAS (env 1).

**GHCR-Image-Pull funktioniert aktuell nicht:** das GitHub-Actions-Workflow
pusht zwar nach `ghcr.io/mbay-odw/foerderrechner:latest`, das Package ist aber
privat, und die Sichtbarkeit lässt sich nicht per API umstellen (GitHub gibt
404 zurück — bekanntes Gotcha, siehe `abnahme-service`, dessen Package manuell
über die GitHub-Weboberfläche auf public gestellt wurde). Bis das für dieses
Repo ebenso manuell erledigt ist (Package-Settings → Change visibility →
Public), läuft der deployte Stack auf einem **lokal auf dem Host gebauten
Image** (`foerderrechner:latest`, kein Registry-Pfad):

```bash
# Build-Kontext auf den Host kopieren (Port 5022)
tar --exclude='.git' --exclude='data' -czf /tmp/build.tar.gz .
scp -i ~/.ssh/id_ed25519_truenas -P 5022 /tmp/build.tar.gz \
  truenas_admin@10.0.1.14:/home/truenas_admin/foerderrechner-build/build.tar.gz

# Auf dem Host: entpacken + bauen (truenas_admin hat sudo docker, aber keinen
# direkten Socket-Zugriff)
ssh -i ~/.ssh/id_ed25519_truenas -p 5022 truenas_admin@10.0.1.14 \
  'cd foerderrechner-build && tar xzf build.tar.gz && sudo docker build -t foerderrechner:latest .'

# Stack redeployen (Portainer-Token liegt im portainer-mcp-Container, siehe
# reference_portainer_redeploy-Memory): PUT /api/stacks/58?endpointId=1
```

## Datenpersistenz

```
data/
├── settings.json    Firmenname, Kontakt, Akzentfarbe
└── logo.*           Firmenlogo
```
