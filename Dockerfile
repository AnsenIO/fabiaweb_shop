FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl (for healthcheck) + runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "gunicorn>=23,<24" "flask>=3.1,<4" "requests>=2.32"

# Install app deps (requirements.txt may have extras)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code (data/ is bind-mounted at runtime)
COPY . .

# Run as non-root
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8081

CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--workers", "2", "--timeout", "30", "server:app"]
