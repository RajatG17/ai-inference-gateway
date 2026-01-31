.PHONY: up down logs

up:
	docker compose -f infra/docker-compose.yml up --build
down:
	docker compose -f infra/docker-compose.yml down -v
logs:
	docker compose -f infra/docker-compose.yml logs -f --tail=200