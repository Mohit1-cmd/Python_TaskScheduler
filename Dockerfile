# ── Stage 1: deps layer (cached unless requirements.txt changes) ──
FROM python:3.10-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: app image ──
FROM base AS app

COPY . .

# Default: show help; override with docker run ... python cli.py <cmd>
CMD ["python", "cli.py", "--help"]
