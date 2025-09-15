#!/bin/bash
# DigitalOcean Droplet Setup Script for Trigger.dev Supervisor

set -e

echo "🚀 Setting up Trigger.dev Supervisor on DigitalOcean Droplet"

# Update system
apt-get update
apt-get upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    apt-get install docker-compose-plugin -y
fi

# Create directory for supervisor
mkdir -p /opt/trigger-supervisor
cd /opt/trigger-supervisor

# Create docker-compose.yml for supervisor
cat > docker-compose.yml << 'EOF'
name: trigger-supervisor

services:
  supervisor:
    image: ghcr.io/triggerdotdev/supervisor:v4-beta
    restart: unless-stopped
    depends_on:
      - docker-proxy
    networks:
      - supervisor
      - docker-proxy
    environment:
      # These will be set from environment variables
      TRIGGER_WORKER_TOKEN: ${TRIGGER_WORKER_TOKEN}
      MANAGED_WORKER_SECRET: ${MANAGED_WORKER_SECRET}
      TRIGGER_API_URL: ${TRIGGER_API_URL}
      OTEL_EXPORTER_OTLP_ENDPOINT: ${OTEL_EXPORTER_OTLP_ENDPOINT}
      # Docker configuration
      DOCKER_HOST: tcp://docker-proxy:2375
      DOCKER_RUNNER_NETWORKS: supervisor
      DOCKER_REGISTRY_URL: ${DOCKER_REGISTRY_URL:-}
      DOCKER_REGISTRY_USERNAME: ${DOCKER_REGISTRY_USERNAME:-}
      DOCKER_REGISTRY_PASSWORD: ${DOCKER_REGISTRY_PASSWORD:-}
      # Supervisor configuration
      TRIGGER_WORKLOAD_API_DOMAIN: ${DROPLET_PUBLIC_IP}
      TRIGGER_WORKLOAD_API_PORT_EXTERNAL: 8020
      DOCKER_AUTOREMOVE_EXITED_CONTAINERS: 1
    ports:
      - "8020:8020"

  docker-proxy:
    image: tecnativa/docker-socket-proxy:latest
    restart: unless-stopped
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

networks:
  docker-proxy:
  supervisor:
EOF

# Create .env template
cat > .env.template << 'EOF'
# Get these from your webapp deployment
TRIGGER_WORKER_TOKEN=tr_wgt_...
MANAGED_WORKER_SECRET=

# Webapp URL (from App Platform)
TRIGGER_API_URL=https://your-app.ondigitalocean.app
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-app.ondigitalocean.app/otel

# This droplet's public IP (will be auto-filled)
DROPLET_PUBLIC_IP=

# Optional: Docker registry credentials
DOCKER_REGISTRY_URL=
DOCKER_REGISTRY_USERNAME=
DOCKER_REGISTRY_PASSWORD=
EOF

# Get droplet public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)
echo "DROPLET_PUBLIC_IP=${PUBLIC_IP}" >> .env.template

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.template to .env and fill in the values"
echo "2. Get TRIGGER_WORKER_TOKEN from webapp (create worker group or use bootstrap token)"
echo "3. Set TRIGGER_API_URL to your App Platform webapp URL"
echo "4. Run: docker compose up -d"
echo ""
echo "Your droplet IP: ${PUBLIC_IP}"