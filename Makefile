# Makefile for Security Dashboard
.PHONY: help install dev build run docker-build docker-run docker-compose-up docker-compose-down clean test

# Default environment
ENV_FILE := .env

help: ## Show this help message
	@echo "Security Dashboard - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies in virtual environment
	@echo "📦 Setting up virtual environment and installing dependencies..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

dev: ## Run development server with Flask
	@echo "🚀 Starting development server..."
	. venv/bin/activate && python flaskkk.py

run: ## Run production server with Gunicorn (local)
	@echo "🚀 Starting production server with Gunicorn..."
	./start_gunicorn.sh

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t security-dashboard:latest .
	@echo "✅ Docker image built successfully!"

docker-run: ## Run Docker container
	@echo "🐳 Running Docker container..."
	docker run -d \
		--name security-dashboard \
		-p 5000:5000 \
		--env-file $(ENV_FILE) \
		security-dashboard:latest
	@echo "✅ Container started! Access at http://localhost:5000"

docker-compose-up: ## Start full stack with Docker Compose
	@echo "🐳 Starting full stack with Docker Compose..."
	docker-compose up -d
	@echo "✅ Full stack started! Access at http://localhost:5000"

docker-compose-down: ## Stop Docker Compose stack
	@echo "🛑 Stopping Docker Compose stack..."
	docker-compose down
	@echo "✅ Stack stopped!"

docker-logs: ## View Docker container logs
	docker logs -f security-dashboard

compose-logs: ## View Docker Compose logs
	docker-compose logs -f

clean: ## Clean up containers and images
	@echo "🧹 Cleaning up..."
	-docker stop security-dashboard
	-docker rm security-dashboard
	-docker-compose down
	-docker rmi security-dashboard:latest
	@echo "✅ Cleanup complete!"

test: ## Test the application
	@echo "🧪 Testing application endpoints..."
	curl -f http://localhost:5000/api/ping || echo "❌ Application not running"
	@echo "✅ Test complete!"

status: ## Check application status
	@echo "📊 Checking application status..."
	@echo "Docker containers:"
	@docker ps | grep security || echo "No containers running"
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:5000/api/ping || echo "Application not responding"

production-env: ## Copy production environment template
	@echo "📝 Creating production environment file..."
	cp .env.production .env
	@echo "✅ Please edit .env with your production values!"

backup-db: ## Backup database (Docker Compose)
	@echo "💾 Backing up database..."
	docker exec security_dashboard_db mysqldump -u dashboard -psecurepass security_dashboard > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backed up!"

restore-db: ## Restore database from backup (specify BACKUP_FILE=filename.sql)
	@echo "🔄 Restoring database from $(BACKUP_FILE)..."
	docker exec -i security_dashboard_db mysql -u dashboard -psecurepass security_dashboard < $(BACKUP_FILE)
	@echo "✅ Database restored!"
