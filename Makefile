.PHONY: dev build test install clean help

help:
	@echo "Jakebot Labs Dashboard - Make targets"
	@echo ""
	@echo "  install    Install package in development mode"
	@echo "  dev        Start development server with auto-reload"
	@echo "  build      Build frontend and copy to backend/static"
	@echo "  test       Run pytest tests"
	@echo "  clean      Clean build artifacts"

install:
	pip install -e .

dev:
	uvicorn backend.main:app --host 127.0.0.1 --port 7842 --reload

build:
	cd frontend && npm run build && cp -r dist/* ../backend/static/

test:
	pytest tests/ -v

clean:
	rm -rf backend/static/*
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
