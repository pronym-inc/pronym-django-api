test:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image pytest -c /app/tests/tox.ini
coverage:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image pytest -c /app/tests/tox.ini --cov=/usr/local/lib/python3.6/site-packages/pronym_api
makemigrations:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image python3 /app/manage_django.py makemigrations
