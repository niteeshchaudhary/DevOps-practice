-- Example SQL patch: run with
--   ./apply 005_sql_example.sql
-- or
--   python apply.py patches/005_sql_example.sql

INSERT INTO items (id, name, status, updated_at)
VALUES (10, 'sql-service', 'running', datetime('now'))
ON CONFLICT(id) DO UPDATE SET
  name = excluded.name,
  status = excluded.status,
  updated_at = excluded.updated_at;

UPDATE items
SET status = 'running', updated_at = datetime('now')
WHERE name = 'logger';
