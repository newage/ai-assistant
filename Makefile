COMPOSE = docker compose --env-file .env -f docker/docker-compose.yml

.PHONY: up down rebuild

up:
	$(COMPOSE) up -d --build --wait

down:
	$(COMPOSE) down -v

rebuild:
	$(COMPOSE) down -v
	$(COMPOSE) up --build --wait
	$(COMPOSE) run --rm ai-service python -m scripts.seed_faq data/faq.sample.json
