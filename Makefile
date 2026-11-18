.PHONY: check fmt lint types security django-check migrations-check test test-one up down build messages

COMPOSE := docker compose -f docker-compose.local.yml
RUN := $(COMPOSE) run --rm django
# Host-side tools load Django settings but never connect; give them a placeholder DB.
HOST := DATABASE_URL=postgres://unused:unused@localhost:5432/unused uv run --quiet

check: lint types django-check migrations-check test

fmt:
	uv run --quiet black .
	uv run --quiet isort .

lint:
	uv run --quiet black --check .
	uv run --quiet isort --check .
	uv run --quiet flake8
	@if [ -f .importlinter ]; then uv run --quiet lint-imports; else echo "lint-imports: no .importlinter yet"; fi

types:
	$(HOST) mypy .

security:
	uv run --quiet bandit -q -c pyproject.toml -r apps config
	@req=$$(mktemp) && uv export --quiet --format requirements-txt --all-groups --no-emit-project -o $$req \
		&& uv run --quiet pip-audit --strict --disable-pip --require-hashes -r $$req; rc=$$?; rm -f $$req; exit $$rc

django-check:
	$(RUN) python manage.py check

migrations-check:
	$(RUN) python manage.py makemigrations --check --dry-run

test:
	$(RUN) sh -c "coverage run -m pytest -p no:sugar && sh scripts/coverage-gates.sh"

test-one:
	$(RUN) pytest -p no:sugar $(T)

up:
	$(COMPOSE) up -d --remove-orphans

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

messages:
	$(RUN) sh -c "python manage.py makemessages -l fr_FR -l en_US --ignore=.venv && python manage.py compilemessages"
