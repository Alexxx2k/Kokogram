ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE = docker compose -f docker-compose.test.yml

.PHONY: help up down restart ps logs clean migrate migrate-down

help: ## Показать список команд
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

up: ## Поднять инфраструктуру (profile infra) и дождаться готовности
	$(COMPOSE) --profile infra up -d --build --wait --wait-timeout 180

ps: ## Статус контейнеров
	$(COMPOSE) --profile infra ps

down: ## Остановить контейнеры (данные сохраняются)
	$(COMPOSE) --profile infra down

clean: ## Остановить и удалить данные (тома)
	$(COMPOSE) --profile infra down -v

restart: down up ## Перезапустить инфраструктуру

logs: ## Логи: make logs s=seaweedfs (без s показывает все)
	$(COMPOSE) --profile infra logs --tail 50 $(s)

migrate: ## применить миграции (alembic upgrade head)
	python -m alembic -c db/alembic.ini upgrade head

migrate-down: ## откатить все миграции (alembic downgrade base)
	python -m alembic -c db/alembic.ini downgrade base
