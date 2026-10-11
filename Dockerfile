FROM python:3.12-slim
# Docker-Secrets: NAME_FILE=/run/secrets/... wird beim Start zu NAME geladen
COPY --chmod=0755 env-secrets.sh /usr/local/bin/env-secrets

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# UID 1026 / GID 100 matches the host setup (Synology/TrueNAS convention)
RUN groupadd -g 100 -o app 2>/dev/null || true \
 && useradd -m -u 1026 -g 100 -o app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN mkdir -p /data && chown -R 1026:100 /data /srv

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

ENTRYPOINT ["/usr/local/bin/env-secrets"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
