test:
	docker build -t sanic/test-image .
	docker run -t sanic/test-image python3 /app/runtests.py