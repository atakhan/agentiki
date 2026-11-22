# Сборка и локальный запуск agentiki.
# Список целей: make help

UV      ?= uv
NPM     ?= npm
COMPOSE ?= docker compose
HOST    ?= 127.0.0.1
PORT    ?= 8000

WEB_DIR   := web
VENV      := .venv
PY_STAMP  := $(VENV)/.install-stamp
WEB_STAMP := $(WEB_DIR)/node_modules/.install-stamp
WEB_DIST  := $(WEB_DIR)/dist/.build-stamp

WEB_INPUTS := $(WEB_DIR)/index.html \
	$(WEB_DIR)/vite.config.ts \
	$(WEB_DIR)/tsconfig.json \
	$(WEB_DIR)/tsconfig.app.json \
	$(WEB_DIR)/tsconfig.node.json \
	$(WEB_DIR)/package.json \
	$(WEB_DIR)/package-lock.json \
	$(shell find $(WEB_DIR)/src -type f)

.DEFAULT_GOAL := help

.PHONY: help build install install-python install-web build-web build-image \
	check test test-verbose serve dev-api dev-web preview up down clean distclean

help:
	@printf '%s\n' \
		'Сборка' \
		'  make build         зависимости и web/dist (локальный артефакт)' \
		'  make build-web     только фронтенд: tsc + vite → web/dist' \
		'  make build-image   образ приложения через docker compose' \
		'  make install       uv sync --frozen и npm ci' \
		'' \
		'Проверка' \
		'  make check         сборка фронтенда и unittest' \
		'  make test          python -m unittest discover -s tests' \
		'  make test-verbose  то же с -v' \
		'' \
		'Запуск' \
		'  make serve         uvicorn без reload, UI из web/dist' \
		'  make dev-api       uvicorn --reload на $(HOST):$(PORT)' \
		'  make dev-web       Vite на :5173, прокси /api → :8000' \
		'  make preview       vite preview собранного UI' \
		'  make up            docker compose up --build' \
		'  make down          docker compose down' \
		'' \
		'Очистка' \
		'  make clean         web/dist и кэши Python' \
		'  make distclean     clean, плюс .venv и web/node_modules' \
		'' \
		'Переменные: UV, NPM, COMPOSE, HOST, PORT'

build: $(PY_STAMP) $(WEB_DIST)

install: install-python install-web

install-python: $(PY_STAMP)

install-web: $(WEB_STAMP)

$(PY_STAMP): pyproject.toml uv.lock
	$(UV) sync --frozen
	@touch $@

$(WEB_STAMP): $(WEB_DIR)/package.json $(WEB_DIR)/package-lock.json
	cd $(WEB_DIR) && $(NPM) ci
	@touch $@

build-web: $(WEB_DIST)

$(WEB_DIST): $(WEB_STAMP) $(WEB_INPUTS)
	cd $(WEB_DIR) && $(NPM) run build
	@touch $@

build-image:
	$(COMPOSE) build

check: $(WEB_DIST) test

test: $(PY_STAMP)
	$(UV) run python -m unittest discover -s tests

test-verbose: $(PY_STAMP)
	$(UV) run python -m unittest discover -s tests -v

serve: $(PY_STAMP) $(WEB_DIST)
	$(UV) run uvicorn agentiki.server.main:app --host $(HOST) --port $(PORT)

dev-api: $(PY_STAMP)
	$(UV) run uvicorn agentiki.server.main:app --reload --host $(HOST) --port $(PORT)

dev-web: $(WEB_STAMP)
	cd $(WEB_DIR) && $(NPM) run dev

preview: $(WEB_DIST)
	cd $(WEB_DIR) && $(NPM) run preview

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

clean:
	rm -rf $(WEB_DIR)/dist *.egg-info src/*.egg-info
	find src tests -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache

distclean: clean
	rm -rf $(VENV) $(WEB_DIR)/node_modules
