# Ops Controller for Trigger.dev

Automated deployment and configuration tool for Trigger.dev supervisor on DigitalOcean.

## 🎯 Overview

The Ops Controller is a **continuous monitoring service** that automatically maintains your Trigger.dev deployment. It runs in the background, checking and fixing issues as they arise, providing a truly "deploy and forget" experience.

**What it does:**
1. **Continuous Monitoring**: Runs every 1-60 minutes (configurable)
2. **Self-Healing**: Automatically detects and fixes configuration drift
3. **Configuration Extraction**: Extracts worker tokens and config from Railway
4. **PostgreSQL Management**: Maintains logical replication configuration
5. **Supervisor Health**: Monitors and redeploys supervisor as needed

## 🚀 Quick Start

### Prerequisites

- DigitalOcean account with API token
- Railway project with Trigger.dev webapp deployed
- PostgreSQL database with superuser access (for replication setup)

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# DigitalOcean
DIGITALOCEAN_TOKEN=dop_v1_your_token_here
SUPERVISOR_REGION=nyc1
SUPERVISOR_SIZE=s-2vcpu-2gb

# Railway
RAILWAY_API_TOKEN=your_railway_api_token
RAILWAY_PROJECT_ID=your_railway_project_id
# Note: Railway provides RAILWAY_ENVIRONMENT_ID, not RAILWAY_ENVIRONMENT
# This is automatically available in Railway deployments
RAILWAY_ENVIRONMENT_ID=your_railway_environment_id

# PostgreSQL
DATABASE_URL=postgresql://user:password@host:port/database
# Name of PostgreSQL service in Railway (default: "Postgres")
DB_SERVICE_NAME=Postgres

# Monitoring Configuration
# Enable/disable continuous monitoring (default: true)
IS_ACTIVE=true
# Check interval in minutes (1-60, default: 1)
CHECK_INTERVAL=1
# Auto-disable after successful deployment (default: false)
AUTO_DISABLE=false
# Number of healthy cycles before auto-disable (default: 3)
HEALTHY_CYCLES_BEFORE_DISABLE=3

# Trigger.dev Configuration
TRIGGER_VERSION=v4.0.0
# Manual worker token (optional - leave empty to extract from logs)
TRIGGER_WORKER_TOKEN=
```

> **Note**: Railway automatically provides `RAILWAY_ENVIRONMENT_ID` as an environment variable in your deployments. This is different from the environment name (e.g., "production"). The controller uses this ID to uniquely identify your Railway environment.

### Running with Docker

```bash
# Build the image
docker build -t trigger-ops-controller .

# Run continuous monitoring
docker run --env-file .env trigger-ops-controller

# Run with custom interval (every 5 minutes)
docker run --env-file .env -e CHECK_INTERVAL=5 trigger-ops-controller

# Run in disabled mode (for testing)
docker run --env-file .env -e IS_ACTIVE=false trigger-ops-controller
```

### Running with Docker Compose

```bash
# Run continuous monitoring service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run continuous monitoring
python ops_controller.py

# Run with custom settings via environment
IS_ACTIVE=true CHECK_INTERVAL=5 python ops_controller.py
```

## ⚙️ Monitoring Configuration

### Environment Variables

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `IS_ACTIVE` | Enable/disable monitoring | `true` | `true`, `false` |
| `CHECK_INTERVAL` | Check frequency in minutes | `1` | `1-60` |
| `AUTO_DISABLE` | Auto-disable after success | `false` | `true`, `false` |
| `HEALTHY_CYCLES_BEFORE_DISABLE` | Cycles before auto-disable | `3` | `1-100` |
| `DB_SERVICE_NAME` | PostgreSQL service name | `Postgres` | Any string |
| `TRIGGER_WORKER_TOKEN` | Manual token override | (empty) | `tr_wgt_*` format |

### Monitoring Behavior

**When `IS_ACTIVE=true` (default)**:
- Monitors every `CHECK_INTERVAL` minutes
- Automatically configures PostgreSQL logical replication if needed
- Deploys supervisor to DigitalOcean if missing
- Performs health checks on supervisor
- Self-heals configuration drift
- Logs all actions and status

**When `IS_ACTIVE=false`**:
- Service runs but monitoring is disabled
- Logs "Monitoring disabled" message
- Sleeps indefinitely (useful for debugging)

## 🔑 Worker Token Management

### Token Priority System

The ops-controller uses a smart priority system for obtaining the worker token:

1. **Manual Override** (highest priority)
   - Set `TRIGGER_WORKER_TOKEN` environment variable
   - Useful when logs have expired or for custom tokens

2. **Cached Token** (from previous extraction)
   - Stored in state file (`/tmp/ops-controller-state.json`)
   - Survives container restarts (if volume persisted)

3. **Log Extraction** (fallback)
   - Searches Railway webapp logs for `tr_wgt_*` pattern
   - Only works if logs haven't expired (~3 days retention)

### Handling Log Expiration

Railway logs expire after approximately 3 days. After expiration:

**Option 1: Manual Token**
```bash
# Extract token manually from webapp UI or logs
TRIGGER_WORKER_TOKEN=tr_wgt_abc123xyz789 docker-compose up -d
```

**Option 2: Restart Webapp**
```bash
# Restart webapp to generate fresh logs with token
railway redeploy webapp
# Then restart ops-controller
docker-compose restart
```

## 🤖 Auto-Disable Feature

### Purpose

Once everything is deployed and healthy, continuous monitoring wastes resources and API calls. Auto-disable stops monitoring after successful deployment.

### Configuration

```bash
# Enable auto-disable after 3 healthy cycles
AUTO_DISABLE=true
HEALTHY_CYCLES_BEFORE_DISABLE=3
```

### How It Works

1. **Monitors deployment** until everything is healthy
2. **Counts consecutive healthy cycles** (default: 3)
3. **Auto-disables monitoring** after threshold reached
4. **Logs success** and enters idle mode
5. **Saves resources** by stopping unnecessary checks

### Re-enabling After Auto-Disable

```bash
# Option 1: Restart with IS_ACTIVE=true
IS_ACTIVE=true docker-compose restart

