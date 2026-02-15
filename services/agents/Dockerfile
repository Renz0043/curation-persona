FROM python:3.12-slim

ARG AGENT
ENV AGENT=${AGENT}

WORKDIR /app

COPY pyproject.toml .
COPY shared/ shared/
COPY ${AGENT}/ ${AGENT}/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD uvicorn ${AGENT}.main:app --host 0.0.0.0 --port 8080
