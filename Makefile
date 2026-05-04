.PHONY: help up down build logs init-data backend frontend clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services with Docker Compose
	docker compose up -d

up-build: ## Build and start all services
	docker compose up --build -d

down: ## Stop all services
	docker compose down

build: ## Build Docker images
	docker compose build

logs: ## Tail logs from all services
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-frontend: ## Tail frontend logs
	docker compose logs -f frontend

init-data: ## Run the data init script inside the backend container
	docker compose exec backend python scripts/init_data.py

backend-shell: ## Open a shell in the backend container
	docker compose exec backend bash

frontend-shell: ## Open a shell in the frontend container
	docker compose exec frontend sh

dev-backend: ## Run backend locally (requires venv)
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend: ## Run frontend locally
	cd frontend && npm run dev

install-backend: ## Install backend Python dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend Node dependencies
	cd frontend && npm install

clean: ## Remove all containers, volumes, and images
	docker compose down -v --rmi local
