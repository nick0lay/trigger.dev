# Railway Template Creation Guide

## Understanding Railway Templates

Railway templates are **created from existing deployed services**, not from configuration files. Here's the correct process:

## 📋 Step-by-Step Template Creation

### Step 1: Deploy Your Service First

```bash
# 1. Set up your environment variables locally
export DIGITALOCEAN_TOKEN="dop_v1_your_token"
export TRIGGER_WORKER_TOKEN="tr_wgt_generated_token"
export MANAGED_WORKER_SECRET="generated_secret"

# 2. Deploy to Railway
railway up --detach

# 3. Add any missing variables via Railway dashboard or CLI
railway variables set SUPERVISOR_AUTO_DEPLOY=true
railway variables set SUPERVISOR_INSTANCE_SIZE=s-2vcpu-2gb
railway variables set SUPERVISOR_REGION=nyc1
```

### Step 2: Verify Deployment Works

1. Check that webapp deploys successfully
2. Verify supervisor deployment starts (check logs)
3. Ensure all services are healthy

### Step 3: Create Template from Deployed Service

#### Option A: Via Railway Dashboard

1. Go to your Railway project dashboard
2. Click on **Settings** → **Generate Template**
3. Configure template settings:
   - Template Name: `Trigger.dev with DigitalOcean Supervisor`
   - Description: `Complete Trigger.dev v4 stack with automated supervisor deployment`
   - Include all services (PostgreSQL, Redis, ClickHouse, etc.)
4. Configure environment variables visibility:
   - Mark `DIGITALOCEAN_TOKEN` as required
   - Mark secrets as auto-generated
   - Set default values where appropriate
5. Publish template

#### Option B: Via Railway CLI

```bash
# From your deployed project
railway template create \
  --name "Trigger.dev with DigitalOcean Supervisor" \
  --description "Complete stack with automated supervisor deployment"
```

### Step 4: Configure Template Variables

When creating the template, configure these variable settings:

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DIGITALOCEAN_TOKEN` | String | - | ✅ Yes | DigitalOcean API token |
| `TRIGGER_WORKER_TOKEN` | Secret | Auto-generate | No | Shared auth token |
| `MANAGED_WORKER_SECRET` | Secret | Auto-generate | No | Worker secret |
| `SESSION_SECRET` | Secret | Auto-generate | No | Session encryption |
| `ENCRYPTION_KEY` | Secret | Auto-generate | No | Data encryption |
| `SUPERVISOR_AUTO_DEPLOY` | String | `true` | No | Auto-deploy supervisor |
| `SUPERVISOR_INSTANCE_SIZE` | String | `s-2vcpu-2gb` | No | Droplet size |
| `SUPERVISOR_REGION` | String | `nyc1` | No | Deployment region |

## 🚀 Using the Template

Once created, users can deploy with:

### Via Deploy Button

Add to your README:
```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_TEMPLATE_ID)
```

### Via Railway Dashboard

1. Users visit railway.app/templates
2. Search for your template
3. Click "Deploy"
4. Enter only `DIGITALOCEAN_TOKEN`
5. All other variables are auto-configured

## 📁 What Gets Included in the Template

The Railway template includes:
- **Code**: Your repository at the current commit
- **Services**: All Railway services (Postgres, Redis, etc.)
- **Configuration**: The `railway.json` file settings
- **Variables**: Environment variable schema and defaults
- **Scripts**: The `.railway/scripts/` directory

## 🔧 How Our Implementation Works

### 1. railway.json Configuration
```json
{
  "deploy": {
    "startCommand": "chmod +x .railway/scripts/*.sh && ./.railway/scripts/railway-startup.sh && pnpm start"
  }
}
```
This ensures our startup script runs before the webapp starts.

### 2. Startup Orchestration
The `railway-startup.sh` script:
1. Sets up shared tokens
2. Configures PostgreSQL
3. Triggers supervisor deployment (background)

### 3. Supervisor Deployment
The `deploy-digitalocean-supervisor.sh` script:
1. Uses DigitalOcean API (no SSH needed)
2. Deploys via cloud-init (self-configuring)
3. Reports status back to webapp

## ⚠️ Important Notes

### Railway Templates Are NOT:
- ❌ Created from JSON files in your repo
- ❌ Defined by configuration alone
- ❌ Automatically updated when you change code

### Railway Templates ARE:
- ✅ Snapshots of deployed services
- ✅ Created from running Railway projects
- ✅ Include service configurations and variables
- ✅ One-click deployable by other users

## 🔄 Updating Your Template

To update an existing template:

1. Deploy your updated code to Railway
2. Test all functionality
3. Go to template settings in Railway dashboard
4. Click "Update Template" to snapshot current deployment
5. Update version notes if needed

## 📋 Testing Your Template

Before publishing:

1. **Test fresh deployment**: Delete project and redeploy from template
2. **Verify variables**: Ensure only `DIGITALOCEAN_TOKEN` is required
3. **Check automation**: Supervisor should deploy automatically
4. **Monitor logs**: Ensure no errors in deployment process

## 🎯 End User Experience

When users deploy your template:

```
1. Click "Deploy on Railway"
   ↓
2. Enter DigitalOcean API Token
   ↓ 
3. Click "Deploy"
   ↓
4. Everything else is automatic:
   - Webapp deploys on Railway
   - PostgreSQL configured
   - Supervisor deploys to DigitalOcean
   - Complete stack ready in ~5 minutes
```

## 🔍 Troubleshooting Template Creation

### "Cannot create template" Error
- Ensure your service is fully deployed
- Check that all services are healthy
- Verify you have the right permissions

### Variables Not Showing in Template
- Add variables to deployed service first
- Then create/update template
- Mark variables as "template variables" in settings

### Template Deployment Fails for Users
- Test with a fresh Railway account
- Verify all required files are committed
- Check that scripts have executable permissions

## 📚 References

- [Railway Templates Documentation](https://docs.railway.app/deploy/templates)
- [Railway CLI Documentation](https://docs.railway.app/develop/cli)
- [Creating Railway Templates Guide](https://blog.railway.app/p/templates)