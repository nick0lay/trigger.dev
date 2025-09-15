# Environment Variables for Ops Controller

This document describes all environment variables used by the Trigger.dev Ops Controller for automated supervisor deployment.

## DigitalOcean Configuration

DIGITALOCEAN_TOKEN="dop_v1_8ca..." # DigitalOcean API token for creating and managing droplets. Get from https://cloud.digitalocean.com/account/api/tokens
SUPERVISOR_REGION="nyc1" # DigitalOcean region where supervisor droplet will be created. Available: nyc1, nyc3, sfo3, ams3, sgp1, lon1, fra1, tor1, blr1
SUPERVISOR_SIZE="s-1vcpu-1gb" # DigitalOcean droplet size for supervisor. Options: s-1vcpu-1gb, s-2vcpu-2gb, s-2vcpu-4gb, s-4vcpu-8gb

## Railway Integration

RAILWAY_API_TOKEN="47aea0a9-435e-4f21-8f88-a56d63ff2392" # Railway API token for managing services and extracting configuration. Get from Railway account settings
RAILWAY_PROJECT_ID="${{RAILWAY_PROJECT_ID}}" # Railway project ID, automatically provided by Railway platform
RAILWAY_ENVIRONMENT_ID="${{RAILWAY_ENVIRONMENT_ID}}" # Railway environment ID, automatically provided by Railway platform

## PostgreSQL Database

DATABASE_URL="${{Postgres.DATABASE_URL}}" # PostgreSQL connection string from Railway Postgres service. Used for logical replication configuration
DB_SERVICE_NAME="Postgres" # Name of PostgreSQL service in Railway project. Change if your service has different name

## Railway Service Names

WEBAPP_SERVICE_NAME="trigger.dev" # Name of webapp service in Railway project. Used for token extraction and API configuration

## Monitoring Configuration

IS_ACTIVE="true" # Enable/disable continuous monitoring. Set to "false" to pause monitoring without stopping container
CHECK_INTERVAL="1" # Monitoring frequency in minutes (1-60). How often to check supervisor health and configuration
AUTO_DISABLE="false" # Automatically disable monitoring after successful deployment to save resources
HEALTHY_CYCLES_BEFORE_DISABLE="3" # Number of consecutive healthy cycles before auto-disable triggers

## Trigger.dev Configuration

TRIGGER_VERSION="v4.0.0" # Version of Trigger.dev to deploy on supervisor. Should match your webapp version
TRIGGER_WORKER_TOKEN="tr_wgt_..." # Manual worker token override. Leave empty to extract from webapp logs automatically

## Docker Registry (Optional)

DOCKER_REGISTRY_URL="${{registry.RAILWAY_PUBLIC_DOMAIN}}" # Docker registry domain for supervisor images. Optional if using default Docker Hub

## Operational Settings (Advanced)

MAX_RETRIES="3" # Maximum retry attempts for failed operations
RETRY_DELAY="5" # Delay in seconds between retry attempts
LOG_SCAN_LINES="1000" # Number of log lines to scan when extracting worker token
DROPLET_WAIT_TIMEOUT="300" # Maximum time to wait for droplet creation (in seconds)

## Usage Examples

### Basic Configuration (Minimum Required)
```bash
DIGITALOCEAN_TOKEN="dop_v1_your_token_here"
RAILWAY_API_TOKEN="your_railway_api_token"
DATABASE_URL="${{Postgres.DATABASE_URL}}"
```

### Production Configuration with Auto-Disable
```bash
DIGITALOCEAN_TOKEN="dop_v1_your_token_here"
SUPERVISOR_REGION="nyc1"
SUPERVISOR_SIZE="s-2vcpu-2gb"
RAILWAY_API_TOKEN="your_railway_api_token"
DATABASE_URL="${{Postgres.DATABASE_URL}}"
DB_SERVICE_NAME="Postgres"
WEBAPP_SERVICE_NAME="trigger.dev"
IS_ACTIVE="true"
CHECK_INTERVAL="5"
AUTO_DISABLE="true"
HEALTHY_CYCLES_BEFORE_DISABLE="3"
TRIGGER_VERSION="v4.0.0"
```

### Custom Service Names
```bash
# If your Railway services have custom names
DB_SERVICE_NAME="MyPostgresDB"
WEBAPP_SERVICE_NAME="my-webapp-service"
```

## Security Notes

- **DIGITALOCEAN_TOKEN**: Keep this secret, it provides full access to your DigitalOcean account
- **RAILWAY_API_TOKEN**: Keep this secret, it provides access to your Railway project
- **DATABASE_URL**: Contains database credentials, handle securely
- **TRIGGER_WORKER_TOKEN**: Authentication token for supervisor, generated automatically if not provided

## Troubleshooting

### Missing Worker Token
If ops-controller cannot extract worker token from logs:
1. Check if webapp service name is correct (`WEBAPP_SERVICE_NAME`)
2. Ensure webapp has been deployed and started recently (logs expire after ~3 days)
3. Set `TRIGGER_WORKER_TOKEN` manually as fallback

### Service Not Found Errors
If ops-controller reports service not found:
1. Verify service names match your Railway project exactly
2. Check `DB_SERVICE_NAME` and `WEBAPP_SERVICE_NAME` settings
3. Use Railway dashboard to confirm exact service names

### Supervisor Health Issues
If supervisor deployment fails or becomes unhealthy:
1. Check DigitalOcean droplet in console
2. Verify `SUPERVISOR_REGION` and `SUPERVISOR_SIZE` are valid
3. Ensure DigitalOcean API token has sufficient permissions