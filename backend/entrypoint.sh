#!/usr/bin/env bash
set -e

echo "==> Waiting for PostgreSQL to be ready..."
until python -c "
import asyncio
import asyncpg

async def check():
    url = '${DATABASE_URL}'.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    await conn.close()

asyncio.run(check())
" 2>/dev/null; do
  echo "Postgres is unavailable - sleeping 1s"
  sleep 1
done

echo "==> PostgreSQL is up and reachable!"

# Only run migrations if this container is the API service or explicit migration runner
if [[ "$*" == *"uvicorn"* ]] || [[ "$1" == "migrate" ]]; then
  echo "==> Running Alembic database migrations..."
  alembic upgrade head
  echo "==> Database migrations applied successfully!"
fi

exec "$@"
