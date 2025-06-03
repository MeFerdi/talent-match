FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for opencv-python and others
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    bash \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]