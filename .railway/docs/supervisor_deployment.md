# Automated Supervisor Deployment with Ops Controller

This implementation provides **automated supervisor deployment** to DigitalOcean using a dedicated ops-controller service that monitors and maintains your Trigger.dev deployment.

## 🚀 Features

- **Continuous Monitoring**: Self-healing service that monitors deployment health
- **Smart Token Management**: Automatic extraction from Railway API with manual override
- **PostgreSQL Auto-Configuration**: Sets up logical replication for ClickHouse
- **Zero SSH Required**: Uses cloud-init for automatic DigitalOcean configuration
- **Auto-Disable**: Stops monitoring after successful deployment to save resources
- **Idempotent Operations**: Safe to run multiple times, handles configuration drift

## 📋 Prerequisites

1. Railway account with Trigger.dev project deployed
2. DigitalOcean account with API token
3. Railway API token with project access

## 🎯 Quick Start

### Step 1: Deploy Ops Controller

```bash
# 1. Navigate to ops-controller directory
cd .railway/ops-controller

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your tokens and configuration

# 3. Start ops controller
docker-compose up -d

# 4. Monitor logs
docker-compose logs -f
```

### Step 2: Required Environment Variables

```bash
# DigitalOcean Configuration
DIGITALOCEAN_TOKEN=dop_v1_your_token_here
SUPERVISOR_REGION=nyc1
SUPERVISOR_SIZE=s-2vcpu-2gb

# Railway Configuration
RAILWAY_API_TOKEN=your_railway_api_token
RAILWAY_PROJECT_ID=your_railway_project_id
RAILWAY_ENVIRONMENT_ID=your_railway_environment_id

# PostgreSQL Configuration
DATABASE_URL=postgresql://user:password@host:port/database
DB_SERVICE_NAME=Postgres

# Monitoring Configuration (Optional)
IS_ACTIVE=true
CHECK_INTERVAL=1
AUTO_DISABLE=false
HEALTHY_CYCLES_BEFORE_DISABLE=3

# Manual Token Override (Optional)
TRIGGER_WORKER_TOKEN=tr_wgt_your_token_here
```

## 🔧 Ops Controller Architecture

### Core Components

1. **Railway Client** (`railway_client.py`)
   - Extracts worker tokens from webapp logs
   - Gets environment variables from Railway API
   - Manages service restarts when needed

2. **PostgreSQL Configurator** (`postgres_configurator.py`)
   - Sets up logical replication (WAL level = logical)
   - Configures TaskRun table replica identity
   - Creates publication for ClickHouse replication

3. **DigitalOcean Manager** (`digitalocean_manager.py`)
   - Creates supervisor droplets via API
   - Configures cloud-init for automatic setup
   - Monitors supervisor health

4. **Main Controller** (`ops_controller.py`)
   - Orchestrates the entire deployment process
   - Provides continuous monitoring and self-healing
   - Manages state persistence and auto-disable

### Monitoring Behavior

**Active Monitoring** (`IS_ACTIVE=true`):
- Runs every `CHECK_INTERVAL` minutes
- Automatically configures PostgreSQL if needed
- Deploys supervisor if missing or unhealthy
- Self-heals configuration drift
- Logs all actions and status

**Auto-Disable Feature** (`AUTO_DISABLE=true`):
- Monitors deployment until fully healthy
- Counts consecutive healthy cycles
- Auto-disables after `HEALTHY_CYCLES_BEFORE_DISABLE` reached
- Saves DigitalOcean API calls and resources

## 🔄 Deployment Flow

1. **Configuration Extraction**
   - Extracts `TRIGGER_WORKER_TOKEN` from Railway webapp logs
   - Gets `MANAGED_WORKER_SECRET` and `API_ORIGIN` from Railway API
   - Caches configuration for future use

2. **PostgreSQL Configuration**
   - Checks current replication settings
   - Sets `wal_level = 'logical'` if needed
   - Configures `TaskRun` table with `REPLICA IDENTITY FULL`
   - Creates `task_runs_to_clickhouse_v1_publication`
   - Restarts PostgreSQL service via Railway API if required

3. **Supervisor Deployment**
   - Creates DigitalOcean droplet with cloud-init
   - Installs Docker and supervisor containers
   - Configures with extracted tokens
   - Monitors health endpoint (`/health`)

## 📁 File Structure

```
.railway/ops-controller/
├── ops_controller.py           # Main orchestrator with monitoring loop
├── railway_client.py           # Railway API integration
├── postgres_configurator.py    # PostgreSQL logical replication setup
├── digitalocean_manager.py     # DigitalOcean droplet management
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Service orchestration
├── .env.example               # Environment template
└── README.md                  # Detailed documentation
```

## 🛠️ Configuration Options

### Droplet Configuration

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `SUPERVISOR_SIZE` | Droplet size | `s-2vcpu-2gb` | `s-1vcpu-1gb`, `s-2vcpu-4gb`, `s-4vcpu-8gb` |
| `SUPERVISOR_REGION` | Droplet region | `nyc1` | `nyc1`, `sfo3`, `ams3`, `sgp1`, `lon1`, `fra1` |

