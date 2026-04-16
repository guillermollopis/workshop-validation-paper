FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force cache bust on every deploy so file changes are picked up
ARG CACHEBUST=2
COPY 08_4afc_experiment.py wsgi.py ./
COPY data/curated/ data/curated/

RUN mkdir -p /data/results /data/sessions

ENV RESULTS_DIR=/data/results
ENV SESSION_DIR=/data/sessions

CMD exec gunicorn wsgi:app \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
