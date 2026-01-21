## PostgreSQL Tuning for 1 GB RAM Server

This file contains **conservative, production-friendly settings** you can apply to PostgreSQL on a small VM (~1 GB RAM, light load, low concurrency).  
Your system summary:

- **CPU / Load**: system load ~0.02 (very light)
- **Disk**: 44.6% of 23.17 GB used
- **RAM**: 1 GB total, ~62% currently used
- **Swap**: 0%

These settings assume:
- Mostly OLTP-style queries (short/medium, not huge analytics)
- Few concurrent connections (typically \< 50)

---

## 1. `postgresql.conf` Settings

Edit your `postgresql.conf` (or use `ALTER SYSTEM` below) and set values like:

```conf
# CONNECTIONS
max_connections = 50

# MEMORY
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 4MB
maintenance_work_mem = 128MB

# CHECKPOINT / WAL
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 256MB
max_wal_size = 1GB

# QUERY PLANNER
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 50

# LOGGING (optional but recommended)
log_min_duration_statement = 500ms
log_checkpoints = on
log_temp_files = 10MB
log_autovacuum_min_duration = 0
```

After editing `postgresql.conf`, **reload** PostgreSQL:

```bash
sudo systemctl reload postgresql
```

Or, on some systems:

```bash
sudo service postgresql reload
```

---

## 2. Equivalent `ALTER SYSTEM` Commands

If you prefer to apply settings from `psql`, you can run:

```sql
-- Run these in psql as a superuser (e.g. postgres)

ALTER SYSTEM SET max_connections TO '50';

ALTER SYSTEM SET shared_buffers TO '256MB';
ALTER SYSTEM SET effective_cache_size TO '768MB';
ALTER SYSTEM SET work_mem TO '4MB';
ALTER SYSTEM SET maintenance_work_mem TO '128MB';

ALTER SYSTEM SET checkpoint_timeout TO '15min';
ALTER SYSTEM SET checkpoint_completion_target TO '0.9';
ALTER SYSTEM SET wal_buffers TO '16MB';
ALTER SYSTEM SET min_wal_size TO '256MB';
ALTER SYSTEM SET max_wal_size TO '1GB';

ALTER SYSTEM SET default_statistics_target TO '100';
ALTER SYSTEM SET random_page_cost TO '1.1';
ALTER SYSTEM SET effective_io_concurrency TO '50';

ALTER SYSTEM SET log_min_duration_statement TO '500ms';
ALTER SYSTEM SET log_checkpoints TO 'on';
ALTER SYSTEM SET log_temp_files TO '10MB';
ALTER SYSTEM SET log_autovacuum_min_duration TO '0';
```

Then reload the config:

```sql
SELECT pg_reload_conf();
```

---

## 3. Useful Inspection Queries

You can quickly inspect current settings and activity:

```sql
-- Check key memory settings
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW work_mem;
SHOW maintenance_work_mem;

-- Basic health / activity
SELECT now() AS current_time,
       version(),
       current_setting('max_connections') AS max_connections,
       COUNT(*) AS active_connections
FROM pg_stat_activity;

-- Largest tables/indexes (by size)
SELECT relkind,
       relname,
       pg_size_pretty(pg_total_relation_size(oid)) AS total_size
FROM pg_class
WHERE relkind IN ('r','i')
ORDER BY pg_total_relation_size(oid) DESC
LIMIT 20;
```

---

## 4. Notes

- If you routinely see **memory pressure** (swap starting to be used, OOM kills, or high `%mem` from PostgreSQL), **lower**:
  - `shared_buffers` (e.g. to `192MB`)
  - `effective_cache_size` (e.g. `512MB`)
  - `work_mem` (e.g. `2MB`)
- If you have **very few connections** (e.g. 5–10 total), you can slightly increase `work_mem` (e.g. `8MB`) for faster sorts/joins.
- Always **monitor** after changes: CPU, RAM, disk I/O, checkpoints, and autovacuum behavior.

