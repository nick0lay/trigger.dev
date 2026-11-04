"""Railway API Client for extracting configuration"""

import re
import time
from typing import Optional, Dict, Any, List
import requests
from retrying import retry
from config import Config


class RailwayClient:
    """Client for interacting with Railway API"""

    def __init__(self):
        self.api_url = Config.RAILWAY_API_URL
        self.headers = {
            "Authorization": f"Bearer {Config.RAILWAY_API_TOKEN}",
            "Content-Type": "application/json",
        }
        self.project_id = Config.RAILWAY_PROJECT_ID
        self.environment_id = Config.RAILWAY_ENVIRONMENT_ID

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Dict:
        """Execute GraphQL request to Railway API"""
        payload = {"query": query, "variables": variables or {}}

        response = requests.post(self.api_url, json=payload, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    def get_service_id(self, service_name: str) -> Optional[str]:
        """Get service ID by name"""
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
                services {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        data = self._graphql_request(query, {"projectId": self.project_id})
        services = data.get("project", {}).get("services", {}).get("edges", [])

        for service in services:
            if service["node"]["name"].lower() == service_name.lower():
                return service["node"]["id"]

        return None

    def find_postgres_service(self) -> Optional[str]:
        """Find PostgreSQL service by trying common names"""
        from config import Config

        # List of common PostgreSQL service names to try
        postgres_names = [
            Config.DB_SERVICE_NAME,  # User configured name (default: "Postgres")
            "Postgres",  # Common Railway template name
            "postgres",  # Lowercase version
            "PostgreSQL",  # Full name variant
            "Database",  # Generic database name
            "DB",  # Short database name
        ]

        # Remove duplicates while preserving order
        unique_names = []
        for name in postgres_names:
            if name not in unique_names:
                unique_names.append(name)

        print(f"🔍 Searching for PostgreSQL service in: {unique_names}")

        for service_name in unique_names:
            service_id = self.get_service_id(service_name)
            if service_id:
                print(f"✅ Found PostgreSQL service: '{service_name}' (ID: {service_id})")
                return service_name

        # If not found, list available services for debugging
        print("⚠️ PostgreSQL service not found. Available services:")
        self.list_all_services()
        return None

    def list_all_services(self) -> None:
        """List all services in the project for debugging"""
        query = """
        query GetProject($projectId: String!) {
            project(id: $projectId) {
                services {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        try:
            data = self._graphql_request(query, {"projectId": self.project_id})
            services = data.get("project", {}).get("services", {}).get("edges", [])

            if services:
                for service in services:
                    name = service["node"]["name"]
                    service_id = service["node"]["id"]
                    print(f"   - {name} (ID: {service_id[:12]}...)")
            else:
                print("   No services found in project")
        except Exception as e:
            print(f"   Could not list services: {e}")

    def get_latest_deployment_id(self, service_name: str) -> Optional[str]:
        """Get the latest successful deployment ID for a service"""
        service_id = self.get_service_id(service_name)
        if not service_id:
            return None

        query = """
        query GetDeployment($environmentId: String!, $projectId: String!, $serviceId: String!) {
            deployments(
                input: {
                    environmentId: $environmentId,
                    projectId: $projectId,
                    serviceId: $serviceId,
                    status: {in: SUCCESS}
                }
                last: 1
            ) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        """

        try:
            data = self._graphql_request(
                query,
                {
                    "environmentId": self.environment_id,
                    "projectId": self.project_id,
                    "serviceId": service_id,
                },
            )

            edges = data.get("deployments", {}).get("edges", [])
            if edges:
                return edges[0]["node"]["id"]

            print(f"⚠️ No successful deployments found for {service_name}")
            return None

        except Exception as e:
            print(f"⚠️ Failed to get deployment ID for {service_name}: {e}")
            return None

    def get_service_variables(self, service_name: str) -> Dict[str, str]:
        """Get environment variables for a service using correct Railway API"""
        service_id = self.get_service_id(service_name)
        if not service_id:
            print(f"⚠️ Service '{service_name}' not found")
            return {}

        # Correct Railway GraphQL query for environment variables
        query = """
        query GetVariables($projectId: String!, $environmentId: String!, $serviceId: String!) {
            variables(
                projectId: $projectId
                environmentId: $environmentId
                serviceId: $serviceId
            )
        }
        """

        try:
            data = self._graphql_request(
                query,
                {
                    "projectId": self.project_id,
                    "environmentId": self.environment_id,
                    "serviceId": service_id,
                },
            )

            # Railway returns variables as a key/value object
            variables = data.get("variables", {})
            return variables

        except Exception as e:
            print(f"⚠️ Failed to get variables for {service_name}: {e}")
            return {}

    def get_deployment_logs(
        self, service_name: str, lines: int = 1000, filter: str = None
    ) -> str:
        """Get logs of the latest successful deployment of a service"""
        deployment_id = self.get_latest_deployment_id(service_name)
        if not deployment_id:
            return ""
        return self.get_logs_for_deployment(deployment_id, lines, filter)

    def get_logs_for_deployment(
        self, deployment_id: str, lines: int = 1000, filter: str = None
    ) -> str:
        """Get the logs of one deployment, joined into one string"""
        query = """
        query GetDeploymentLogs($deploymentId: String!, $limit: Int!, $filter: String) {
            deploymentLogs(
                deploymentId: $deploymentId
                limit: $limit
                filter: $filter
            ) {
                message
                timestamp
                severity
            }
        }
        """

        try:
            variables = {"deploymentId": deployment_id, "limit": lines}
            if filter is not None:
                variables["filter"] = filter

            data = self._graphql_request(query, variables)

            logs_data = data.get("deploymentLogs", [])
            return "\n".join([log.get("message", "") for log in logs_data if log])
        except Exception as e:
            print(f"⚠️ Failed to get logs for deployment {deployment_id}: {e}")
            return ""

    def list_deployment_ids(self, service_name: str, limit: int) -> List[str]:
        """Deployment IDs of a service, newest first, including removed ones.

        The webapp prints the worker token only on its first boot, so the
        token is usually in an older deployment that has since been REMOVED.
        """
        service_id = self.get_service_id(service_name)
        if not service_id:
            return []

        query = """
        query ListDeployments($input: DeploymentListInput!, $first: Int!) {
            deployments(input: $input, first: $first) {
                edges { node { id status createdAt } }
            }
        }
        """
        try:
            data = self._graphql_request(
                query,
                {
                    "first": limit,
                    "input": {
                        "projectId": self.project_id,
                        "environmentId": self.environment_id,
                        "serviceId": service_id,
                        # REMOVING: right after a webapp redeploy the old deployment,
                        # which may hold the token, is still shutting down.
                        "status": {"in": ["SUCCESS", "REMOVING", "REMOVED", "FAILED", "CRASHED", "SLEEPING"]},
                    },
                },
            )
        except Exception as e:
            print(f"⚠️ Failed to list deployments for {service_name}: {e}")
            return []

        nodes = [e["node"] for e in data.get("deployments", {}).get("edges", [])]
        nodes.sort(key=lambda n: n.get("createdAt") or "", reverse=True)
        return [n["id"] for n in nodes[:limit]]

    def persist_worker_token(self, token: str) -> bool:
        """Save the worker token as TRIGGER_WORKER_TOKEN on this service.

        Keeps the token across ops-controller redeploys and log expiry.
        Needs RAILWAY_SERVICE_ID, which Railway sets at runtime. Never raises.
        """
        if not Config.RAILWAY_SERVICE_ID:
            print("⚠️ RAILWAY_SERVICE_ID not set; not saving the worker token")
            return False

        query = """
        mutation SaveWorkerToken($input: VariableCollectionUpsertInput!) {
            variableCollectionUpsert(input: $input)
        }
        """
        try:
            self._graphql_request(
                query,
                {
                    "input": {
                        "projectId": self.project_id,
                        "environmentId": self.environment_id,
                        "serviceId": Config.RAILWAY_SERVICE_ID,
                        "variables": {"TRIGGER_WORKER_TOKEN": token},
                        "skipDeploys": True,
                    }
                },
            )
            print("✅ Saved worker token as TRIGGER_WORKER_TOKEN on this service")
            return True
        except Exception as e:
            print(f"⚠️ Could not save worker token: {e}")
            return False

    def extract_worker_token(self, cached_token: str = None) -> Optional[str]:
        """Extract TRIGGER_WORKER_TOKEN with priority: env var > cache > logs"""

        # Priority 1: Check for manual override
        if Config.TRIGGER_WORKER_TOKEN:
            print(
                f"✅ Using manually configured worker token: {Config.TRIGGER_WORKER_TOKEN[:7]}***"
            )
            return Config.TRIGGER_WORKER_TOKEN

        # Priority 2: Use cached token if available
        if cached_token:
            print(f"✅ Using cached worker token: {cached_token[:7]}***")
            return cached_token

        # Priority 3: Extract from webapp logs, newest deployment first
        print(f"🔍 Extracting worker token from {Config.WEBAPP_SERVICE_NAME} logs...")
        token_pattern = r"(tr_wgt_[a-zA-Z0-9]+)"
        deployment_ids = self.list_deployment_ids(
            Config.WEBAPP_SERVICE_NAME, Config.TOKEN_SEARCH_DEPLOYMENTS
        )
        if not deployment_ids:
            print("⚠️ No webapp deployments found")
            return None

        for deployment_id in deployment_ids:
            logs = self.get_logs_for_deployment(
                deployment_id, Config.LOG_SCAN_LINES, "tr_wgt_"
            )
            matches = re.findall(token_pattern, logs)
            if matches:
                # The most recent token in that deployment (last match)
                token = matches[-1]
                print(f"✅ Found worker token in logs of deployment {deployment_id}: {token[:7]}***")
                self.persist_worker_token(token)
                return token

        print(f"⚠️ No worker token found in the last {len(deployment_ids)} webapp deployments")
        print("   Tip: Set TRIGGER_WORKER_TOKEN manually or check if logs have expired")
        return None

    def get_configuration(self, cached_config: Dict[str, str] = None) -> Dict[str, str]:
        """Get all required configuration from Railway services"""
        print("📊 Fetching configuration from Railway services...")

        config = {}
        cached_config = cached_config or {}

        # Extract worker token with priority handling
        cached_token = cached_config.get("TRIGGER_WORKER_TOKEN")
        worker_token = self.extract_worker_token(cached_token)
        if worker_token:
            config["TRIGGER_WORKER_TOKEN"] = worker_token

        # Get webapp variables using Railway API
        webapp_vars = self.get_service_variables(Config.WEBAPP_SERVICE_NAME)
        if webapp_vars:
            config["MANAGED_WORKER_SECRET"] = webapp_vars.get("MANAGED_WORKER_SECRET", "")
            config["TRIGGER_API_URL"] = webapp_vars.get("API_ORIGIN", "")

        # Get registry variables using Railway API
        registry_vars = self.get_service_variables("registry")
        if registry_vars:
            config["DOCKER_REGISTRY_URL"] = registry_vars.get("RAILWAY_PUBLIC_DOMAIN", "")
            # Credentials for registries with basic auth (REGISTRY_USERNAME and
            # REGISTRY_PASSWORD on the registry service). Empty means no auth.
            config["DOCKER_REGISTRY_USERNAME"] = registry_vars.get("REGISTRY_USERNAME", "")
            config["DOCKER_REGISTRY_PASSWORD"] = registry_vars.get("REGISTRY_PASSWORD", "")

        # Add OTEL endpoint based on API URL
        if config.get("TRIGGER_API_URL"):
            config["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{config['TRIGGER_API_URL']}/otel"

        return config

    def restart_service(self, service_name: str) -> bool:
        """Restart a Railway service"""
        service_id = self.get_service_id(service_name)

        # If service not found and it looks like a PostgreSQL service, try smart detection
        if not service_id and service_name.lower() in [
            "postgres",
            "postgresql",
            "database",
            "db",
        ]:
            print(
                f"⚠️ Service '{service_name}' not found, trying smart PostgreSQL detection..."
            )
            detected_name = self.find_postgres_service()
            if detected_name:
                service_name = detected_name
                service_id = self.get_service_id(service_name)

        if not service_id:
            print(f"⚠️ Cannot restart - service '{service_name}' not found")
            return False

        query = """
        mutation RestartService($serviceId: String!, $environmentId: String!) {
            serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId)
        }
        """

        try:
            self._graphql_request(
                query, {"serviceId": service_id, "environmentId": self.environment_id}
            )
            print(f"✅ Restarted service: {service_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to restart {service_name}: {e}")
            return False

    def wait_for_service_ready(self, service_name: str, timeout: int = 300) -> bool:
        """Wait for a service to be ready after restart"""
        print(f"⏳ Waiting for {service_name} to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if service is responding (simplified check via logs)
            logs = self.get_deployment_logs(service_name, 50)
            if "ready" in logs.lower() or "started" in logs.lower():
                print(f"✅ {service_name} is ready")
                return True

            time.sleep(10)

        print(f"⚠️ Timeout waiting for {service_name}")
        return False
