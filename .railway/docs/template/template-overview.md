# Deploy and Host Trigger.dev on Railway

Trigger.dev is an open-source platform that lets developers reliably run long-duration background jobs—like AI workflows and data processing—directly in their codebase, without timeouts, manual scaling, or complex setup.

## About Hosting Trigger.dev

Hosting Trigger.dev involves deploying a web application with task queue, scheduler, and worker pool for background job execution. You need PostgreSQL for job storage, Redis for queue management, ClickHouse for analytics, object storage for large payloads, and a Docker registry for deployments. This Railway template provides a complete production-ready deployment that includes all necessary services: Trigger.dev webapp, managed PostgreSQL and Redis, ClickHouse analytics database, MinIO object storage, and a private Docker registry—everything needed to run enterprise-grade background jobs with automatic scaling and monitoring.

## Common Use Cases

- **AI workflow orchestration** - LLM pipelines, model inference, and AI agent automation without timeouts
- **Video and audio processing** - Long-running media processing tasks that exceed typical serverless limits
- **Data import and ETL** - Batch processing, data transformation, and migration jobs with progress tracking
- **Document generation** - Automated PDF creation, report generation, and file processing workflows
- **Webhook automation** - Event-driven workflows and third-party service integrations with retry logic
- **Scheduled task execution** - Cron-like scheduling with robust error handling and real-time monitoring
- **API workflow orchestration** - Chain multiple API calls with proper error handling and state management

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
- **Documentation** - [Official Trigger.dev docs](https://trigger.dev/docs)

### Optional Services

- **Electric Sync Engine** - [Deploy separately](https://railway.com/deploy/electricsql-1) for real-time PostgreSQL synchronization
- **External ClickHouse** - Replace built-in ClickHouse with cloud provider, manage with [CH-UI](https://ch-ui.com/)
- **External Object Storage** - Replace built-in MinIO with AWS S3, Google Cloud Storage, or other providers

### Implementation Details

**What's Included:**
- ✅ Core Trigger.dev webapp with dashboard, API, and built-in task workers
- ✅ Managed PostgreSQL and Redis via Railway services
- ✅ ClickHouse analytics database for advanced metrics and observability
- ✅ MinIO S3-compatible object storage for large payloads and file processing
- ✅ Private Docker registry for secure task deployment and container management
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

## Why Deploy Trigger.dev on Railway?

Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying Trigger.dev on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.

**Additional Railway Benefits:**
- **Zero infrastructure administration** - Fully managed PostgreSQL, Redis, ClickHouse, MinIO, and Docker registry with automatic backups
- **One-click deployment** - Deploy complete Trigger.dev stack from this template in ~5 minutes
- **Cost-effective** - Pay only for resources used, all services scale down to zero when idle
- **Production-ready** - SSL certificates, monitoring, health checks, and observability included
- **Complete observability** - Built-in analytics with ClickHouse and monitoring dashboards
- **Secure deployments** - Private Docker registry for secure task container management
- **Developer-friendly** - GitHub integration with automatic deployments and CI/CD