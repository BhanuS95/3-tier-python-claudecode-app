# Database Initialization Scripts

Place `.sql` or executable `.sh` files here if you need PostgreSQL to
run one-time setup (e.g. `CREATE EXTENSION`) the first time its data
volume is initialized. Files are executed in alphabetical order by the
official `postgres` Docker image on first startup only -- see
`database/README.md` for details.

This project currently has no init scripts; the schema is fully
managed by Alembic migrations in `backend/migrations/`.
