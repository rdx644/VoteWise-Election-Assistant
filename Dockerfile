FROM python:3.12-slim

# Security: non-root user
RUN groupadd -r votewise && useradd -r -g votewise -d /app -s /sbin/nologin votewise

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/

# Set ownership
RUN chown -R votewise:votewise /app

USER votewise

# Environment
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
