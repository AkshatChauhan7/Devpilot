# DevPilot Execution Runner Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    docker.io \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (but needs docker group for container execution)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Run execution service
CMD ["python", "-m", "app.main"]