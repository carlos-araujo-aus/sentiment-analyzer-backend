FROM python:3.11-slim

RUN rm -f /etc/apt/sources.list.d/mongodb-org-6.0.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system appgroup && adduser --system --no-create-home --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Run gunicorn using shell form to allow environment variable expansion
CMD gunicorn --bind 0.0.0.0:$PORT run:app