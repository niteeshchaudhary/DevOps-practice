-- Postgres dialect example (use when DB_BACKEND=postgres)
--   DB_BACKEND=postgres ./apply patches/examples/006_postgres_example.sql

INSERT INTO items (id, name, status, updated_at)
VALUES (20, 'pg-service', 'running', NOW()::text)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  status = EXCLUDED.status,
  updated_at = EXCLUDED.updated_at;

UPDATE items
SET status = 'running', updated_at = NOW()::text
WHERE name = 'logger';
