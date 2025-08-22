# Troubleshooting Guide

## Common Issues and Solutions

### Migration Issues

#### Prisma P3009 Error: Failed Migrations
**Error**: `migrate found failed migrations in the target database`

**Cause**: Previous migration attempt failed, blocking new migrations.

**Solution**:
```bash
# Connect to Railway PostgreSQL
PGPASSWORD="your-password" psql -h your-host.proxy.rlwy.net -p port -U postgres -d railway

# Check failed migrations
SELECT migration_name, finished_at, logs 
FROM _prisma_migrations 
WHERE finished_at IS NULL;

# Remove failed migration record
DELETE FROM _prisma_migrations 
WHERE migration_name = 'failed_migration_name';
```

#### Type Already Exists Error
**Error**: `type "AuthenticationMethod" already exists`

**Cause**: Trying to apply consolidated migration to database with existing schema.

**Solution**:
```bash
# Option 1: Reset database (if data loss acceptable)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# Option 2: Use for fresh Railway deployment
railway up --detach  # On a new service
```

#### No Migrations Found
**Error**: `No migrations found in internal-packages/database/prisma/migrations`

**Solution**: Run from Trigger.dev root directory:
```bash
cd /path/to/trigger.dev
./.railway/generate-consolidated-migration.sh
```

### Environment Variable Issues

#### Missing Required Variables
**Error**: Various services fail to start

**Required Variables**:
```bash
# Generate secrets
openssl rand -hex 16

# Set in Railway
railway variables --set SESSION_SECRET=<value>
railway variables --set MAGIC_LINK_SECRET=<value>
railway variables --set ENCRYPTION_KEY=<value>
railway variables --set MANAGED_WORKER_SECRET=<value>

# Set explicit port for Remix
railway variables --set PORT=3030
```

#### railway.json Not Applying
**Problem**: Variables in railway.json not being used

**Solution**: Variables must exist before railway.json can reference them:
```bash
# First: Create variables
railway variables --set KEY=value

# Then: Deploy with railway.json
railway up --detach  # Uses railway.json
```

**Note**: `railway redeploy` does NOT apply railway.json changes.

### Database Connection Issues

#### Railway PostgreSQL Access
**Getting connection details**:
```bash
# View in Railway dashboard
railway service Postgres

# Look for "Connect to your service over TCP"
# Example: tramway.proxy.rlwy.net:32581
```

#### Redis Connection Errors
**Error**: `getaddrinfo ENOTFOUND redis.railway.internal`

**Solution**: Already fixed in codebase with IPv6 support (`family: 0`). If persists:
```bash
# Verify Redis is running
railway service Redis
railway status

# Check Redis variables
railway variables | grep REDIS
```

### Docker Build Issues

#### Docker Cache Using Old Migration
**Problem**: Docker using cached layer with old migration name

**Solution**:
```bash
# Generate with new prefix to bust cache
./.railway/generate-consolidated-migration.sh --clean --prefix=v4_fresh

# Deploy with fresh build
railway up --detach
```

#### Migration Not Being Replaced
**Problem**: Consolidated migration added on top of existing 692 migrations

**Solution**: Ensure Dockerfile clears existing migrations:
```dockerfile
# CRITICAL: Must clear before copying
RUN rm -rf /triggerdotdev/internal-packages/database/prisma/migrations/*
COPY .railway/consolidated-migration/ /triggerdotdev/.../migrations/
```

### Deployment Issues

#### ClickHouse Validation Error
**Error**: `CLICKHOUSE_URL must be a valid URL`

**Solution**:
```bash
# Option 1: Disable (empty string)
railway variables --set CLICKHOUSE_URL=""

# Option 2: Use real instance
railway variables --set CLICKHOUSE_URL="https://user:pass@host:8443"
```

#### Missing Public Domain
**Problem**: No public URL for service

**Solution**:
```bash
railway domain  # Generates Railway-provided domain
```

#### Port Validation Error
**Error**: `PORT must be integer`

**Solution**:
```bash
railway variables --set PORT=3030  # Remix apps need explicit port
```

### Script Execution Issues

#### Portable Shell Compatibility
**Error**: `bad array subscript` or similar shell errors

**Solution**: Script already uses portable syntax:
```bash
# Instead of: ${array[-1]}
LATEST=$(printf '%s\n' "${array[@]}" | tail -1)
```

#### Permission Denied
**Error**: Cannot execute script

**Solution**:
```bash
chmod +x .railway/generate-consolidated-migration.sh
```

## Database Management

### Check Database State
```bash
# Connect to Railway PostgreSQL
PGPASSWORD="password" psql -h host.proxy.rlwy.net -p port -U postgres -d railway

# List all tables
\dt

# Check migrations
SELECT * FROM _prisma_migrations ORDER BY started_at DESC;

# Count tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
```

### Clean Database Reset
```bash
# WARNING: Destroys all data
DROP TABLE IF EXISTS ... CASCADE;  # All tables
DROP TYPE IF EXISTS ... CASCADE;   # All custom types

# Then redeploy
railway up --detach
```

## Performance Verification

### Check Migration Time
```bash
# View deployment logs
railway logs

# Look for migration timing
# Should see: "Running prisma migrations" 
# Followed by quick completion (~30s)
```

### Verify Single Migration
```bash
# Connect to database
PGPASSWORD="..." psql -h ... -d railway

# Should show only 1 consolidated migration
SELECT COUNT(*) FROM _prisma_migrations;
```

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Migration conflicts | Reset database or clean failed records |
| Variable not working | Use `railway up`, not `railway redeploy` |
| Docker cache issues | Use `--clean --prefix=new_name` |
| Connection timeouts | Check service status with `railway status` |
| Build failures | Verify `.env.example` exists |

## Getting Help

1. Check deployment logs: `railway logs`
2. Verify service status: `railway status`
3. Review Railway dashboard for service health
4. Check Trigger.dev logs in deployed application
5. File issues at: https://github.com/nick0lay/trigger.dev/issues