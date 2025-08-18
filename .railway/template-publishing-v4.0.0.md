# Deploy and Host Trigger.dev v4.0.0 - Build long-running background jobs & AI workflows

# Deploy and Host Trigger.dev on Railway

Trigger.dev is an open-source platform that lets developers reliably run long-duration background jobs—like AI workflows and data processing—directly in their codebase, without timeouts, manual scaling, or complex setup. It solves pain points like failed jobs, timeout limits, and lack of visibility with durable scheduling, automatic retries, and powerful observability.

## About Hosting Trigger.dev

Hosting Trigger.dev involves deploying a web application with task queue, scheduler, and worker pool for background job execution. You need PostgreSQL for job storage, Redis for queue management, and proper environment configuration. This Railway template provides a **streamlined "light" deployment** that includes the core webapp with managed PostgreSQL and Redis services—the essential components needed to run production-grade background jobs.

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
- **Redis instance** - Queue management, real-time features, and caching (provided by Railway)
- **Node.js/TypeScript runtime** - Core execution environment for webapp and task processing
- **Python support** - Full Python environment available for polyglot task execution and AI/ML workflows

### Deployment Dependencies

- **Trigger.dev v4.0.0** - [Latest stable release](https://github.com/triggerdotdev/trigger.dev/releases/tag/trigger.dev%404.0.0)
- **Railway account** - [Sign up at railway.app](https://railway.app)
- **Environment variables** - Auto-configured via Railway template with secure secret generation

### Implementation Details

Deploy a **light version** of Trigger.dev optimized for Railway's managed services:

**What's Included:**
- ✅ **Core Trigger.dev webapp** with dashboard, API, and built-in task workers
- ✅ **Managed PostgreSQL and Redis** via Railway services
- ✅ **Vertical auto-scaling** and health monitoring
- ✅ **SSL certificates** and secure environment setup

**Services Not Included** (vs. full docker-compose):
- ❌ **Electric sync engine** - Real-time PostgreSQL synchronization
- ❌ **ClickHouse database** - Analytics database (connect external via environment variables)
- ❌ **CH-UI interface** - ClickHouse web management interface
- ❌ **OTEL collector** - OpenTelemetry collection (Railway provides built-in observability)

**Key v4.0.0 Developer Features:**
- **Machine presets** - Scale tasks with `micro`, `small-1x`, `large-2x` resource configurations
- **Real-time streaming** - Send live progress updates to your frontend with `ctx.sendEvent()`
- **Enhanced retry logic** - Configurable backoff strategies and error handling
- **TypeScript-first** - Full type safety throughout task definitions and payloads
- **Polyglot task execution** - Write tasks in both Node.js/TypeScript and Python within the same project

**External Integrations Supported:**
- 🔗 **ClickHouse analytics** via environment variables for advanced metrics and observability
- 🔗 **S3-compatible object storage** for large payloads and file processing tasks
- 🔗 **Email services** (Resend, SMTP, AWS SES) for user authentication and notifications

### Email Configuration (Optional)
- **With SMTP configured**: Users receive invitation emails and password reset links directly
- **Without SMTP**: Invitation links are logged to Railway deployment logs - check the "Logs" tab to copy invitation URLs for new users
- **Supported providers**: Any SMTP service, Resend, AWS SES, or external email APIs

## Why Deploy Trigger.dev on Railway?

Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while automatically managing resource scaling.

By deploying Trigger.dev on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.

**Key Railway Benefits:**
- **Zero database administration** - Fully managed PostgreSQL and Redis with automatic backups
- **Intelligent scaling** - Automatic vertical scaling with configurable worker concurrency
- **Cost-effective** - Pay only for resources used, scale down to zero when idle
- **Developer-friendly** - One-click deployment from GitHub with automatic updates
- **Production-ready** - SSL certificates, monitoring, and health checks included
- **Simplified deployment** - Focus on building tasks while Railway handles infrastructure