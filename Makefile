test:
	docker build -t sanic/test-image .
	docker run -t sanic/test-image python3 /app/manage_django.py test
makemigrations:
	docker build -t sanic/test-image .
	docker run -t sanic/test-image python3 /app/manage_django.py makemigrations
