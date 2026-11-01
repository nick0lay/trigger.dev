# Railway Deployment for Trigger.dev

## 🚀 One-Click Deploy (Recommended)

**Deploy complete Trigger.dev stack in ~5 minutes:**

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/triggerdev?referralCode=CG2P3Y&utm_medium=integration&utm_source=template&utm_campaign=generic)

**Template URL**: https://railway.com/deploy/triggerdev?referralCode=CG2P3Y&utm_medium=integration&utm_source=template&utm_campaign=generic

The template's Railway packaging (webapp Dockerfile, registry image, template description) lives in [nick0lay/railway-templates](https://github.com/nick0lay/railway-templates/tree/main/solutions/trigger-dev). This fork builds the patched webapp image (`ghcr.io/nick0lay/trigger.dev-railway`) and the ops-controller image (`ghcr.io/nick0lay/trigger-ops-controller`).

**What you get**:
- ✅ Complete Trigger.dev v4 stack with all services
- ✅ PostgreSQL, Redis, ClickHouse, Railway Bucket, password-protected Docker registry
- ✅ IPv6 DNS support and auto-generated secrets
- ✅ Production-ready configuration

## 🛠️ Manual Deployment

Deploy Trigger.dev v4.0.0 manually to Railway in 3 steps:

```bash
# 1. Generate consolidated migration (once)
./.railway/generate-consolidated-migration.sh --prefix=release_v4

# 2. Deploy to Railway
railway up --detach

# 3. Monitor deployment (35-40 seconds total)
railway logs
```

## ⚡ Performance

**45x faster deployments** using consolidated migrations:
- **Before**: 692 individual migrations (~25 minutes)
- **After**: 1 consolidated migration (~35 seconds)

## 🏗️ Architecture

### Docker-Based Deployment
- Uses custom Railway-optimized image: `ghcr.io/nick0lay/trigger.dev-railway:v4.0.0`
- Includes IPv6 support for Redis connections
- Fixes ClickHouse HTTP/HTTPS handling
- Replaces 692 migrations with 1 consolidated migration
- Zero runtime complexity - original entrypoint unchanged

#### Available Docker Images
Pre-built Railway-optimized containers available at:
**https://github.com/nick0lay/trigger.dev/pkgs/container/trigger.dev-railway**

**Available tags:**
- `latest` - Latest stable Railway build
- `v4.0.0` - Specific version with Railway optimizations
- `main` - Latest main branch build

**Features included in Railway images:**
- ✅ IPv6 DNS support for Redis connectivity
- ✅ Consolidated migrations (45x faster deployments) 
- ✅ ClickHouse HTTP/HTTPS protocol fixes
- ✅ Railway-specific environment variable handling
- ✅ Production-ready configuration

### Key Components
- **`Dockerfile.simple`** - Minimal Docker configuration
- **`generate-consolidated-migration.sh`** - Universal migration consolidator
- **`consolidated-migration/`** - Generated migration files

## 📚 Documentation

- [**Migration Guide**](docs/migration-guide.md) - How consolidated migrations work
- [**Docker Image Workflow**](docs/docker-image-workflow.md) - Custom Docker builds with IPv6 fixes
- [**Data Replication Setup**](docs/DATA_REPLICATION.md) - **CRITICAL**: Why runs may not appear in UI and how to fix
- [**Troubleshooting**](docs/troubleshooting.md) - Common issues and solutions
- [**Railway Template**](docs/railway-template.md) - Publishing to Railway templates

## ⚠️ Important Post-Deployment Steps

### Runs Not Appearing in UI?
If your tasks execute successfully but don't appear in the `/orgs/.../runs` page:

See [Data Replication Setup](docs/DATA_REPLICATION.md) for complete configuration guide.

## 🔧 Common Operations

### Generate Fresh Migration
```bash
# For development
./.railway/generate-consolidated-migration.sh

# For production release
./.railway/generate-consolidated-migration.sh --prefix=release_v4

# Clean regenerate
./.railway/generate-consolidated-migration.sh --clean
```

### Database Management
```bash
# Connect to Railway PostgreSQL
PGPASSWORD="your-password" psql -h your-host.proxy.rlwy.net -p port -U postgres -d railway

# Check migration status
SELECT migration_name, finished_at FROM _prisma_migrations ORDER BY started_at DESC LIMIT 5;
```

### Deployment Commands
```bash
# Deploy with railway.json config
railway up --detach

# Check status
railway status

# View logs
railway logs

# Redeploy existing deployment
railway redeploy
```

## 🎯 Requirements

- Railway CLI installed
- Railway project linked
- PostgreSQL and Redis services created in Railway
- Environment variables configured (see [troubleshooting](docs/troubleshooting.md))

## 📊 Migration Consolidation

The universal migration script:
- **Idempotent** - Safe to run multiple times
- **Automatic** - Detects new migrations since last baseline
- **Flexible** - Supports development and release prefixes
- **Fast** - Generates in ~5 seconds

## 🚨 Important Notes

1. **Fresh Database Required**: Consolidated migrations work best with clean databases
2. **Docker Cache**: Use `--clean` flag to bust Docker cache if needed
3. **Environment Variables**: Must be set before `railway up` (see docs)

## 🔗 Related Resources

- [Railway Template](https://railway.com/deploy/triggerdev?referralCode=CG2P3Y&utm_medium=integration&utm_source=template&utm_campaign=generic) - One-click deployment
- [Railway packaging](https://github.com/nick0lay/railway-templates/tree/main/solutions/trigger-dev) - Template source in nick0lay/railway-templates
- [Trigger.dev Documentation](https://trigger.dev/docs) - Official docs
- [Railway Documentation](https://docs.railway.app) - Platform docs
- [Original Repository](https://github.com/triggerdotdev/trigger.dev) - Upstream source