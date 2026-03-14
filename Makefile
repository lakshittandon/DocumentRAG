PYTHON ?= python3

.PHONY: backend-test backend-compile frontend-build plan-docx

backend-test:
	cd backend && $(PYTHON) -m unittest discover -s tests

backend-compile:
	$(PYTHON) -m compileall backend/app

frontend-build:
	cd frontend && npm run build

plan-docx:
	./scripts/export_project_plan.sh

