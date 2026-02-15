FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY shared/ shared/
COPY collector/ collector/
COPY librarian/ librarian/
COPY researcher/ researcher/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD uvicorn ${AGENT}.main:app --host 0.0.0.0 --port 8080
