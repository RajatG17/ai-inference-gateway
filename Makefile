.PHONY: up down logs migrate migrate-gen bootstrap

up:
	docker compose -f infra/docker-compose.yml up --build
down:
	docker compose -f infra/docker-compose.yml down -v
logs:
	docker compose -f infra/docker-compose.yml logs -f --tail=200
migrate:
	docker compose -f infra/docker-compose.yml exec api alembic upgrade head
# Generate a new migration from model changes. Usage: make migrate-gen msg="add users table"
migrate-gen:
	docker compose -f infra/docker-compose.yml exec api alembic revision --autogenerate -m "$(msg)"
bootstrap:
	python scripts/bootstrap.py
generate-key:
	docker compose -f infra/docker-compose.yml exec api python scripts/bootstrap.py
get-key:
	make migrate && make generate-key
