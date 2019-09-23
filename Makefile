test:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image python3 /app/manage_django.py test
coverage:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image python3 /app/manage_django.py coverage
makemigrations:
	docker build -t pronym/test-image .
	docker run --rm -t pronym/test-image python3 /app/manage_django.py makemigrations
