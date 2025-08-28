#!/bin/bash

# Deploy Trigger.dev supervisor + docker-proxy to DigitalOcean (Robust Version)
# This version handles temporary connection drops and retries operations

set -euo pipefail

# Configuration
DROPLET_NAME="trigger-supervisor-$(date +%s)"
DROPLET_SIZE="s-2vcpu-2gb"
DROPLET_REGION="nyc1" 
DROPLET_IMAGE="docker-20-04"
SSH_KEY_ID="28144145" # Correct SSH key ID (not name)

# SSH options for all connections
SSH_OPTS="-o ConnectTimeout=15 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=30"

echo "🚀 Deploying Trigger.dev supervisor + docker-proxy to DigitalOcean"
echo "📝 Using fixes: SSH key ID, worker token env var, port mapping, firewall, docker compose syntax"

# Function to wait for SSH with retries
wait_for_ssh() {
    local ip=$1
    local max_attempts=60
    local attempt=1
    
    echo "⏳ Waiting for SSH to be available on $ip..."
    echo "💡 Tip: You can also connect manually: ssh root@$ip"
    
    while ! ssh $SSH_OPTS root@"$ip" echo "SSH ready" &>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "❌ SSH connection failed after $max_attempts attempts"
            echo "🔍 Please check if the droplet is running"
            return 1
        fi
        echo "  SSH attempt $attempt/$max_attempts (waiting for droplet to boot...)"
        sleep 15
        ((attempt++))
    done
    
    echo "✅ SSH connection established"
    return 0
}

# Function to retry SSH commands
retry_ssh() {
    local ip=$1
    shift
    local max_retries=3
    local retry=1
    
    while [ $retry -le $max_retries ]; do
        if ssh $SSH_OPTS root@"$ip" "$@"; then
            return 0
        fi
        echo "⚠️ SSH command failed (attempt $retry/$max_retries), retrying in 10 seconds..."
        sleep 10
        ((retry++))
    done
    
    echo "❌ SSH command failed after $max_retries attempts"
    return 1
}

# Function to retry SCP uploads
retry_scp() {
    local src=$1
    local ip=$2
    local dst=$3
    local max_retries=3
    local retry=1
    
    while [ $retry -le $max_retries ]; do
        if scp $SSH_OPTS "$src" root@"$ip":"$dst"; then
            echo "✅ Uploaded: $src -> $dst"
            return 0
        fi
        echo "⚠️ SCP upload failed (attempt $retry/$max_retries), retrying in 10 seconds..."
        sleep 10
        # Re-establish SSH connection
        if ! ssh $SSH_OPTS root@"$ip" echo "SSH test" &>/dev/null; then
            echo "🔄 SSH connection lost, waiting for reconnection..."
            wait_for_ssh "$ip"
        fi
        ((retry++))
    done
    
    echo "❌ SCP upload failed after $max_retries attempts: $src"
    return 1
}

# Create droplet
echo "📦 Creating DigitalOcean droplet: $DROPLET_NAME"
DROPLET_ID=$(doctl compute droplet create "$DROPLET_NAME" \
    --size "$DROPLET_SIZE" \
    --image "$DROPLET_IMAGE" \
    --region "$DROPLET_REGION" \
    --ssh-keys "$SSH_KEY_ID" \
    --wait \
    --format ID \
    --no-header)

echo "✅ Droplet created with ID: $DROPLET_ID"

# Get droplet IP
echo "🔍 Getting droplet IP address..."
DROPLET_IP=$(doctl compute droplet get "$DROPLET_ID" --format PublicIPv4 --no-header)
echo "📍 Droplet IP: $DROPLET_IP"

# Wait for SSH to be available
if ! wait_for_ssh "$DROPLET_IP"; then
    echo "❌ Could not establish SSH connection"
    exit 1
fi

# Open firewall port 8020 for supervisor API
echo "🔒 Opening firewall port 8020..."
retry_ssh "$DROPLET_IP" 'ufw allow 8020/tcp'

# Create deployment directory
echo "📁 Setting up deployment directory..."
retry_ssh "$DROPLET_IP" 'mkdir -p /opt/trigger-supervisor'

# Create corrected docker-compose.yml
echo "📋 Creating corrected docker-compose.yml..."
cat > /tmp/docker-compose-corrected.yml << 'EOF'
name: trigger

x-logging: &logging-config
  driver: ${LOGGING_DRIVER:-local}
  options:
    max-size: ${LOGGING_MAX_SIZE:-20m}
    max-file: ${LOGGING_MAX_FILES:-5}
    compress: ${LOGGING_COMPRESS:-true}

