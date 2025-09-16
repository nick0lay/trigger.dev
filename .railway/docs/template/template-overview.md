# Deploy and Host Trigger.dev on Railway (Webapp) + DigitalOcean (Supervisor)

Trigger.dev is an open-source platform that lets developers reliably run long-duration background jobs—like AI workflows and data processing—directly in their codebase, without timeouts, manual scaling, or complex setup.

## About This Dual-Platform Deployment

This template deploys Trigger.dev across two platforms: **Railway hosts the webapp** (orchestration, API, dashboard) while **DigitalOcean runs the supervisor** (task execution in Docker containers). This architecture is required because Railway doesn't provide Docker socket access needed for task execution, while DigitalOcean droplets have full Docker capabilities.

The included **ops-controller automates the entire deployment process**—requiring only your DigitalOcean API token alongside Railway's auto-provided credentials. After one-click deployment, the system automatically provisions a DigitalOcean droplet, configures task execution, and maintains the supervisor without manual intervention.

## Common Use Cases

- **AI workflow orchestration** - LLM pipelines, model inference, and AI agent automation without timeouts
- **Video and audio processing** - Long-running media processing tasks that exceed typical serverless limits
- **Data import and ETL** - Batch processing, data transformation, and migration jobs with progress tracking
- **Document generation** - Automated PDF creation, report generation, and file processing workflows
- **Webhook automation** - Event-driven workflows and third-party service integrations with retry logic
- **Scheduled task execution** - Cron-like scheduling with robust error handling and real-time monitoring
- **API workflow orchestration** - Chain multiple API calls with proper error handling and state management

## Architecture: Railway + DigitalOcean

**Why Two Platforms?**
Trigger.dev v4 requires a supervisor service to execute tasks in Docker containers. Railway's platform restrictions prevent Docker socket access (`/var/run/docker.sock`), making task execution impossible. DigitalOcean droplets provide the full Docker capabilities needed for the supervisor.

**How It Works:**
1. **Railway Services**: Webapp, PostgreSQL, Redis, ClickHouse, MinIO, Docker registry
2. **DigitalOcean Service**: Supervisor droplet for task execution
3. **ops-controller**: Automates cross-platform deployment and monitoring
4. **One-Click Setup**: Deploy button requires only your DigitalOcean API token

## Dependencies for Trigger.dev Hosting

- **PostgreSQL database** - Job storage, state management, and task persistence (provided by Railway)
- **Redis instance** - Queue management, real-time features, and caching (provided by Railway with IPv6 support)
- **ClickHouse database** - Analytics database for advanced metrics and observability (provided by Railway)
- **MinIO object storage** - S3-compatible storage for large payloads and file processing (provided by Railway)
- **Docker registry** - Private registry for task deployment and container management (provided by Railway)
- **Node.js/TypeScript runtime** - Core execution environment for webapp and task processing
- **Environment variables** - Auto-configured via Railway template with secure secret generation

### Deployment Dependencies

