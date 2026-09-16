.PHONY: help install-backend install-frontend test-backend test-frontend run-backend run-frontend docker-up docker-down lint

help:
	@echo "NEXORA ATLAS - Development Commands"
	@echo "======================================"
	@echo "make install-backend   Install Python dependencies"
	@echo "make install-frontend  Install Node dependencies"
	@echo "make run-backend       Run FastAPI backend with uvicorn (port 8000)"
	@echo "make run-frontend      Run Vite development server (port 5173)"
	@echo "make test-backend      Run backend pytest suite"
	@echo "make test-frontend     Run frontend vitest suite"
	@echo "make docker-up         Start PostgreSQL and containers via Docker Compose"
	@echo "make docker-down       Stop Docker Compose containers"

install-backend:
	cd apps/api && pip install -r requirements.txt

install-frontend:
	cd apps/web && npm install

run-backend:
	cd apps/api && python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

run-frontend:
	cd apps/web && npm run dev

test-backend:
	cd apps/api && pytest tests -v

test-frontend:
	cd apps/web && npm test

docker-up:
	docker-compose up -d postgres

docker-down:
	docker-compose down
