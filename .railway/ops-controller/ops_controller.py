#!/usr/bin/env python3
"""
Ops Controller - Automated supervisor deployment for Trigger.dev
Orchestrates PostgreSQL configuration and DigitalOcean deployment
"""
import sys
import time
import json
from typing import Dict
from colorama import init, Fore, Style

from config import Config
from railway_client import RailwayClient
from postgres_configurator import PostgresConfigurator
from digitalocean_manager import DigitalOceanManager

# Initialize colorama for colored output
init(autoreset=True)


class OpsController:
    """Main orchestrator for supervisor deployment"""

    def __init__(self):
        self.railway_client = RailwayClient()
        self.do_manager = DigitalOceanManager()
        self.config_cache = {}
        self.deployment_state = {
            "postgres_configured": False,
            "supervisor_deployed": False,
            "config_extracted": False
        }
        self.consecutive_healthy_cycles = 0
        self.is_disabled = False

    def print_header(self):
        """Print application header"""
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.CYAN}    Trigger.dev Ops Controller")
        print(f"{Fore.CYAN}    Automated Supervisor Deployment")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

    def print_status(self, message: str, status: str = "info"):
        """Print colored status message"""
        colors = {
            "info": Fore.BLUE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED
        }
        symbols = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        color = colors.get(status, Fore.WHITE)
        symbol = symbols.get(status, "•")
        print(f"{color}{symbol} {message}{Style.RESET_ALL}")

    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        self.print_status("Validating environment configuration...", "info")

        if not Config.validate():
            self.print_status("Environment validation failed", "error")
            return False

        self.print_status("Environment validated successfully", "success")
        return True

    def extract_configuration(self) -> Dict[str, str]:
        """Extract configuration from Railway"""
        self.print_status("Extracting configuration from Railway...", "info")

        try:
            # Pass cached config to prioritize cached/manual tokens
            config = self.railway_client.get_configuration(self.config_cache)

            if not config.get("TRIGGER_WORKER_TOKEN"):
                self.print_status("Could not extract worker token", "warning")
                if not Config.TRIGGER_WORKER_TOKEN:
                    self.print_status("Tip: Set TRIGGER_WORKER_TOKEN manually if logs have expired", "warning")
                return {}

            self.config_cache = config
            self.deployment_state["config_extracted"] = True

            self.print_status(f"Extracted {len(config)} configuration values", "success")
            for key in config:
                masked_value = config[key][:20] + "..." if len(config[key]) > 20 else config[key]
                print(f"    {key}: {masked_value}")

            return config
        except Exception as e:
            self.print_status(f"Failed to extract configuration: {e}", "error")
            return {}

    def configure_postgres(self) -> bool:
        """Configure PostgreSQL for logical replication"""
        self.print_status("Configuring PostgreSQL for logical replication...", "info")

        try:
            with PostgresConfigurator() as pg:
                # Check if already configured
                is_configured, status = pg.is_replication_configured()
                if is_configured:
                    self.print_status(f"PostgreSQL already configured: {status}", "success")
                    self.deployment_state["postgres_configured"] = True
                    return True

                # Configure replication
                def handle_restart():
                    self.print_status("PostgreSQL restart required", "warning")
                    self.print_status("Restarting PostgreSQL via Railway...", "info")
                    db_service_name = Config.DB_SERVICE_NAME
                    if self.railway_client.restart_service(db_service_name):
                        self.print_status(f"PostgreSQL ({db_service_name}) restarted", "success")
                        time.sleep(30)  # Wait for restart
                    else:
                        self.print_status(f"Could not restart PostgreSQL service '{db_service_name}' automatically", "warning")

                success = pg.configure_replication(handle_restart)

                if success:
                    self.print_status("PostgreSQL configured successfully", "success")
                    self.deployment_state["postgres_configured"] = True
                else:
                    self.print_status("PostgreSQL configuration incomplete", "warning")

                return success

        except Exception as e:
            self.print_status(f"Failed to configure PostgreSQL: {e}", "error")
            return False

    def deploy_supervisor(self) -> bool:
        """Deploy supervisor to DigitalOcean"""
        self.print_status("Deploying supervisor to DigitalOcean...", "info")

        if not self.config_cache:
            self.print_status("No configuration available for deployment", "error")
            return False

        try:
            # Check if already deployed
            deployment_info = self.do_manager.get_deployment_info()
            if deployment_info.get("deployed"):
                self.print_status(f"Supervisor already deployed at {deployment_info['ip_address']}", "success")
                self.deployment_state["supervisor_deployed"] = True
                return True

            # Deploy supervisor
            success = self.do_manager.deploy_supervisor(self.config_cache)

            if success:
                self.print_status("Supervisor deployed successfully", "success")
                self.deployment_state["supervisor_deployed"] = True

                # Get deployment info
                info = self.do_manager.get_deployment_info()
                if info.get("deployed"):
                    print(f"\n{Fore.GREEN}Deployment Details:{Style.RESET_ALL}")
                    print(f"  Name: {info['name']}")
                    print(f"  IP: {info['ip_address']}")
                    print(f"  Health: {info['health_url']}")
            else:
                self.print_status("Supervisor deployment failed", "error")

            return success

        except Exception as e:
            self.print_status(f"Failed to deploy supervisor: {e}", "error")
            return False

    def run_full_deployment(self) -> bool:
        """Run full deployment process"""
        self.print_header()

        # Step 1: Validate environment
        if not self.validate_environment():
            return False

        # Step 2: Extract configuration
        config = self.extract_configuration()
        if not config:
            self.print_status("Cannot proceed without configuration", "error")
            return False

        # Step 3: Configure PostgreSQL
        if not self.configure_postgres():
            self.print_status("PostgreSQL configuration failed, but continuing...", "warning")

        # Step 4: Deploy supervisor
        if not self.deploy_supervisor():
            return False

        # Summary
        self.print_summary()
        return True

    def run_check_status(self) -> bool:
        """Check deployment status"""
        self.print_header()

        # Check PostgreSQL
        self.print_status("Checking PostgreSQL configuration...", "info")
        try:
            with PostgresConfigurator() as pg:
                is_configured, status = pg.is_replication_configured()
                if is_configured:
                    self.print_status(f"PostgreSQL: {status}", "success")
                else:
                    self.print_status(f"PostgreSQL: {status}", "warning")
        except Exception as e:
            self.print_status(f"Could not check PostgreSQL: {e}", "error")

        # Check supervisor
        self.print_status("Checking supervisor deployment...", "info")
        deployment_info = self.do_manager.get_deployment_info()
        if deployment_info.get("deployed"):
            self.print_status(f"Supervisor deployed at {deployment_info['ip_address']}", "success")
            print(f"  Status: {deployment_info['status']}")
            print(f"  Region: {deployment_info['region']}")
            print(f"  Size: {deployment_info['size']}")
            print(f"  Health: {deployment_info['health_url']}")
        else:
            self.print_status("No supervisor deployment found", "warning")

        return True

    def run_destroy(self) -> bool:
        """Destroy supervisor deployment"""
        self.print_header()
        self.print_status("⚠️ WARNING: This will destroy the supervisor droplet!", "warning")

        # Confirm destruction
        response = input("Type 'DESTROY' to confirm: ")
        if response != "DESTROY":
            self.print_status("Destruction cancelled", "info")
            return False

        self.print_status("Destroying supervisor deployment...", "warning")
        if self.do_manager.destroy_droplet():
            self.print_status("Supervisor destroyed", "success")
            return True
        else:
            self.print_status("Failed to destroy supervisor", "error")
            return False

    def print_summary(self):
        """Print deployment summary"""
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.CYAN}Deployment Summary")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

        status_emoji = {
            True: "✅",
            False: "❌"
        }

        print(f"Configuration extracted: {status_emoji[self.deployment_state['config_extracted']]}")
        print(f"PostgreSQL configured: {status_emoji[self.deployment_state['postgres_configured']]}")
        print(f"Supervisor deployed: {status_emoji[self.deployment_state['supervisor_deployed']]}")

        if all(self.deployment_state.values()):
            print(f"\n{Fore.GREEN}🎉 Deployment completed successfully!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️ Deployment partially completed{Style.RESET_ALL}")

    def save_state(self, filename: str = "/tmp/ops-controller-state.json"):
        """Save deployment state to file"""
        try:
            state = {
                "deployment_state": self.deployment_state,
                "config_cache": self.config_cache,
                "consecutive_healthy_cycles": self.consecutive_healthy_cycles,
                "is_disabled": self.is_disabled,
                "timestamp": time.time()
            }
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            self.print_status(f"State saved to {filename}", "info")
        except Exception as e:
            self.print_status(f"Failed to save state: {e}", "warning")

    def load_state(self, filename: str = "/tmp/ops-controller-state.json"):
        """Load deployment state from file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            self.deployment_state = state.get("deployment_state", {})
            self.config_cache = state.get("config_cache", {})
            self.consecutive_healthy_cycles = state.get("consecutive_healthy_cycles", 0)
            self.is_disabled = state.get("is_disabled", False)
            self.print_status(f"State loaded from {filename}", "info")
            if self.consecutive_healthy_cycles > 0:
                self.print_status(f"Resuming with {self.consecutive_healthy_cycles} consecutive healthy cycles", "info")
        except Exception:
            pass  # Ignore if file doesn't exist


    def run_monitoring_loop(self) -> None:
        """Run continuous monitoring loop"""
        self.print_header()

        if not Config.IS_ACTIVE:
            self.print_status("Monitoring is disabled (IS_ACTIVE=false)", "warning")
            self.print_status("Service will sleep indefinitely", "info")
            while True:
                time.sleep(300)  # Sleep 5 minutes and check again
                continue

        self.print_status(f"Starting continuous monitoring (interval: {Config.CHECK_INTERVAL} minutes)", "info")
        if Config.AUTO_DISABLE:
            self.print_status(f"Auto-disable enabled after {Config.HEALTHY_CYCLES_BEFORE_DISABLE} healthy cycles", "info")
        self.print_status("Press Ctrl+C to stop", "info")

        # Initial state load
        self.load_state()

        while True:
            try:
                # Check if auto-disabled
                if self.is_disabled:
                    self.print_status("Monitoring auto-disabled after successful deployment", "info")
                    self.print_status("Service will sleep indefinitely", "info")
                    while True:
                        time.sleep(300)  # Sleep 5 minutes
                        continue

                self.print_status("=== Starting monitoring cycle ===", "info")
                cycle_start = time.time()

                # Validate environment first
                if not self.validate_environment():
                    self.print_status("Environment validation failed, retrying in next cycle", "error")
                else:
                    # Run the monitoring checks
                    self._run_monitoring_cycle()

                # Save state after cycle
                self.save_state()

                # Calculate sleep time
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, (Config.CHECK_INTERVAL * 60) - cycle_duration)

                if sleep_time > 0:
                    self.print_status(f"Cycle completed in {cycle_duration:.1f}s, sleeping for {sleep_time:.1f}s", "info")
                    time.sleep(sleep_time)
                else:
                    self.print_status(f"Cycle took {cycle_duration:.1f}s (longer than {Config.CHECK_INTERVAL}min interval)", "warning")

            except KeyboardInterrupt:
                self.print_status("Monitoring stopped by user", "info")
                break
            except Exception as e:
                self.print_status(f"Error in monitoring cycle: {e}", "error")
                self.print_status(f"Retrying in {Config.CHECK_INTERVAL} minutes", "warning")
                time.sleep(Config.CHECK_INTERVAL * 60)

    def _run_monitoring_cycle(self) -> None:
        """Run a single monitoring cycle"""
        # Step 1: Extract configuration if needed
        if not self.deployment_state.get("config_extracted") or not self.config_cache:
            self.print_status("Extracting configuration from Railway...", "info")
            config = self.extract_configuration()
            if not config:
                self.print_status("Could not extract configuration, will retry next cycle", "warning")
                return

        # Step 2: Check and configure PostgreSQL
        if not self.deployment_state.get("postgres_configured"):
            self.print_status("PostgreSQL not configured, configuring now...", "info")
            postgres_success = self.configure_postgres()
            if not postgres_success:
                self.print_status("PostgreSQL configuration failed, will retry next cycle", "warning")
        else:
            # Quick check if PostgreSQL is still configured
            try:
                from postgres_configurator import PostgresConfigurator
                with PostgresConfigurator() as pg:
                    is_configured, status = pg.is_replication_configured()
                    if is_configured:
                        self.print_status("PostgreSQL replication: ✅ Configured", "success")
                    else:
                        self.print_status(f"PostgreSQL replication: ❌ {status}", "warning")
                        self.deployment_state["postgres_configured"] = False
            except Exception as e:
                self.print_status(f"Could not check PostgreSQL status: {e}", "warning")

        # Step 3: Check and deploy supervisor
        if not self.deployment_state.get("supervisor_deployed"):
            self.print_status("Supervisor not deployed, deploying now...", "info")
            supervisor_success = self.deploy_supervisor()
            if not supervisor_success:
                self.print_status("Supervisor deployment failed, will retry next cycle", "warning")
        else:
            # Quick health check of supervisor
            try:
                deployment_info = self.do_manager.get_deployment_info()
                if deployment_info.get("deployed"):
                    ip_address = deployment_info.get("ip_address")
                    if ip_address:
                        # Quick health check
                        import requests
                        try:
                            response = requests.get(f"http://{ip_address}:8020/health", timeout=10)
                            if response.status_code == 200:
                                self.print_status(f"Supervisor health: ✅ Healthy at {ip_address}:8020", "success")
                            else:
                                self.print_status(f"Supervisor health: ⚠️ Unhealthy (HTTP {response.status_code})", "warning")
                        except Exception as e:
                            self.print_status(f"Supervisor health: ⚠️ Unreachable ({e})", "warning")
                    else:
                        self.print_status("Supervisor: ⚠️ No IP address", "warning")
                else:
                    self.print_status("Supervisor: ❌ Not deployed", "warning")
                    self.deployment_state["supervisor_deployed"] = False
            except Exception as e:
                self.print_status(f"Could not check supervisor status: {e}", "warning")

        # Check if everything is healthy
        is_fully_healthy = (
            self.deployment_state.get("config_extracted") and
            self.deployment_state.get("postgres_configured") and
            self.deployment_state.get("supervisor_deployed")
        )

        if is_fully_healthy:
            self.consecutive_healthy_cycles += 1
            self.print_status(f"✅ System fully healthy (cycle {self.consecutive_healthy_cycles}/{Config.HEALTHY_CYCLES_BEFORE_DISABLE})", "success")

            # Check for auto-disable
            if Config.AUTO_DISABLE and self.consecutive_healthy_cycles >= Config.HEALTHY_CYCLES_BEFORE_DISABLE:
                self.print_status("🎉 Everything is working perfectly!", "success")
                self.print_status(f"Auto-disabling monitoring after {self.consecutive_healthy_cycles} healthy cycles", "info")
                self.print_status("To re-enable, set IS_ACTIVE=true", "info")
                self.is_disabled = True
        else:
            # Reset counter if not healthy
            self.consecutive_healthy_cycles = 0

        self.print_status("=== Monitoring cycle completed ===", "success")


def main():
    """Main entry point"""
    controller = OpsController()

    try:
        # Run continuous monitoring loop
        controller.run_monitoring_loop()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
