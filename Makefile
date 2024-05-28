start:
	docker compose -f docker-compose.yaml -p dupish up -d --build
stop:
	docker compose -f docker-compose.yaml -p dupish down

