# AI Inference Gateway

## Alembic migrations

### Prerequisites

- Postgres running and reachable (e.g. local or `docker compose -f infra/docker-compose.yml up -d postgres`).
- `DATABASE_URL` set (e.g. in `.env` in project root). For local Postgres with default user: `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_gateway`.
- Database created if needed: `createdb ai_gateway`.

### Apply migrations (upgrade to latest)

```bash
alembic upgrade head
```

Or:

```bash
make migrate
```

### Generate a new migration (after changing models)

1. Edit models under `app/models/` (e.g. add a column in `api_key.py` or add a new model).
2. Generate a migration from the diff:

   ```bash
   alembic revision --autogenerate -m "short description of change"
   ```

   Or with Make (set `msg` to your description):

   ```bash
   make migrate-gen msg="add users table"
   ```

3. Review the new file in `alembic/versions/` and fix any optional/indices if needed.
4. Apply it:

   ```bash
   alembic upgrade head
   ```

### Other useful commands

- **Current revision:** `alembic current`
- **Migration history:** `alembic history`
- **Downgrade one revision:** `alembic downgrade -1`
- **Offline SQL (no DB connection):** `alembic upgrade head --sql`