- **Trigger.dev v4.0.0** - [Latest stable release](https://github.com/triggerdotdev/trigger.dev/releases/tag/trigger.dev%404.0.0)
- **Railway account** - [Sign up at railway.app](https://railway.app)
- **DigitalOcean account** - [Sign up at digitalocean.com](https://digitalocean.com) and [generate API token](https://cloud.digitalocean.com/account/api/tokens)
- **ops-controller** - Automated deployment service (included in template)
- **Documentation** - [Official Trigger.dev docs](https://trigger.dev/docs)

### Optional Services

- **Electric Sync Engine** - [Deploy separately](https://railway.com/deploy/electricsql-1) for real-time PostgreSQL synchronization
- **External ClickHouse** - Replace built-in ClickHouse with cloud provider, manage with [CH-UI](https://ch-ui.com/)
- **External Object Storage** - Replace built-in MinIO with AWS S3, Google Cloud Storage, or other providers

### Implementation Details

**What's Included:**
- ✅ **Railway Services**: Trigger.dev webapp, PostgreSQL, Redis, ClickHouse, MinIO, Docker registry
- ✅ **DigitalOcean Supervisor**: Automated droplet deployment for task execution
- ✅ **ops-controller**: Cross-platform automation with health monitoring and auto-scaling
- ✅ **One-Click Setup**: Deploy with just DigitalOcean API token, everything else auto-configured
- ✅ Optimized migrations (~1 minute vs 20+ minutes)
- ✅ IPv6 DNS support for Railway internal networking
- ✅ Auto-generated secure secrets (SESSION_SECRET, ENCRYPTION_KEY, etc.)
- ✅ Vertical auto-scaling and health monitoring
- ✅ SSL certificates and secure environment setup

**Key v4.0.0 Features:**
- Machine presets - Scale tasks with `micro`, `small-1x`, `large-2x` resource configurations
- Real-time streaming - Send live progress updates to your frontend
- Enhanced retry logic - Configurable backoff strategies and error handling
- TypeScript-first - Full type safety throughout task definitions
- Polyglot support - Write tasks in both Node.js/TypeScript and Python

## Email Configuration (Optional)

**Default Behavior**: Without email configuration, Trigger.dev logs magic links and invitations to the console instead of sending emails. Check Railway deployment logs to find invitation URLs.

**Why Configure Email**: Enable automatic magic link authentication and user invitation emails for a seamless user experience.

### Option 1: Resend (Recommended) 

**Best for**: Quick setup, excellent deliverability, modern API
**Free tier**: 3,000 emails/month
**Setup time**: ~2 minutes

Add these environment variables to Railway:
```yaml
EMAIL_TRANSPORT=resend
FROM_EMAIL=onboarding@resend.dev    # Use their test domain instantly
REPLY_TO_EMAIL=support@yourdomain.com
RESEND_API_KEY=re_xxxxxxxxxx        # Get from resend.com dashboard
```

**Setup steps**:
1. Sign up at [resend.com](https://resend.com) (free)
2. Copy API key from dashboard  
3. Add environment variables to Railway service
4. Magic links and invitations now send via email! ✅

### Option 2: SMTP (Standard Email Server)

**Best for**: Using existing email infrastructure, Gmail/Outlook integration
**Setup time**: ~10 minutes

```yaml
EMAIL_TRANSPORT=smtp
FROM_EMAIL=noreply@yourdomain.com
REPLY_TO_EMAIL=support@yourdomain.com
SMTP_HOST=smtp.gmail.com          # Your SMTP server
SMTP_PORT=587                     # Usually 587 for TLS, 465 for SSL
SMTP_SECURE=false                 # true for SSL, false for TLS
SMTP_USER=your-email@gmail.com    # SMTP username
SMTP_PASSWORD=your-app-password   # SMTP password or app password
```

**Popular SMTP servers**:
- Gmail: `smtp.gmail.com:587` (requires App Password)
- Outlook: `smtp-mail.outlook.com:587`
- SendGrid: `smtp.sendgrid.net:587`

### Option 3: AWS SES (Enterprise)

**Best for**: High volume, cost-effective enterprise deployment
**Setup time**: ~30 minutes

```yaml
EMAIL_TRANSPORT=aws-ses
FROM_EMAIL=noreply@yourdomain.com
REPLY_TO_EMAIL=support@yourdomain.com
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1              # Your AWS SES region
```

**Setup requirements**:
- AWS account with SES enabled
- Domain verification
- IAM user with SES permissions
- Production access request (removes sending limits)

### Finding Invitation Links (No Email Configured)

When email is not configured, find invitation links in Railway logs:
1. Go to Railway dashboard → **trigger.dev service** → **View Logs**
2. Look for entries: `##### sendEmail to [email], subject: [subject]`
3. Copy magic link URLs: `https://your-app.up.railway.app/magic?token=<token>`
4. Share links with users for registration

## Why This Dual-Platform Approach?

This template combines **Railway's managed infrastructure** with **DigitalOcean's Docker capabilities** to provide the complete Trigger.dev v4 experience without compromise.

**Railway handles your infrastructure complexity** - PostgreSQL, Redis, ClickHouse, MinIO, and Docker registry are fully managed with automatic backups, while **DigitalOcean provides the Docker socket access** essential for task execution that Railway cannot offer.

**Key Benefits:**
- **True one-click deployment** - ops-controller automates the entire cross-platform setup
- **Zero infrastructure administration** - Railway manages databases, DigitalOcean supervisor auto-configures
- **Cost-effective** - Railway services scale to zero when idle, DigitalOcean droplet optimizes for task load
- **Production-ready** - SSL certificates, health monitoring, and observability across both platforms
- **Complete feature set** - Full Trigger.dev v4 capabilities without platform limitations
- **Automated maintenance** - ops-controller handles supervisor updates and health monitoring
- **Developer-friendly** - GitHub integration, automatic deployments, and unified logging