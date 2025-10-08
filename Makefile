setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

lint: setup
	./venv/bin/black *.py

run:
	./venv/bin/python run.py