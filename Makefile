IMAGE_NAME ?= ghcr.io/puc-behring-institute-for-ai/seja
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
SEJA_DEV_TAG ?= seja:dev
DOCKER_BUILDKIT := 1
COMPOSE_FILE := docker-compose.yml

.PHONY: help build build-local test test-cli test-unit test-integration test-invariants test-local lint typecheck format clean install-dev install image push sign sign-blob verify validate release changelog version security-scan

help:
	@echo 'SEJA — Makefile'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image with version tag
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(IMAGE_NAME):$(VERSION) \
		-t $(IMAGE_NAME):latest \
		--cache-from type=registry,ref=$(IMAGE_NAME):buildcache \
		--cache-to type=registry,ref=$(IMAGE_NAME):buildcache,mode=max \
		-f Dockerfile .

build-local: ## Build single-arch dev image (fast, local testing)
	docker build -t $(SEJA_DEV_TAG) -f Dockerfile .

test-local: build-local ## Build and test container locally
	@echo "=== Starting test container ==="
	docker rm -f seja-test 2>/dev/null; \
	docker run -d --name seja-test \
		-e SEJA_RUN_MIGRATIONS=true \
		-e SEJA_DB_PATH=/tmp/seja-test.db \
		-p 18765:8765 \
		$(SEJA_DEV_TAG) >/dev/null 2>&1
	@echo "Waiting 10s for server startup..."
	@sleep 10
	@echo ""
	@echo "=== Healthcheck ==="
	@STATUS=$$(docker inspect seja-test --format '{{.State.Health.Status}}' 2>/dev/null || echo "not_found"); \
	echo "Container status: $$STATUS"
	@echo ""
	@echo "=== HTTP Health Endpoint ==="
	@curl -sf http://localhost:18765/health && echo "" || echo "(endpoint not responding yet)"
	@echo ""
	@echo "=== Container Logs ==="
	@docker logs seja-test 2>&1 | tail -30
	@echo ""
	@docker inspect seja-test --format '{{.State.Health.Status}}' 2>/dev/null | grep -q healthy && \
		echo "✓ Container is healthy" || \
		( echo "✗ Container is not healthy"; docker logs seja-test 2>&1 | tail -10; \
		docker rm -f seja-test >/dev/null 2>&1; exit 1 )
	@docker rm -f seja-test >/dev/null 2>&1
	@echo "✓ Test passed"

test: test-cli test-unit test-integration test-invariants ## Run all test suites

test-cli: ## Run CLI tests with bats
	bats tests/cli/

test-unit: ## Run unit tests only
	python -m pytest tests/unit -v --cov=mcp --cov-report=term-missing

test-integration: ## Run integration tests only
	python -m pytest tests/integration -v

test-invariants: ## Run invariant tests (critical — tests that forbidden tools do not exist)
	python -m pytest tests/invariants -v

lint: ## Run ruff linter on mcp/
	python -m ruff check mcp/

typecheck: ## Run mypy on mcp/
	python -m mypy mcp/

format: ## Run ruff format on mcp/
	python -m ruff format mcp/

clean: ## Clean Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

install-dev: ## Install dev dependencies
	pip install -e mcp/[dev]

install: ## Install production dependencies
	pip install -e mcp/

image: build ## Build Docker image (alias for build)

push: ## Push Docker image to registry
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

sign: ## Sign Docker image with cosign (keyless)
	cosign sign $(IMAGE_NAME):$(VERSION) --yes
	cosign sign $(IMAGE_NAME):latest --yes

sign-blob: ## Sign CLI script with cosign sign-blob (keyless)
	cosign sign-blob scripts/seja --b64 --output-signature scripts/seja.sig --yes

verify: ## Verify cosign signature
	cosign verify $(IMAGE_NAME):$(VERSION) --certificate-identity-regexp '.*' --certificate-oidc-issuer https://token.actions.githubusercontent.com

validate: lint typecheck test ## Run all validation steps (lint + typecheck + test)

release: test build sign push sign-blob ## Full release pipeline

changelog: ## Generate changelog from git log
	@git log --oneline --no-decorate --pretty=format:"* %s" $$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD 2>/dev/null || echo "No tags found"

version: ## Show current version from git describe
	@echo $(VERSION)

security-scan: ## Run trivy or grype on the image (if available)
	@if command -v trivy >/dev/null 2>&1; then \
		trivy image $(IMAGE_NAME):$(VERSION); \
	elif command -v grype >/dev/null 2>&1; then \
		grype $(IMAGE_NAME):$(VERSION); \
	else \
		echo "No security scanner found (trivy or grype)"; \
	fi
