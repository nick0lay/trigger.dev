"""Configuration for Ops Controller"""
import os
import re
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the ops controller"""

    # DigitalOcean settings
    DIGITALOCEAN_TOKEN: str = os.getenv("DIGITALOCEAN_TOKEN", "")
    SUPERVISOR_REGION: str = os.getenv("SUPERVISOR_REGION", "nyc3")
    SUPERVISOR_SIZE: str = os.getenv("SUPERVISOR_SIZE", "s-2vcpu-2gb")
    SUPERVISOR_IMAGE: str = "docker-20-04"
    SUPERVISOR_TAG_PREFIX: str = "trigger-supervisor"

    # Railway settings
    RAILWAY_API_TOKEN: str = os.getenv("RAILWAY_API_TOKEN", "")
    RAILWAY_API_URL: str = "https://backboard.railway.app/graphql/v2"
    RAILWAY_PROJECT_ID: str = os.getenv("RAILWAY_PROJECT_ID", "")
    RAILWAY_ENVIRONMENT_ID: str = os.getenv("RAILWAY_ENVIRONMENT_ID", "")
    # Set by Railway at runtime; used to save the worker token on this service.
    RAILWAY_SERVICE_ID: str = os.getenv("RAILWAY_SERVICE_ID", "")

    # PostgreSQL settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_SERVICE_NAME: str = os.getenv("DB_SERVICE_NAME", "Postgres")

    # Railway service names
    WEBAPP_SERVICE_NAME: str = os.getenv("WEBAPP_SERVICE_NAME", "trigger.dev")

    # Trigger.dev settings
    TRIGGER_VERSION: str = os.getenv("TRIGGER_VERSION", "v4.0.0")
    # Manual worker token override (optional)
    TRIGGER_WORKER_TOKEN: str = os.getenv("TRIGGER_WORKER_TOKEN", "")
    DOCKER_REGISTRY_URL: str = os.getenv("DOCKER_REGISTRY_URL", "")

    # Operational settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    LOG_SCAN_LINES: int = 1000
    # How many webapp deployments (newest first) to search for the worker token
    TOKEN_SEARCH_DEPLOYMENTS: int = 20
    DROPLET_WAIT_TIMEOUT: int = 300  # 5 minutes

    # Monitoring settings
    IS_ACTIVE: bool = os.getenv("IS_ACTIVE", "true").lower() == "true"
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "1"))
    # Auto-disable after successful deployment
    AUTO_DISABLE: bool = os.getenv("AUTO_DISABLE", "false").lower() == "true"
    HEALTHY_CYCLES_BEFORE_DISABLE: int = int(os.getenv("HEALTHY_CYCLES_BEFORE_DISABLE", "3"))

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [
            ("DIGITALOCEAN_TOKEN", cls.DIGITALOCEAN_TOKEN),
            ("RAILWAY_API_TOKEN", cls.RAILWAY_API_TOKEN),
            ("RAILWAY_PROJECT_ID", cls.RAILWAY_PROJECT_ID),
            ("DATABASE_URL", cls.DATABASE_URL)
        ]

        missing = []
        for name, value in required:
            if not value:
                missing.append(name)

        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False

        # Validate CHECK_INTERVAL is reasonable (1-60 minutes)
        if not (1 <= cls.CHECK_INTERVAL <= 60):
            print(f"❌ CHECK_INTERVAL must be between 1 and 60 minutes, got {cls.CHECK_INTERVAL}")
            return False

        return True

    @classmethod
    def get_supervisor_tag(cls) -> str:
        """Get unique tag for supervisor droplet"""
        env_id = cls.RAILWAY_ENVIRONMENT_ID[:8] if cls.RAILWAY_ENVIRONMENT_ID else "default"
        return f"{cls.SUPERVISOR_TAG_PREFIX}-{cls.RAILWAY_PROJECT_ID}-{env_id}"

    VERSION_TAG_PREFIX: str = "trigger-version:"

    @classmethod
    def get_version_tag(cls, version: str = None) -> str:
        """Droplet tag that records the Trigger.dev version of the supervisor.

        DigitalOcean tags allow only letters, numbers, ':', '-' and '_', so
        v4.8.3 becomes trigger-version:v4-8-3.
        """
        value = version or cls.TRIGGER_VERSION
        return cls.VERSION_TAG_PREFIX + re.sub(r"[^A-Za-z0-9_-]", "-", value)

    @classmethod
    def get_droplet_name(cls) -> str:
        """Generate droplet name"""
        import time
        timestamp = int(time.time())
        env_id = cls.RAILWAY_ENVIRONMENT_ID[:8] if cls.RAILWAY_ENVIRONMENT_ID else "default"
        return f"{cls.SUPERVISOR_TAG_PREFIX}-{env_id}-{timestamp}"
