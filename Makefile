.PHONY: dev backend test build eval docs migrate compose

backend:
	APP_MODE=demo .venv/bin/uvicorn human_api.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

dev:
	./scripts/dev.sh

test:
	.venv/bin/pytest -q

build:
	cd frontend && npm run build

eval:
	PYTHONPATH=backend .venv/bin/python evaluations/evaluate_retrieval.py

docs:
	.venv/bin/python scripts/build_deliverables.py

migrate:
	.venv/bin/alembic upgrade head

compose:
	cd frontend && npm ci && npm run build
	docker compose up --build
