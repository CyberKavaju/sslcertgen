set shell := ["bash", "-cu"]

python := "python3.12"

install:
    {{python}} -m pip install --upgrade pip
    {{python}} -m pip install -r requirements-dev.txt

lint:
    ruff check .

format-check:
    ruff format --check .

type-check:
    mypy app

test:
    pytest -m "unit or integration" --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=60

check-all: lint format-check type-check test

start: docker-dev

docker-dev:
    @if ss -ltn | grep -E ':(80|443)\s' >/dev/null; then \
        echo "Error: ports 80 and/or 443 are already bound. Stop conflicting services and retry."; \
        exit 1; \
    fi
    @echo "Starting SSL Certificate Generator..."
    @echo ""
    @echo "Open the app at:"
    @echo "  → http://127.0.0.1"
    @echo "  → https://127.0.0.1"
    @echo ""
    docker compose -f deployment/docker-compose.yml up --build

docker-prod-cert DOMAIN EMAIL:
    ./deployment/scripts/obtain-le-cert.sh {{DOMAIN}} {{EMAIL}}

docker-prod DOMAIN:
    DOMAIN={{DOMAIN}} docker compose -f deployment/docker-compose.prod.yml up -d
