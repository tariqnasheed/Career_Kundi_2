# =============================================================================
# Careerkundi Backend — Production Dockerfile
# Multi-stage build: a "builder" stage installs dependencies with UV into a
# self-contained virtualenv, then a slim "runtime" stage copies only what's
# needed to run, keeping the final image small and free of build tooling.
# =============================================================================

# --- Stage 1: builder ---------------------------------------------------------
FROM python:3.11-slim AS builder

# Install UV by copying its static binary from the official distroless image.
# This is faster and smaller than `pip install uv`.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy only dependency manifests first so Docker can cache this layer and
# skip re-resolving dependencies when only application code changes.
COPY pyproject.toml uv.lock ./

# Create a venv and install all production dependencies via uv.
RUN uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python \
        fastapi uvicorn python-multipart pydantic pydantic-settings email-validator \
        sqlalchemy alembic asyncpg psycopg2-binary redis \
        langchain langchain-community langgraph langchain-google-genai google-generativeai \
        faiss-cpu networkx sentence-transformers \
        playwright beautifulsoup4 lxml httpx \
        weasyprint python-docx markdown2 \
        python-jose bcrypt slowapi \
        structlog opentelemetry-api opentelemetry-sdk prometheus-client \
        tenacity python-slugify

# --- Stage 2: runtime -----------------------------------------------------------
FROM python:3.11-slim AS runtime

# System libraries required by WeasyPrint (PDF rendering) and Playwright
# (headless Chromium) at runtime. Kept minimal and pinned to slim variants.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
        libffi8 shared-mime-info \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
        libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring in the pre-built virtualenv from the builder stage — no compilers
# or package managers needed in the final image.
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install the Chromium browser binary used by the web-scraping tools.
# (Skipped automatically if PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 is set, useful
# for CI image builds that don't need live scraping.)
RUN playwright install --with-deps chromium || true

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=10 --start-period=20s \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations then start the server. Using `sh -c` so both commands run
# in sequence as the container's single foreground process.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
