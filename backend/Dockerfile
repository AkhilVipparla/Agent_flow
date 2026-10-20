# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first, so code changes don't invalidate the (slow) install layer.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY demo ./demo

# Never run as root inside the container.
RUN useradd --system --uid 10001 --no-create-home app
USER app

EXPOSE 8000

# Liveness only (no database call), so a slow dependency can't make the platform kill the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["sh", "-c", "python -c \"import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=4)\""]

# --proxy-headers / --forwarded-allow-ips: this image is meant to sit behind a platform load
# balancer (Render, Fly, Cloud Run), which supplies X-Forwarded-For/Proto. Don't expose it
# directly to the internet with these flags. Logs are written by the app, so no access log here.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log --no-server-header"]
