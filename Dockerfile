FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for timezones, zipping large files efficiently, and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends tzdata curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data dirs
RUN mkdir -p /data/uploads /data/archives

# Gunicorn for production serving
ENV PORT=8080
EXPOSE 8080

# Healthcheck to ensure the app is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

CMD ["gunicorn", "-w", "2", "-k", "gthread", "--threads", "8", "--timeout", "300", "-b", "0.0.0.0:8080", "app:app"]