### Monitoring Configuration

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `IS_ACTIVE` | Enable monitoring | `true` | `true`, `false` |
| `CHECK_INTERVAL` | Check frequency (minutes) | `1` | `1-60` |
| `AUTO_DISABLE` | Auto-disable after success | `false` | `true`, `false` |
| `HEALTHY_CYCLES_BEFORE_DISABLE` | Cycles before auto-disable | `3` | `1-100` |

### Token Management

**Priority System:**
1. **Manual Override** (`TRIGGER_WORKER_TOKEN` env var) - Highest priority
2. **Cached Token** (from previous extraction) - Medium priority
3. **Log Extraction** (from Railway webapp logs) - Fallback

**Note**: Railway logs expire after ~3 days. Use manual override if logs have expired.

## 📊 Monitoring & Health Checks

### Check Deployment Status

```bash
# View ops controller logs
docker-compose logs -f ops-controller

# Check specific cycle
docker-compose logs --tail=50 ops-controller

# Monitor supervisor health directly
curl http://<droplet_ip>:8020/health
```

### State Persistence

The controller maintains state in `/tmp/ops-controller-state.json`:
- Configuration cache (including extracted tokens)
- Deployment status
- Consecutive healthy cycle counter
- Auto-disable status

## 🔍 Troubleshooting

### Worker Token Issues

**Problem**: "Could not extract worker token"
**Solutions**:
1. Check if webapp has been deployed and started
2. Verify webapp logs contain token (pattern: `tr_wgt_*`)
3. Set `TRIGGER_WORKER_TOKEN` manually if logs expired
4. Restart webapp to generate fresh logs

### PostgreSQL Configuration Issues

**Problem**: PostgreSQL configuration fails
**Solutions**:
1. Verify `DATABASE_URL` has superuser privileges
2. Check if `DB_SERVICE_NAME` matches your PostgreSQL service name
3. Ensure webapp has run migrations (tables must exist)
4. Some managed PostgreSQL services don't allow `ALTER SYSTEM` commands

### Supervisor Health Issues

**Problem**: Supervisor health check fails
**Solutions**:
1. SSH to droplet: `ssh root@<droplet-ip>`
2. Check cloud-init logs: `tail -f /var/log/cloud-init-output.log`
3. Check Docker containers: `docker ps`
4. View supervisor logs: `docker logs trigger-supervisor-1`

### Service Name Detection

**Problem**: PostgreSQL service not found
**Solutions**:
- Controller tries these names automatically: `Postgres`, `postgres`, `PostgreSQL`, `Database`, `DB`
- Set `DB_SERVICE_NAME` to your actual service name
- Check Railway service list in project dashboard

## 🔐 Security Considerations

- **API Tokens**: Never commit tokens to version control
- **PostgreSQL**: Requires superuser privileges for replication setup
- **DigitalOcean**: Droplet has public IP - firewall rules configured automatically
- **Docker Socket**: Protected via docker-proxy with read-only access
- **Token Storage**: Cached tokens stored in persistent volume

## 🚀 Advanced Usage

### Scaling Supervisor

```bash
# Update droplet size
echo "SUPERVISOR_SIZE=s-4vcpu-8gb" >> .env
docker-compose restart

# Controller will detect change and deploy new droplet
```

### Changing Monitoring Frequency

```bash
# Check every 5 minutes instead of 1
echo "CHECK_INTERVAL=5" >> .env
docker-compose restart
```

### Temporarily Disabling Monitoring

```bash
# Disable monitoring (useful for maintenance)
echo "IS_ACTIVE=false" >> .env
docker-compose restart

# Re-enable monitoring
echo "IS_ACTIVE=true" >> .env
docker-compose restart
```

### Manual State Reset

```bash
# Clear cached state (forces fresh configuration extraction)
docker-compose down -v  # Removes volumes
docker-compose up -d
```

## 📝 Architecture Benefits

This ops-controller approach solves several challenges:

1. **Railway Platform Limitations**: Bypasses Railway's Docker-in-Docker restrictions
2. **Token Management**: Handles Railway log retention (3-day expiration)
3. **Self-Healing**: Automatically fixes configuration drift
4. **Resource Efficiency**: Auto-disable feature stops unnecessary monitoring
5. **Reliability**: Idempotent operations safe to run multiple times

## 🤝 Support

For issues or questions:
- Check ops-controller logs: `docker-compose logs -f`
- Review this documentation and the ops-controller README
- Verify environment variables are correctly set
- Test Railway API connectivity and permissions
- Check DigitalOcean API limits and billing

## 💡 Tips

- Use `AUTO_DISABLE=true` in production to save resources
- Monitor DigitalOcean billing for supervisor costs
- Consider geographic proximity when selecting regions
- Use larger droplet sizes for high-throughput workloads
- Keep Railway API tokens secure and rotate regularly
- Set `TRIGGER_WORKER_TOKEN` manually if you frequently redeploy