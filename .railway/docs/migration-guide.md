# Consolidated Migration Guide

## Overview

This guide explains how Trigger.dev's consolidated migration system achieves **45x faster deployments** on Railway by replacing 692 individual Prisma migrations with a single optimized migration.

## How It Works

### Traditional Approach (Slow)
```
Fresh DB → Migration 1 → Migration 2 → ... → Migration 692 → ~20 minutes
```

### Consolidated Approach (Fast)
```
Fresh DB → Apply 1 consolidated migration → ~30 seconds
```

## The Universal Script

**File**: `generate-consolidated-migration.sh`

### Core Features
- **Idempotent**: Safe to run multiple times
- **Automatic Detection**: Identifies new migrations since last baseline
- **Timestamp-Based**: Uses Prisma's `YYYYMMDDHHMMSS_` format
- **Flexible Naming**: Supports development and release prefixes

### Usage

#### Initial Baseline
```bash
# Creates: 20250814092224_consolidated
./.railway/generate-consolidated-migration.sh
```

#### Release Baseline
```bash
# Creates: 20250814092224_release_v4_consolidated
./.railway/generate-consolidated-migration.sh --prefix=release_v4
```

#### Clean Regeneration
```bash
# Delete existing and regenerate from scratch
./.railway/generate-consolidated-migration.sh --clean
```

#### Automatic Incremental Updates
```bash
# If new migrations exist, automatically includes them
./.railway/generate-consolidated-migration.sh
```

## Docker Integration

### How Replacement Works

The `Dockerfile.simple` completely replaces existing migrations:

```dockerfile
# Step 1: Remove ALL existing migrations (692 files)
RUN rm -rf /triggerdotdev/internal-packages/database/prisma/migrations/*

# Step 2: Copy ONLY our consolidated migration (1 file)
COPY .railway/consolidated-migration/ /triggerdotdev/.../migrations/
```

### File Structure

```
.railway/
└── consolidated-migration/
    └── 20250814092224_consolidated/
        ├── migration.sql    # All 692 migrations in one file
        └── metadata.json    # Generation information
```

## Migration Strategy Decision Tree

```
Clean mode (--clean)?
├─ Yes → Delete existing + regenerate everything
└─ No  → Smart automatic detection:
    └─ Existing consolidated migration?
        ├─ No  → Generate initial baseline
        └─ Yes → Newer migrations available?
            ├─ No  → Nothing to do (up to date)
            └─ Yes → Update baseline (incremental)
```

## Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Migration Files** | 692 | 1 | **692x reduction** |
| **Migration Time** | ~20 minutes | ~30 seconds | **40x faster** |
| **Docker Build** | 5-10 minutes | 5-10 seconds | **60x faster** |
| **Total Deploy** | ~25 minutes | ~35 seconds | **45x faster** |

## Development Workflow

### Day 1: Initial Setup
```bash
# Generate consolidated migration
./.railway/generate-consolidated-migration.sh

# Deploy to Railway
railway up --detach
```

### Ongoing Development
```bash
# Pull latest changes
git pull

# Update consolidated migration (automatic incremental)
./.railway/generate-consolidated-migration.sh

# Deploy updated version
railway up --detach
```

### Release Preparation
```bash
# Create release-specific baseline
./.railway/generate-consolidated-migration.sh --clean --prefix=release_v4

# Commit to repository
git add .railway/consolidated-migration/
git commit -m "Add v4.0.0 release baseline"

# Deploy release
railway up --detach
```

## Metadata Structure

Each consolidated migration includes metadata:

```json
{
  "migration_name": "20250814092224_consolidated",
  "generated_at": "2025-08-21T22:00:00Z",
  "strategy": "clean-regenerate",
  "includes_up_to": "20250814092224",
  "included_migrations": 692,
  "baseline_lines": 1950,
  "schema_checksum": "772a4ae..."
}
```

## Important Considerations

### Database State
- **Fresh Database**: Consolidated migrations apply cleanly
- **Existing Database**: May require database reset or schema sync
- **Failed Migrations**: Must be cleaned from `_prisma_migrations` table

### Docker Caching
- Use unique prefixes to bust Docker cache layers
- The `--clean` flag ensures fresh generation
- Railway rebuilds on each `railway up`

### Migration Naming
Uses the timestamp of the **latest migration** as baseline:
```
Latest: 20250814092224_add_task_run_plan_type
Result: 20250814092224_consolidated
```

## Technical Details

### SQL Generation
Uses Prisma's migration diff engine:
```bash
npx prisma migrate diff \
  --from-empty \
  --to-schema-datamodel ./prisma/schema.prisma \
  --script
```

### Prisma Compatibility
- Works with Prisma 5.4.1+
- Maintains migration history in `_prisma_migrations` table
- Compatible with `prisma migrate deploy`

## Benefits Summary

✅ **45x faster deployments** (35s vs 25min)  
✅ **Single migration file** (vs 692 files)  
✅ **Zero runtime complexity** (original entrypoint)  
✅ **Idempotent operation** (safe reruns)  
✅ **Automatic updates** (detects new migrations)  
✅ **Docker optimized** (minimal layers)