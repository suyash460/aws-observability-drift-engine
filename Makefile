.PHONY: up down ps logs test tf-validate

up:
	docker-compose up --build -d

down:
	docker-compose down -v

ps:
	docker-compose ps

logs:
	docker-compose logs -f

test:
	docker-compose exec -e PYTHONPATH=. drift-engine python -m pytest -v -o cache_dir=/tmp/.pytest_cache

tf-validate:
	cd infra/terraform && terraform init -backend=false && terraform fmt -check -recursive && terraform validate
