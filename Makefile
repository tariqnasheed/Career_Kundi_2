# =============================================================================
# Careerkundi — Makefile
# Single entry point for every common dev/build/test/deploy task. Run
# `make help` to see this list. Every target below mirrors a command that
# is also documented in full in README.md.
# =============================================================================

# The .PHONY list tells Make that these aren't real files. For example, when you run 
# `make build`, it won't look for a file named "build", it will just run the command.
.PHONY: help install sync lock build test test-backend test-frontend test-e2e \
        test-coverage lint format migrate seed seed-role-packs build-skill-knowledge sync-role-catalog \
        dev dev-backend dev-frontend \
        docker-build docker-up docker-down docker-logs clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup & Dependencies ---------------------------------------------------

install: ## Install all backend + frontend dependencies
	cd backend && uv sync --all-extras
	cd frontend && npm install

sync: ## Re-sync backend dependencies from pyproject.toml
	cd backend && uv sync --all-extras

lock: ## Regenerate uv.lock from pyproject.toml
	cd backend && uv lock

build: ## Build production frontend bundle + backend wheel
	cd frontend && npm run build
	cd backend && uv build

# --- Local Development ------------------------------------------------------

dev: ## Run backend + frontend dev servers concurrently (requires two terminals normally;
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."

dev-backend: ## Start FastAPI with hot-reload on :8000
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start Vite dev server with hot-reload on :5173
	cd frontend && npm run dev

# --- Database -------------------------------------------------------------

migrate: ## Apply all pending Alembic database migrations
	cd backend && uv run alembic upgrade head

migration: ## Create a new Alembic migration (usage: make migration name="add_x")
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

seed: ## Populate the database with demo data (user, jobs, roadmaps, CVs)
	cd backend && uv run python scripts/seed.py

seed-role-packs: ## Pre-generate role packs (JSON/Markdown/metadata only — no PDFs)
	cd backend && uv run python -m scripts.seed_role_packs

seed-role-packs-force: ## Regenerate all pre-seeded role packs (JSON/Markdown; no PDFs)
	cd backend && uv run python -m scripts.seed_role_packs --force

seed-role-packs-pdf: ## EXPLICIT: regenerate missing PDFs from existing structured JSON
	cd backend && uv run python -m scripts.seed_role_packs --pdf-only

seed-role-packs-pdf-force: ## EXPLICIT: regenerate all PDFs (overwrite existing)
	cd backend && uv run python -m scripts.seed_role_packs --pdf-only --force

build-skill-knowledge: ## Build PhD-level skill/role knowledge JSON
	cd backend && uv run python scripts/build_skill_knowledge.py

sync-role-catalog: ## Sync popular_roles_catalog.json from frontend TS definitions
	python3 scripts/sync_role_catalog.py

# --- Testing & Code Quality -------------------------------------------------

test: test-backend test-frontend ## Run all backend + frontend unit tests

test-backend: ## Run backend pytest suite
	cd backend && uv run pytest -v

test-frontend: ## Run frontend vitest suite
	cd frontend && npm test -- --run

test-e2e: ## Run Playwright end-to-end browser tests
	cd frontend && npm run test:e2e

test-coverage: ## Generate HTML coverage reports for backend + frontend
	cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term
	cd frontend && npm run test:coverage

lint: ## Lint backend (ruff) + frontend (eslint)
	cd backend && uv run ruff check . && uv run mypy app
	cd frontend && npm run lint

format: ## Auto-format backend (black) + frontend (prettier)
	cd backend && uv run black . && uv run ruff check --fix .
	cd frontend && npm run format

# --- Docker & Production ----------------------------------------------------

docker-build: ## Build all Docker images defined in docker-compose.yml
	docker compose build

docker-up: ## Start the full stack (frontend, backend, db, redis, nginx)
	docker compose up --build

docker-down: ## Stop and remove all containers (keep volumes)
	docker compose down

docker-down-volumes: ## Stop containers AND delete volumes (full reset)
	docker compose down -v

docker-logs: ## Tail logs from every running service
	docker compose logs -f

clean: ## Remove all build artifacts, caches, and generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache backend/htmlcov
	rm -rf frontend/dist frontend/coverage
