FROM python:3.10.17-slim-trixie

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

EXPOSE 8000

# Environment variables
ENV WORKERS=4
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV LOG_LEVEL=info
ENV TIMEOUT=120

CMD ["sh", "-c", "gunicorn app.main:app --workers $WORKERS --worker-class $WORKER_CLASS --bind $HOST:$PORT --timeout $TIMEOUT --log-level $LOG_LEVEL --access-logfile - --error-logfile - --preload"]