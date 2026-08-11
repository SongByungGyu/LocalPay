#!/bin/sh
set -eu

echo "[entrypoint] Waiting for database..."
# alembic will fail if DB is not ready; short retry
for i in 1 2 3 4 5 6 7 8 9 10; do
    if alembic upgrade head 2>&1 | tail -5; then
        echo "[entrypoint] Migrations applied."
        break
    fi
    echo "[entrypoint] Migration attempt $i failed, retrying in 3s..."
    sleep 3
done

if [ "${SEED_ON_START:-false}" = "true" ]; then
    echo "[entrypoint] Seeding demo data (SEED_ON_START=true)..."
    python -m app.seed.run_seed || echo "[entrypoint] Seed failed (non-fatal)."
fi

echo "[entrypoint] Starting uvicorn on 0.0.0.0:8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level "${LOG_LEVEL:-info}"