services:
  supervisor:
    image: ghcr.io/triggerdotdev/supervisor:${TRIGGER_IMAGE_TAG:-v4-beta}
    restart: ${RESTART_POLICY:-unless-stopped}
    logging: *logging-config
    depends_on:
      - docker-proxy
    networks:
      - supervisor
      - docker-proxy
      - webapp
    volumes:
      - shared:/home/node/shared
    ports:
      - "8020:8020"
    # Only needed for bootstrap
    user: root
    # Only needed for bootstrap
    command: sh -c "chown -R node:node /home/node/shared && exec /usr/bin/dumb-init -- pnpm run --filter supervisor start"
    environment:
      # FIX: Use environment variable instead of file
      TRIGGER_WORKER_TOKEN: ${TRIGGER_WORKER_TOKEN}
      MANAGED_WORKER_SECRET: ${MANAGED_WORKER_SECRET}
      TRIGGER_API_URL: ${TRIGGER_API_URL:-http://webapp:3000}
      OTEL_EXPORTER_OTLP_ENDPOINT: ${OTEL_EXPORTER_OTLP_ENDPOINT:-http://webapp:3000/otel}
      TRIGGER_WORKLOAD_API_DOMAIN: supervisor
      TRIGGER_WORKLOAD_API_PORT_EXTERNAL: 8020
      # Optional settings
      DEBUG: 1
      ENFORCE_MACHINE_PRESETS: 1
      TRIGGER_DEQUEUE_INTERVAL_MS: 1000
      DOCKER_HOST: tcp://docker-proxy:2375
      DOCKER_RUNNER_NETWORKS: webapp,supervisor
      DOCKER_REGISTRY_URL: ${DOCKER_REGISTRY_URL:-localhost:5000}
      DOCKER_REGISTRY_USERNAME: ${DOCKER_REGISTRY_USERNAME:-}
      DOCKER_REGISTRY_PASSWORD: ${DOCKER_REGISTRY_PASSWORD:-}
      DOCKER_AUTOREMOVE_EXITED_CONTAINERS: 0
    healthcheck:
      test: ["CMD", "node", "-e", "http.get('http://localhost:8020/health', res => process.exit(res.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 10s

  docker-proxy:
    image: tecnativa/docker-socket-proxy:${DOCKER_PROXY_IMAGE_TAG:-latest}
    restart: ${RESTART_POLICY:-unless-stopped}
    logging: *logging-config
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - docker-proxy
    environment:
      - LOG_LEVEL=info
      - POST=1
      - CONTAINERS=1
      - IMAGES=1
      - INFO=1
      - NETWORKS=1
    healthcheck:
      test: ["CMD", "nc", "-z", "127.0.0.1", "2375"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 5s

volumes:
  shared:

networks:
  docker-proxy:
    name: docker-proxy
  supervisor:
    name: supervisor
  webapp:
    name: webapp
EOF

# Upload configuration files with retries
echo "📤 Uploading configuration files..."
retry_scp "/tmp/docker-compose-corrected.yml" "$DROPLET_IP" "/opt/trigger-supervisor/docker-compose.yml"
retry_scp "scripts/.env.superviser" "$DROPLET_IP" "/opt/trigger-supervisor/.env"

# Clean up temporary file
rm /tmp/docker-compose-corrected.yml

# Deploy supervisor + docker-proxy
echo "🐳 Deploying supervisor and docker-proxy containers..."
retry_ssh "$DROPLET_IP" << 'EOF'
cd /opt/trigger-supervisor

echo "📦 Starting services with docker compose (modern syntax)..."
docker compose up -d

echo "⏳ Waiting for containers to be ready..."
sleep 15

echo "🔍 Checking container status..."
docker compose ps

echo "📊 Container logs (last 15 lines each):"
echo "=== DOCKER-PROXY LOGS ==="
docker compose logs --tail=15 docker-proxy

echo ""
echo "=== SUPERVISOR LOGS ==="
docker compose logs --tail=15 supervisor

echo ""
echo "🌐 Testing internal health endpoint..."
if docker compose exec supervisor curl -f http://localhost:8020/health 2>/dev/null; then
    echo "✅ Internal health check passed"
else
    echo "⚠️ Internal health check failed"
fi
EOF

# Test external health endpoint
echo ""
echo "🌐 Testing external health endpoint..."
sleep 5
if curl -f -m 10 http://"$DROPLET_IP":8020/health 2>/dev/null; then
    echo "✅ External health check passed!"
    HEALTH_STATUS="✅ HEALTHY"
else
    echo "⚠️ External health check failed (but supervisor may still be starting)"
    HEALTH_STATUS="⚠️ STARTING"
fi

echo ""
echo "🎉 Deployment completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Droplet: $DROPLET_NAME ($DROPLET_IP)"
echo "🆔 Droplet ID: $DROPLET_ID"
echo "🔗 Supervisor API: http://$DROPLET_IP:8020/health"
echo "📊 Status: $HEALTH_STATUS"
echo ""
echo "📋 Management commands:"
echo "  🔗 SSH: ssh root@$DROPLET_IP"
echo "  📊 Logs: ssh root@$DROPLET_IP 'cd /opt/trigger-supervisor && docker compose logs -f'"
echo "  🔄 Restart: ssh root@$DROPLET_IP 'cd /opt/trigger-supervisor && docker compose restart'"
echo "  📈 Status: ssh root@$DROPLET_IP 'cd /opt/trigger-supervisor && docker compose ps'"
echo "  🧹 Cleanup: doctl compute droplet delete $DROPLET_ID"
echo ""
echo "🎯 Next steps:"
echo "  1. Test task execution in your Trigger.dev Railway dashboard"
echo "  2. Tasks should now execute on DigitalOcean and report back to Railway"
echo "  3. Monitor logs if needed: ssh root@$DROPLET_IP 'cd /opt/trigger-supervisor && docker compose logs -f supervisor'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"