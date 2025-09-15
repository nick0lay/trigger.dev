"""DigitalOcean Manager for supervisor droplet deployment"""
import time
import digitalocean
from typing import Optional, Dict, List
from jinja2 import Template
from config import Config


class DigitalOceanManager:
    """Manage DigitalOcean droplet deployment for supervisor"""

    def __init__(self):
        self.manager = digitalocean.Manager(token=Config.DIGITALOCEAN_TOKEN)
        self.tag = Config.get_supervisor_tag()

    def get_existing_droplets(self) -> List[digitalocean.Droplet]:
        """Get existing supervisor droplets by tag"""
        try:
            # Get all droplets
            all_droplets = self.manager.get_all_droplets()

            # Filter by our tag
            tagged_droplets = []
            for droplet in all_droplets:
                if self.tag in droplet.tags:
                    tagged_droplets.append(droplet)

            return tagged_droplets
        except Exception as e:
            print(f"❌ Failed to get droplets: {e}")
            return []

    def is_supervisor_deployed(self) -> bool:
        """Check if supervisor is already deployed"""
        droplets = self.get_existing_droplets()
        if droplets:
            print(f"ℹ️ Found {len(droplets)} existing supervisor droplet(s):")
            for droplet in droplets:
                print(f"   - {droplet.name} ({droplet.ip_address}) - Status: {droplet.status}")
            return True
        return False

    def create_cloud_init_script(self, config: Dict[str, str]) -> str:
        """Create cloud-init script for supervisor deployment"""
        template = Template(
            """#cloud-config
package_update: true
packages:
  - curl
  - jq
  - ufw

runcmd:
  # Create directory for supervisor
  - mkdir -p /opt/trigger-supervisor

  # Create environment file
  - |
    cat > /opt/trigger-supervisor/.env << 'EOF'
    TRIGGER_WORKER_TOKEN={{ trigger_worker_token }}
    MANAGED_WORKER_SECRET={{ managed_worker_secret }}
    TRIGGER_API_URL={{ trigger_api_url }}
    OTEL_EXPORTER_OTLP_ENDPOINT={{ otel_endpoint }}
    TRIGGER_WORKLOAD_API_DOMAIN=supervisor
    TRIGGER_WORKLOAD_API_PORT_EXTERNAL=8020
    DEBUG=1
    ENFORCE_MACHINE_PRESETS=1
    TRIGGER_DEQUEUE_INTERVAL_MS=1000
    DOCKER_HOST=tcp://docker-proxy:2375
    DOCKER_RUNNER_NETWORKS=supervisor
    DOCKER_REGISTRY_URL={{ docker_registry_url }}
    DOCKER_REGISTRY_USERNAME={{ docker_registry_username }}
    DOCKER_REGISTRY_PASSWORD={{ docker_registry_password }}
    DOCKER_AUTOREMOVE_EXITED_CONTAINERS=1
    EOF

  # Create Docker networks
  - docker network create docker-proxy --driver bridge || echo "Network exists"
  - docker network create supervisor --driver bridge || echo "Network exists"

  # Create docker-compose.yml
  - |
    cat > /opt/trigger-supervisor/docker-compose.yml << 'EOF'
    name: trigger

    services:
      supervisor:
        image: ghcr.io/triggerdotdev/supervisor:{{ trigger_version }}
        restart: unless-stopped
        depends_on:
          - docker-proxy
        networks:
          - supervisor
          - docker-proxy
        volumes:
          - shared:/home/node/shared
        ports:
          - "8020:8020"
        user: root
        command: sh -c "chown -R node:node /home/node/shared && exec /usr/bin/dumb-init -- pnpm run --filter supervisor start"
        env_file: .env
        healthcheck:
          test: ["CMD", "node", "-e", "http.get('http://localhost:8020/health', res => process.exit(res.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"]
          interval: 30s
          timeout: 10s
          retries: 5
          start_period: 30s

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
        healthcheck:
          test: ["CMD", "nc", "-z", "127.0.0.1", "2375"]
          interval: 30s
          timeout: 5s
          retries: 5

    volumes:
      shared:

    networks:
      docker-proxy:
        external: true
      supervisor:
        external: true
    EOF

  # Configure firewall
  - ufw allow 22/tcp
  - ufw allow 8020/tcp
  - ufw --force enable

  # Start Docker services
  - systemctl enable docker
  - systemctl start docker

  # Wait for Docker
  - |
    echo "Waiting for Docker daemon..."
    for i in {1..30}; do
      if docker info >/dev/null 2>&1; then
        echo "Docker ready after $i attempts"
        break
      fi
      sleep 2
    done

  # Start supervisor containers
  - cd /opt/trigger-supervisor && docker compose up -d

  # Wait for supervisor to be healthy
  - |
    echo "Waiting for supervisor health..."
    for i in {1..60}; do
      if curl -f http://localhost:8020/health >/dev/null 2>&1; then
        echo "Supervisor healthy after $i attempts"
        break
      fi
      sleep 5
    done

  # Log deployment status
  - |
    echo "Deployment completed at $(date)" > /var/log/supervisor-deployment.log
    docker compose ps >> /var/log/supervisor-deployment.log
    curl -s http://localhost:8020/health >> /var/log/supervisor-deployment.log
"""
        )

        # Fill in the template
        return template.render(
            trigger_worker_token=config.get("TRIGGER_WORKER_TOKEN", ""),
            managed_worker_secret=config.get("MANAGED_WORKER_SECRET", ""),
            trigger_api_url=config.get("TRIGGER_API_URL", ""),
            otel_endpoint=config.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
            docker_registry_url=config.get("DOCKER_REGISTRY_URL", ""),
            docker_registry_username=config.get("DOCKER_REGISTRY_USERNAME", ""),
            docker_registry_password=config.get("DOCKER_REGISTRY_PASSWORD", ""),
            trigger_version=Config.TRIGGER_VERSION
        )

    def create_droplet(self, config: Dict[str, str]) -> Optional[digitalocean.Droplet]:
        """Create a new supervisor droplet"""
        print("🚀 Creating DigitalOcean droplet for supervisor...")

        # Check if already deployed
        if self.is_supervisor_deployed():
            print("ℹ️ Supervisor already deployed, skipping creation")
            return None

        # Generate cloud-init script
        user_data = self.create_cloud_init_script(config)

        # Create droplet
        droplet_name = Config.get_droplet_name()
        droplet = digitalocean.Droplet(
            token=Config.DIGITALOCEAN_TOKEN,
            name=droplet_name,
            region=Config.SUPERVISOR_REGION,
            image=Config.SUPERVISOR_IMAGE,
            size_slug=Config.SUPERVISOR_SIZE,
            user_data=user_data,
            monitoring=True,
            tags=[self.tag, "trigger-supervisor", "ops-controller-deployed"]
        )

        try:
            droplet.create()
            print(f"✅ Droplet created: {droplet_name}")
            print(f"   ID: {droplet.id}")
            return droplet
        except Exception as e:
            print(f"❌ Failed to create droplet: {e}")
            return None

    def wait_for_droplet_ready(self, droplet: digitalocean.Droplet,
                              timeout: int = Config.DROPLET_WAIT_TIMEOUT) -> bool:
        """Wait for droplet to be ready"""
        print("⏳ Waiting for droplet to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Reload droplet info
                droplet.load()

                # Check if droplet has IP address
                if droplet.ip_address and droplet.status == "active":
                    print(f"✅ Droplet ready with IP: {droplet.ip_address}")
                    return True

                print(f"   Status: {droplet.status}, IP: {droplet.ip_address or 'pending'}")
                time.sleep(10)
            except Exception as e:
                print(f"⚠️ Error checking droplet status: {e}")
                time.sleep(10)

        print("⚠️ Timeout waiting for droplet")
        return False

    def test_supervisor_health(self, ip_address: str, max_attempts: int = 30) -> bool:
        """Test if supervisor is healthy"""
        import requests

        print(f"🔍 Testing supervisor health at {ip_address}:8020...")

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(f"http://{ip_address}:8020/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Supervisor is healthy (attempt {attempt})")
                    return True
            except Exception:
                pass

            print(f"   Attempt {attempt}/{max_attempts}: Not ready yet...")
            time.sleep(10)

        print("⚠️ Supervisor health check failed")
        return False

    def deploy_supervisor(self, config: Dict[str, str]) -> bool:
        """Deploy supervisor to DigitalOcean"""
        print("🌊 Deploying supervisor to DigitalOcean...")

        # Validate configuration
        required_keys = ["TRIGGER_WORKER_TOKEN", "MANAGED_WORKER_SECRET", "TRIGGER_API_URL"]
        missing_keys = [key for key in required_keys if not config.get(key)]

        if missing_keys:
            print(f"❌ Missing required configuration: {', '.join(missing_keys)}")
            return False

        # Check if already deployed
        existing_droplets = self.get_existing_droplets()
        if existing_droplets:
            droplet = existing_droplets[0]
            print(f"ℹ️ Using existing droplet: {droplet.name} ({droplet.ip_address})")

            # Test health
            if droplet.ip_address:
                if self.test_supervisor_health(droplet.ip_address):
                    print("✅ Supervisor deployment verified")
                    return True
                else:
                    print("⚠️ Existing supervisor not healthy, consider manual intervention")
                    return False

        # Create new droplet
        droplet = self.create_droplet(config)
        if not droplet:
            return False

        # Wait for droplet to be ready
        if not self.wait_for_droplet_ready(droplet):
            print("❌ Droplet creation failed or timed out")
            return False

        # Test supervisor health
        if not self.test_supervisor_health(droplet.ip_address):
            print("⚠️ Supervisor deployment completed but health check failed")
            print("   Check cloud-init logs: ssh root@{} 'tail -f /var/log/cloud-init-output.log'".format(
                droplet.ip_address))
            return False

        print("🎉 Supervisor successfully deployed!")
        print(f"   URL: http://{droplet.ip_address}:8020")
        print(f"   Health: http://{droplet.ip_address}:8020/health")
        return True

    def get_deployment_info(self) -> Dict[str, any]:
        """Get information about deployed supervisor"""
        droplets = self.get_existing_droplets()

        if not droplets:
            return {"deployed": False}

        droplet = droplets[0]
        droplet.load()

        return {
            "deployed": True,
            "name": droplet.name,
            "id": droplet.id,
            "ip_address": droplet.ip_address,
            "status": droplet.status,
            "region": droplet.region["slug"],
            "size": droplet.size["slug"],
            "created_at": droplet.created_at,
            "health_url": f"http://{droplet.ip_address}:8020/health" if droplet.ip_address else None
        }

    def destroy_droplet(self) -> bool:
        """Destroy existing supervisor droplet (use with caution!)"""
        droplets = self.get_existing_droplets()

        if not droplets:
            print("ℹ️ No supervisor droplets to destroy")
            return True

        for droplet in droplets:
            try:
                print(f"🗑️ Destroying droplet: {droplet.name}")
                droplet.destroy()
                print(f"✅ Destroyed droplet: {droplet.name}")
            except Exception as e:
                print(f"❌ Failed to destroy droplet {droplet.name}: {e}")
                return False

        return True
