# Jakebot Labs Dashboard

Week 1 Build — FastAPI backend + Preact frontend for managing agent memory (ChromaDB) and healthkit.

## Features

- **Memory Search**: Query vector memory with semantic search
- **Memory Status**: View chunks, graph nodes/edges, sync status
- **System Status**: Check persistent-memory and agent-healthkit status
- **Dark Theme**: GitHub-inspired dark UI

## Quick Start

### Install

```bash
pip install -e .
```

### Start

```bash
jakebot-dashboard start
```

### Open

```
http://localhost:7842
```

## Development

### Backend Development

```bash
make dev
```

Runs with auto-reload on port 7842.

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Runs Vite dev server on port 5173 with hot module reload.

### Build Frontend

```bash
make build
```

Builds frontend and copies to `backend/static/`.

### Run Tests

```bash
make test
```

## Stack

- **Backend**: FastAPI + Uvicorn + Pydantic v2 + Click
- **Frontend**: Preact + Vite + TypeScript + Tailwind CSS + uPlot + Zustand
- **Memory**: ChromaDB + SentenceTransformers
- **Port**: 7842
- **Auth**: Bearer token middleware (disabled by default)

## API Endpoints

### Memory

- `GET /api/memory/search?q={query}&n={limit}` - Search vector memory
- `GET /api/memory/files` - List indexed files
- `GET /api/memory/status` - Get memory system status

### System

- `GET /api/system/status` - Get system and product status
- `GET /health` - Health check

## Configuration

Set environment variables with `JAKEBOT_DASHBOARD_` prefix:

```bash
export JAKEBOT_DASHBOARD_HOST=0.0.0.0
export JAKEBOT_DASHBOARD_PORT=7842
export JAKEBOT_DASHBOARD_AUTH_ENABLED=true
export JAKEBOT_DASHBOARD_AUTH_TOKEN=your-secret-token
```

Or create `.env` file in project root.

## Project Structure

```
jakebot-dashboard/
├── backend/
│   ├── adapters/      # External system adapters
│   ├── models/        # Pydantic models
│   ├── routers/       # FastAPI routers
│   ├── static/        # Built frontend files
│   ├── auth.py        # Auth middleware
│   ├── cli.py         # CLI commands
│   ├── config.py      # Configuration
│   └── main.py        # FastAPI app
├── frontend/          # Preact + Vite app
├── tests/             # Pytest tests
├── Makefile           # Build targets
└── pyproject.toml     # Package config
```

## License

MIT
