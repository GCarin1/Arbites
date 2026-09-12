# Arbites — imagem única: o FastAPI serve a API e o build da SPA na mesma
# origem. É isso que permite a sessão viver num cookie httpOnly sem CORS e
# sem token no navegador (ADR 0011, capability auth).

# -- estágio 1: build da SPA --------------------------------------------------
FROM node:22-alpine AS frontend

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# -- estágio 2: runtime -------------------------------------------------------
FROM python:3.12-slim

# O runner local executa Behave num subprocess (ADR 0004); sem git, um alvo
# de automação clonado não atualiza.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/arbites ./backend/arbites
COPY --from=frontend /build/dist ./frontend/dist

# Roda sem privilégio: a aplicação executa subprocessos, então um root aqui
# transformaria qualquer falha do runner num comprometimento da máquina.
RUN useradd --create-home --uid 10001 arbites \
    && mkdir -p /data/workspace \
    && chown -R arbites:arbites /app /data
USER arbites

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    ARBITES_WORKSPACE=/data/workspace \
    ARBITES_FRONTEND_DIST=/app/frontend/dist

# Volume: o workspace (fonte de verdade) e o `.arbites/auth.db` (contas,
# sessões e log de atividade — insubstituível, ADR 0011) vivem aqui.
VOLUME ["/data"]

EXPOSE 8347

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8347/api/v1/health').read()"

CMD ["python", "-m", "uvicorn", "arbites.api:app", \
     "--host", "0.0.0.0", "--port", "8347"]
