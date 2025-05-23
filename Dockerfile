FROM python:3.13-alpine AS builder

WORKDIR /app
COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && pip install --user --no-cache-dir -r requirements.txt \
    && apk del .build-deps

FROM python:3.13-alpine

WORKDIR /app


COPY --from=builder /root/.local /root/.local
COPY . .


RUN apk add --no-cache curl bash libffi openssl


ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "pytest tests/ || true && python main.py"]
