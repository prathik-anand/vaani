PY ?= python
PORT ?= 8765

.PHONY: install run demo stub test clean fmt

install:
	$(PY) -m pip install -e .[dev]

run:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port $(PORT) --reload

# Open the demo (starts server in background, opens browser)
demo:
	@echo "Starting Vaani at http://127.0.0.1:$(PORT) ..."
	@$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port $(PORT) &
	@sleep 1
	@$(PY) -c "import webbrowser; webbrowser.open('http://127.0.0.1:$(PORT)')"

# Force the scripted-stub backend regardless of installed engines (deterministic demo)
stub:
	VAANI_FORCE_STUB=1 $(PY) -m uvicorn app.main:app --host 127.0.0.1 --port $(PORT) --reload

test:
	$(PY) -m pytest -q

clean:
	rm -rf __pycache__ .pytest_cache app/__pycache__ tests/__pycache__ *.egg-info
