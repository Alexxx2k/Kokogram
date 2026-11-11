ifneq (,$(wildcard .env))
include .env
export
endif

COMPOSE = docker compose -f docker-compose.test.yml

.PHONY: help up up-full svc down restart ps logs clean migrate migrate-down

help: ## Показать список команд
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

up: ## Поднять инфраструктуру (profile infra) и дождаться готовности
	$(COMPOSE) --profile infra up -d --build --wait --wait-timeout 180

up-full: ## Поднять всю систему (profile full): инфраструктура и сервисы
	$(COMPOSE) --profile full up -d --build --wait --wait-timeout 180

svc: ## Пересобрать и перезапустить один сервис в Docker: make svc s=users
	@test -n "$(s)" || (echo "Использование: make svc s=users" && exit 1)
	$(COMPOSE) --profile full up -d --build --no-deps --wait $(s)

ps: ## Статус контейнеров
	$(COMPOSE) --profile full ps

down: ## Остановить контейнеры (данные сохраняются)
	$(COMPOSE) --profile full down

clean: ## Остановить и удалить данные (тома)
	$(COMPOSE) --profile full down -v

restart: down up ## Перезапустить инфраструктуру

logs: ## Логи: make logs s=users (без s показывает все)
	$(COMPOSE) --profile full logs --tail 50 $(s)

migrate: ## Применить миграции (alembic upgrade head)
	python -m alembic -c db/alembic.ini upgrade head

migrate-down: ## Откатить все миграции (alembic downgrade base)
	python -m alembic -c db/alembic.ini downgrade base