# Option 2: Delete state file and restart
rm /tmp/ops-controller-state.json
docker-compose restart
```

## 🔍 Getting Railway Environment ID

If running locally, you can find your Railway Environment ID in several ways:

1. **From Railway Dashboard**:
   - Go to your project settings
   - The environment ID is in the URL: `railway.app/project/[project-id]/environment/[environment-id]`

2. **From Railway CLI**:
   ```bash
   railway environment
   ```

3. **From within Railway deployment**:
   - The `RAILWAY_ENVIRONMENT_ID` is automatically available as an environment variable

## 🗄️ PostgreSQL Service Configuration

### Service Name Configuration

The ops-controller needs to know your PostgreSQL service name to restart it when configuring logical replication. By default, it expects a service named "Postgres" (matching most Railway templates).

**Environment Variable:**
```bash
DB_SERVICE_NAME=Postgres  # Default value
```

**Common PostgreSQL Service Names:**
- `Postgres` (Railway template default)
- `PostgreSQL` (Full name variant)
- `Database` (Generic naming)
- `DB` (Short naming)

### Smart Detection

If the configured service name isn't found, the controller automatically tries these common names:
1. Your configured `DB_SERVICE_NAME`
2. "Postgres"
3. "postgres" (lowercase)
4. "PostgreSQL"
5. "Database"
6. "DB"

### Configuration Examples

**Default (works with most Railway templates):**
```bash
DB_SERVICE_NAME=Postgres
```

**Custom service names:**
```bash
DB_SERVICE_NAME=my-postgres-db
DB_SERVICE_NAME=production-database
DB_SERVICE_NAME=PostgreSQL
```

## 🔧 How It Works

### Continuous Monitoring Loop

The ops-controller runs a continuous loop that:

1. **⏰ Wakes up** every `CHECK_INTERVAL` minutes
2. **🔍 Checks** current state vs desired state
3. **🔧 Fixes** any issues automatically
4. **📊 Logs** actions taken
5. **😴 Sleeps** until next check

### What Gets Monitored

#### 1. Configuration Extraction
- **Checks**: If worker tokens and config are cached
- **Action**: Extract from Railway API if missing
  - Searches webapp logs for worker token (pattern: `tr_wgt_*`)
  - Gets `MANAGED_WORKER_SECRET` from webapp environment
  - Gets `API_ORIGIN` from webapp for API URL
  - Gets registry URL from registry service

#### 2. PostgreSQL Logical Replication
- **Checks**: Current replication configuration
- **Action**: Configure if not set up properly
  ```sql
  -- Sets WAL level to logical
  ALTER SYSTEM SET wal_level = 'logical';

  -- Sets replica identity for TaskRun table
  ALTER TABLE public."TaskRun" REPLICA IDENTITY FULL;

  -- Creates publication for replication
  CREATE PUBLICATION task_runs_to_clickhouse_v1_publication
  FOR TABLE public."TaskRun";
  ```
- **Auto-restart**: Restarts PostgreSQL via Railway API if needed

#### 3. Supervisor Deployment & Health
- **Checks**: If supervisor droplet exists and is healthy
- **Action**: Deploy new droplet if missing or unhealthy
  - Creates DigitalOcean droplet with cloud-init
  - Installs Docker and supervisor containers
  - Configures with extracted tokens
  - Monitors health endpoint (`/health`)

### Self-Healing Capabilities

The controller automatically fixes:
- **Missing configuration**: Re-extracts from Railway
- **PostgreSQL drift**: Reconfigures replication settings
- **Unhealthy supervisor**: Redeploys droplet
- **Network issues**: Retries with exponential backoff

## 🔍 Deployment Details

### Droplet Configuration

- **Default Size**: `s-2vcpu-2gb` ($24/month)
- **Image**: Ubuntu 20.04 with Docker
- **Region**: Configurable (default: `nyc1`)
- **Tags**: Automatically tagged for identification

### Services Deployed

1. **Supervisor**: Manages task execution
   - Port: 8020
   - Health endpoint: `/health`

2. **Docker Proxy**: Secure Docker socket access
   - Internal port: 2375
   - Read-only socket mount

### Idempotency

The controller is idempotent and checks:
- PostgreSQL replication status before configuring
- Existing droplets by tag before creating new ones
- Service health after deployment

## 🐳 Docker Hub Deployment

To publish the controller image:

```bash
# Build for multiple platforms
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t yourusername/trigger-ops-controller:latest \
  --push .

