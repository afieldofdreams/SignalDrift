.PHONY: install dev dev-backend dev-frontend test test-backend test-frontend lint build up down clean

VENV := backend/.venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
install: $(VENV)
	cd frontend && npm install

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -r backend/requirements.txt

# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------
dev:
	@echo "Starting backend and frontend..."
	$(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend:
	cd backend && $(CURDIR)/$(UVICORN) app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test: test-backend test-frontend

test-backend:
	cd backend && $(CURDIR)/$(PYTEST) -v

test-frontend:
	cd frontend && npm test

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------
lint:
	cd backend && $(CURDIR)/$(RUFF) check .
	cd frontend && npm run lint

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/dist backend/build backend/*.egg-info
	rm -rf frontend/dist frontend/dist-ssr frontend/node_modules
