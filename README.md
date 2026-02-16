# SignalDrift

Full-stack application with a FastAPI backend and React (Vite + TypeScript) frontend.

## Prerequisites

- Python 3.13+
- Node.js 20+
- Docker & Docker Compose (for containerized deployment)

## Quick Start

```bash
# 1. Clone and enter the repo
cd Claude_demo

# 2. Copy the environment file
cp .env.example .env

# 3. Install dependencies
make install

# 4. Run locally (backend + frontend in parallel)
make dev
```

Backend runs at **http://localhost:8000**, frontend at **http://localhost:5173**.

## Running with Docker

```bash
make build   # Build images
make up      # Start containers
make down    # Stop containers
```

Frontend served at **http://localhost:3000**, backend at **http://localhost:8000**.

## Makefile Targets

| Target             | Description                                  |
| ------------------ | -------------------------------------------- |
| `make dev`         | Run backend + frontend locally (parallel)    |
| `make dev-backend` | Run FastAPI with hot reload                  |
| `make dev-frontend`| Run Vite dev server                          |
| `make test`        | Run all tests (backend + frontend)           |
| `make test-backend`| Run pytest                                   |
| `make test-frontend`| Run vitest                                  |
| `make lint`        | Run ruff (backend) + eslint (frontend)       |
| `make build`       | Build Docker images via compose              |
| `make up`          | `docker compose up -d`                       |
| `make down`        | `docker compose down`                        |
| `make clean`       | Remove build artifacts, caches, node_modules |
| `make install`     | Install all dependencies (pip + npm)         |

## Project Structure

```
├── backend/          # FastAPI application
│   ├── app/          # Application code
│   ├── tests/        # pytest test suite
│   └── pyproject.toml
├── frontend/         # React + Vite + TypeScript
│   ├── src/          # Application code
│   └── vite.config.ts
├── docker-compose.yml
├── Makefile
└── README.md
```

## Secret Management

- A single `.env.example` at the project root documents all expected variables with placeholders.
- `.env` is gitignored -- copy from `.env.example` and fill in real values.
- Backend reads the root `.env` via `pydantic-settings` and validates at startup.
- Frontend reads the root `.env` via Vite's `envDir` config (`VITE_` prefix vars only).