# Run from Docker Hub (continuous monitoring)
docker run --env-file .env \
  yourusername/trigger-ops-controller:latest
```

## 🔒 Security Considerations

- **API Tokens**: Never commit tokens to version control
- **PostgreSQL**: Requires sufficient privileges for replication setup
- **DigitalOcean**: Droplet has public IP - ensure firewall rules are proper
- **Docker Socket**: Protected via docker-proxy with read-only access

## 📊 Monitoring and Logs

### Monitoring Dashboard

The controller logs comprehensive status information:

```bash
# View live logs
docker-compose logs -f ops-controller

# Check specific service logs
docker logs -f <container-id>
```

### Log Output Examples

```
✅ Starting continuous monitoring (interval: 1 minutes)
🔍 === Starting monitoring cycle ===
✅ PostgreSQL replication: ✅ Configured
✅ Supervisor health: ✅ Healthy at 142.93.153.45:8020
✅ === Monitoring cycle completed ===
ℹ️ Cycle completed in 2.3s, sleeping for 57.7s
```

### Supervisor Health Check

Monitor supervisor directly:
```bash
curl http://<droplet-ip>:8020/health
```

### State Persistence

The controller saves state to `/tmp/ops-controller-state.json`:
- Configuration cache
- Deployment status
- Last successful check timestamps

## 🚨 Troubleshooting

### Worker Token Not Found

If the controller can't find the worker token:
1. Ensure webapp has been deployed and started
2. Check webapp logs contain a token (format: `tr_wgt_*`)
3. Manually create a worker group in the webapp UI

### PostgreSQL Configuration Fails

If PostgreSQL configuration fails:
1. **Service Name Issues**:
   - Check if your PostgreSQL service name matches `DB_SERVICE_NAME`
   - Controller will list all available services when PostgreSQL service not found
   - Try setting `DB_SERVICE_NAME` to your actual service name

2. **Database Privileges**:
   - Verify `DATABASE_URL` has sufficient privileges (superuser recommended)
   - Ensure connection string is correct and accessible

3. **WAL Level Configuration**:
   - For managed databases, WAL level may need manual configuration
   - Some managed PostgreSQL services don't allow `ALTER SYSTEM` commands

4. **Table Prerequisites**:
   - Check if tables exist before setting replica identity
   - Ensure webapp has run migrations to create required tables

### Supervisor Not Healthy

If supervisor health check fails:
1. SSH to droplet: `ssh root@<droplet-ip>`
2. Check cloud-init logs: `tail -f /var/log/cloud-init-output.log`
3. Check Docker containers: `docker ps`
4. View supervisor logs: `docker logs trigger-supervisor-1`

## 🔄 Updates and Maintenance

### Updating Trigger.dev Version

Update the environment variable and restart the service:
```bash
# Update environment
echo "TRIGGER_VERSION=v4.1.0" >> .env

# Restart service to pick up new version
docker-compose restart
```

### Scaling the Supervisor

To use a larger droplet, update the environment and restart:
```bash
# Update droplet size
echo "SUPERVISOR_SIZE=s-4vcpu-8gb" >> .env

# Restart monitoring - it will deploy new droplet automatically
docker-compose restart
```

The monitoring service will detect the configuration change and deploy a new droplet with the larger size.

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

## 📝 Architecture Notes

This controller implements the hybrid deployment model:
- **Railway**: Hosts webapp with managed PostgreSQL and Redis
- **DigitalOcean**: Hosts supervisor with Docker access for task execution

This architecture solves Railway's Docker-in-Docker limitation while leveraging Railway's excellent managed services.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This tool is part of the Trigger.dev deployment utilities.