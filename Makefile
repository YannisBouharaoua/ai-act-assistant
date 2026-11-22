.PHONY: install test lint eval serve

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check . && ruff format --check .

eval:
	ai-act eval

serve:
	ai-act serve
