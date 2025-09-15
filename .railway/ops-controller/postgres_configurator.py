"""PostgreSQL Configurator for logical replication setup"""
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
from typing import Optional, Tuple
from config import Config


class PostgresConfigurator:
    """Configure PostgreSQL for logical replication"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.connection = None
        self.cursor = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Parse database URL
            parsed = urlparse(self.database_url)

            self.connection = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading /
                user=parsed.username,
                password=parsed.password
            )
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def check_wal_level(self) -> str:
        """Check current WAL level"""
        try:
            self.cursor.execute("SHOW wal_level;")
            result = self.cursor.fetchone()
            return result[0] if result else "unknown"
        except Exception as e:
            print(f"❌ Failed to check WAL level: {e}")
            return "unknown"

    def set_wal_level_logical(self) -> bool:
        """Set WAL level to logical"""
        try:
            # This requires superuser privileges
            self.cursor.execute("ALTER SYSTEM SET wal_level = 'logical';")
            print("✅ Set WAL level to logical (restart required)")
            return True
        except Exception as e:
            print(f"⚠️ Failed to set WAL level: {e}")
            # Try alternative approach for managed databases
            print("   Note: Managed databases may need manual configuration")
            return False

    def check_replica_identity(self, table: str = "TaskRun") -> str:
        """Check replica identity for a table"""
        try:
            query = """
            SELECT relreplident
            FROM pg_class
            WHERE relname = %s AND relnamespace = (
                SELECT oid FROM pg_namespace WHERE nspname = 'public'
            );
            """
            self.cursor.execute(query, (table,))
            result = self.cursor.fetchone()

            if result:
                identity_map = {
                    'd': 'default',
                    'n': 'nothing',
                    'f': 'full',
                    'i': 'index'
                }
                return identity_map.get(result[0], 'unknown')
            return "not_found"
        except Exception as e:
            print(f"❌ Failed to check replica identity: {e}")
            return "error"

    def set_replica_identity_full(self, table: str = "TaskRun") -> bool:
        """Set replica identity to FULL for a table"""
        try:
            query = sql.SQL("ALTER TABLE public.{} REPLICA IDENTITY FULL;").format(
                sql.Identifier(table)
            )
            self.cursor.execute(query)
            print(f"✅ Set replica identity FULL for table: {table}")
            return True
        except Exception as e:
            print(f"❌ Failed to set replica identity: {e}")
            return False

    def check_publication_exists(self, publication_name: str = "task_runs_to_clickhouse_v1_publication") -> bool:
        """Check if publication exists"""
        try:
            query = "SELECT * FROM pg_publication WHERE pubname = %s;"
            self.cursor.execute(query, (publication_name,))
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"❌ Failed to check publication: {e}")
            return False

    def create_publication(self, table: str = "TaskRun",
                         publication_name: str = "task_runs_to_clickhouse_v1_publication") -> bool:
        """Create publication for table"""
        try:
            query = sql.SQL("CREATE PUBLICATION {} FOR TABLE public.{};").format(
                sql.Identifier(publication_name),
                sql.Identifier(table)
            )
            self.cursor.execute(query)
            print(f"✅ Created publication: {publication_name}")
            return True
        except Exception as e:
            if "already exists" in str(e):
                print(f"ℹ️ Publication already exists: {publication_name}")
                return True
            print(f"❌ Failed to create publication: {e}")
            return False

    def is_replication_configured(self) -> Tuple[bool, str]:
        """Check if logical replication is fully configured"""
        issues = []

        # Check WAL level
        wal_level = self.check_wal_level()
        if wal_level != "logical":
            issues.append(f"WAL level is '{wal_level}', needs to be 'logical'")

        # Check replica identity
        replica_identity = self.check_replica_identity()
        if replica_identity != "full":
            issues.append(f"Replica identity is '{replica_identity}', needs to be 'full'")

        # Check publication
        if not self.check_publication_exists():
            issues.append("Publication does not exist")

        if issues:
            return False, "; ".join(issues)

        return True, "Replication is fully configured"

    def configure_replication(self, restart_required_callback=None) -> bool:
        """Configure PostgreSQL for logical replication"""
        print("🔧 Configuring PostgreSQL for logical replication...")

        # Check current status
        is_configured, status = self.is_replication_configured()
        if is_configured:
            print(f"✅ {status}")
            return True

        print(f"ℹ️ Current status: {status}")

        # Step 1: Check and set WAL level
        wal_level = self.check_wal_level()
        print(f"📊 Current WAL level: {wal_level}")

        restart_needed = False
        if wal_level != "logical":
            if self.set_wal_level_logical():
                restart_needed = True
            else:
                print("⚠️ Could not set WAL level automatically")
                print("   Please set it manually in your database configuration")
                return False

        # Step 2: Set replica identity
        replica_identity = self.check_replica_identity()
        print(f"📊 Current replica identity: {replica_identity}")

        if replica_identity != "full":
            if not self.set_replica_identity_full():
                print("⚠️ Could not set replica identity")
                return False

        # Step 3: Create publication
        if not self.check_publication_exists():
            if not self.create_publication():
                print("⚠️ Could not create publication")
                return False

        # Step 4: Handle restart if needed
        if restart_needed and restart_required_callback:
            print("🔄 PostgreSQL restart required for WAL level change")
            restart_required_callback()

        # Final verification
        is_configured, status = self.is_replication_configured()
        if is_configured:
            print(f"✅ {status}")
            return True
        else:
            print(f"⚠️ Configuration incomplete: {status}")
            return False

    def verify_configuration(self) -> bool:
        """Verify that logical replication is properly configured"""
        print("🔍 Verifying PostgreSQL configuration...")

        # Check WAL level
        wal_level = self.check_wal_level()
        print(f"  WAL level: {wal_level} {'✅' if wal_level == 'logical' else '❌'}")

        # Check replica identity
        replica_identity = self.check_replica_identity()
        print(f"  Replica identity: {replica_identity} {'✅' if replica_identity == 'full' else '❌'}")

        # Check publication
        has_publication = self.check_publication_exists()
        print(f"  Publication exists: {'✅' if has_publication else '❌'}")

        # Overall status
        is_configured, status = self.is_replication_configured()
        print(f"\n  Overall: {status}")

        return is_configured


if __name__ == "__main__":
    # Test the configurator
    import os

    if not os.getenv("DATABASE_URL"):
        print("Please set DATABASE_URL environment variable")
        exit(1)

    with PostgresConfigurator() as pg:
        # Check current configuration
        pg.verify_configuration()

        # Configure if needed
        pg.configure_replication()
