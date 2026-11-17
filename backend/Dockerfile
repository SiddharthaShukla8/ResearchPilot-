FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini entrypoint.sh ./
COPY migrations/ ./migrations/
COPY src/ ./src/

RUN pip install --no-cache-dir -e . && pip install --no-cache-dir greenlet "email-validator>=2.0.0"

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "researchpilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
