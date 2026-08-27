FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8001

WORKDIR /app
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt
COPY apps/api /app/apps/api
COPY apps/stocks-app/data /app/apps/stocks-app/data

WORKDIR /app/apps/api
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001
CMD ["sh", "-c", "if [ -z \"$DATABASE_URL\" ] && [ ! -f database/prj008.sqlite3 ]; then SHOULD_SEED=1; fi; python -m alembic upgrade head; if [ \"$SHOULD_SEED\" = \"1\" ]; then python -m scripts.seed_database; fi; exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
