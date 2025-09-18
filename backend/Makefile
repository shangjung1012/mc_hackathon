.PHONY: dev dev-https

dev:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-https:
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 --ssl-keyfile certs/localhost-key.pem --ssl-certfile certs/localhost.pem

