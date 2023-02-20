.PHONY: all down

all:
	docker compose up --build -d

down:
	docker compose down
