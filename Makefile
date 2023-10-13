PYTHON_SRC= $(wildcard jukelify/*.py)
.PHONY: venv

venv:
	python3.11 -m virtualenv venv --prompt .

install-prod:
	pip install -r requirements.txt

install-dev: install-prod
	pip install -r requirements-dev.txt

lint:
	autoflake --in-place --remove-all-unused-imports $(PYTHON_SRC)
	flake8 $(PYTHON_SRC) --max-line-length=100

fmt:
	isort $(PYTHON_SRC)
	black $(PYTHON_SRC)

ck: lint fmt

serve:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload