# PostgreSQL to ClickHouse Data Replication Setup

## Overview

Trigger.dev v4 uses a dual-database architecture for optimal performance:
- **PostgreSQL**: Primary storage for all run data
- **ClickHouse**: Analytics database for fast queries in the UI

**⚠️ IMPORTANT**: By default, the UI queries ClickHouse for displaying runs. If replication is not configured, runs will execute successfully but **won't appear in the UI**.

## Problem Symptoms

- ✅ Tasks execute successfully (visible in supervisor logs)
- ✅ Supervisor connects and reports completion
- ❌ Runs don't appear in the UI at `/orgs/.../projects/.../runs`
- ❌ Run count shows 0 despite successful executions

## Root Cause

The webapp stores runs in PostgreSQL but queries ClickHouse by default for the UI. Without replication, ClickHouse tables remain empty, causing the UI to show no runs.

## Solution Options

### Option 1: Quick Fix - Use PostgreSQL Directly (Recommended for Small Scale)

Force the UI to query PostgreSQL instead of ClickHouse:

```sql
-- Connect to PostgreSQL and run:
INSERT INTO "FeatureFlag" (key, value) 
VALUES ('runsListRepository', 'postgres') 
ON CONFLICT (key) DO UPDATE SET value = 'postgres';
```

This immediately fixes the UI without any replication setup. Suitable for:
- Development environments
- Small to medium production deployments (< 100k runs)
- Quick testing and validation

### Option 2: Full Replication Setup (For Large Scale)

Configure PostgreSQL → ClickHouse logical replication for better performance at scale.

## Full Replication Setup Guide

### Prerequisites

1. PostgreSQL with `wal_level = logical` support
2. ClickHouse instance configured and accessible
3. Redis for coordination (already configured if using Railway template)

### Step 1: Configure PostgreSQL for Logical Replication

```sql
-- 1. Check current WAL level
SHOW wal_level;
-- Should return 'logical'. If it shows 'replica', continue to step 2

-- 2. Change WAL level to logical (requires database restart)
ALTER SYSTEM SET wal_level = 'logical';
-- Note: On Railway managed PostgreSQL, you may need to contact support for this change

-- 3. Set table replica identity for change tracking
ALTER TABLE public."TaskRun" REPLICA IDENTITY FULL;

-- 4. Create publication to expose TaskRun changes
CREATE PUBLICATION task_runs_to_clickhouse_v1_publication FOR TABLE public."TaskRun";

-- 5. Verify publication was created
SELECT * FROM pg_publication WHERE pubname = 'task_runs_to_clickhouse_v1_publication';
```

### Step 2: Restart PostgreSQL

After changing `wal_level`, PostgreSQL must be restarted:
- **Railway**: Restart the PostgreSQL service from the dashboard
- **Self-hosted**: `sudo systemctl restart postgresql`
- **Docker**: `docker restart postgres_container`

### Step 3: Configure Webapp Environment Variables

Add these environment variables to your webapp service (Railway or self-hosted):

```bash
# Enable replication service
RUN_REPLICATION_ENABLED=1

# ClickHouse connection (use your actual connection string)
RUN_REPLICATION_CLICKHOUSE_URL="${{ClickHouse.CLICKHOUSE_URL}}"
# Or for self-hosted:
# RUN_REPLICATION_CLICKHOUSE_URL="http://user:password@clickhouse-host:8123"

# Redis for distributed coordination (use existing Redis service)
RUN_REPLICATION_REDIS_HOST="${{Redis.RAILWAY_PRIVATE_DOMAIN}}"
RUN_REPLICATION_REDIS_PORT="${{Redis.REDISPORT}}"
RUN_REPLICATION_REDIS_PASSWORD="${{Redis.REDISPASSWORD}}"

# Optional performance tuning
RUN_REPLICATION_FLUSH_BATCH_SIZE=100
RUN_REPLICATION_FLUSH_INTERVAL_MS=1000
RUN_REPLICATION_INSERT_STRATEGY=insert
```

### Step 4: Restart Webapp Service

Restart the webapp to start the replication service:
- **Railway**: Redeploy or restart from dashboard
- **Docker**: `docker restart webapp_container`

### Step 5: Verify Replication is Working

#### Check Webapp Logs
Look for these messages indicating successful replication start:
```
🗃️  Clickhouse service enabled to host...
Starting replication client
Connected to PostgreSQL replication slot
Subscribed to PostgreSQL replication
```

#### Check PostgreSQL Replication Status
```sql
-- Should show active replication slot
SELECT slot_name, active, restart_lsn 
FROM pg_replication_slots 
WHERE slot_name = 'task_runs_to_clickhouse_v1';

-- Check publication status
SELECT * FROM pg_stat_replication;
```

#### Check ClickHouse Data Flow
```sql
-- Connect to ClickHouse and check if data is arriving
SELECT COUNT(*) FROM trigger_dev.task_runs_v2;

-- View recent runs
SELECT run_id, created_at, status 
FROM trigger_dev.task_runs_v2 
ORDER BY created_at DESC 
LIMIT 10;
```

### Step 6: Switch UI to Use ClickHouse (Optional)

Once replication is confirmed working:

```sql
-- Update feature flag to use ClickHouse for UI queries
UPDATE "FeatureFlag" 
SET value = 'clickhouse' 
WHERE key = 'runsListRepository';
```

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Supervisor    │────▶│   Webapp     │────▶│   PostgreSQL    │
│  (Task Execution)     │  (Stores Runs)      │  (Primary Storage)
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                       │
                               │                       │ Logical
                               │                       │ Replication
                               │                       ▼
                               │              ┌─────────────────┐
                               │              │   ClickHouse    │
                               └─────────────▶│  (Analytics DB)  │
                                 Queries for  └─────────────────┘
                                 UI Display
```

## Troubleshooting

### Issue: WAL level cannot be changed on managed PostgreSQL

**Solution**: 
- Contact your database provider (Railway, AWS RDS, etc.) to enable logical replication
- Or use Option 1 (PostgreSQL-only) which doesn't require replication

### Issue: Replication slot not created

**Symptoms**: No entry in `pg_replication_slots` after webapp restart

**Check**:
1. Verify `RUN_REPLICATION_ENABLED=1` is set
2. Check webapp logs for connection errors
3. Ensure PostgreSQL allows replication connections
4. Verify `max_replication_slots` > 0 in PostgreSQL

### Issue: ClickHouse connection failures

**Symptoms**: "Failed to connect to ClickHouse" in webapp logs

**Check**:
1. Verify `RUN_REPLICATION_CLICKHOUSE_URL` is correct
2. Test connection: `curl -f "http://user:password@clickhouse-host:8123/ping"`
3. Ensure ClickHouse database `trigger_dev` exists
4. Check ClickHouse tables exist: `task_runs_v2`, `raw_task_runs_payload_v1`

### Issue: Runs still not appearing after replication setup

**Quick Fix**:
```sql
-- Force PostgreSQL backend while investigating
INSERT INTO "FeatureFlag" (key, value) 
VALUES ('runsListRepository', 'postgres') 
ON CONFLICT (key) DO UPDATE SET value = 'postgres';
```

**Then investigate**:
1. Check if data exists in PostgreSQL: `SELECT COUNT(*) FROM "TaskRun"`
2. Check if data reached ClickHouse: `SELECT COUNT(*) FROM trigger_dev.task_runs_v2`
3. Verify environment IDs match between databases

## Performance Considerations

### When to Use PostgreSQL Only (Option 1)
- Development and testing environments
- Small production deployments (< 100k total runs)
- Simple deployment requirements
- When managed PostgreSQL doesn't support logical replication

### When to Use ClickHouse Replication (Option 2)
- Large scale production (> 100k runs)
- Need for complex analytics queries
- Multiple concurrent users viewing run history
- Long-term run data retention requirements

## Migration Notes

### Backfilling Existing Data

If you have existing runs before enabling replication, they won't automatically appear in ClickHouse. To backfill:

1. Use the admin API endpoints (if available)
2. Or temporarily use PostgreSQL backend until new runs populate ClickHouse
3. Consider manual data migration for large datasets

### Switching Between Backends

You can switch between PostgreSQL and ClickHouse at any time using the feature flag:

```sql
-- Use PostgreSQL
UPDATE "FeatureFlag" SET value = 'postgres' WHERE key = 'runsListRepository';

-- Use ClickHouse  
UPDATE "FeatureFlag" SET value = 'clickhouse' WHERE key = 'runsListRepository';
```

## Related Configuration

### Supervisor Configuration
The supervisor doesn't need any special configuration for replication. It always reports to the webapp, which handles storage.

### Required Environment Variables Summary

#### Webapp (Railway or self-hosted)
```bash
# Core database connections (already configured)
DATABASE_URL="${{Postgres.DATABASE_URL}}"
CLICKHOUSE_URL="${{ClickHouse.CLICKHOUSE_URL}}"
REDIS_HOST="${{Redis.RAILWAY_PRIVATE_DOMAIN}}"

# Replication specific (add these)
RUN_REPLICATION_ENABLED=1
RUN_REPLICATION_CLICKHOUSE_URL="${{ClickHouse.CLICKHOUSE_URL}}"
RUN_REPLICATION_REDIS_HOST="${{Redis.RAILWAY_PRIVATE_DOMAIN}}"
RUN_REPLICATION_REDIS_PORT="${{Redis.REDISPORT}}"
RUN_REPLICATION_REDIS_PASSWORD="${{Redis.REDISPASSWORD}}"
```

#### Supervisor (DigitalOcean or other)
No replication-specific configuration needed. Standard configuration from `.railway/docs/SUPERVISOR_DEPLOYMENT.md` applies.

## References

- PostgreSQL Logical Replication: https://www.postgresql.org/docs/current/logical-replication.html
- ClickHouse ReplacingMergeTree: https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/replacingmergetree
- Trigger.dev Architecture: See `ARCHITECTURE.md`