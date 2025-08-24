import os

from twisted.python import log
from twisted.internet import defer


class MigrationManager:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'migrations'
        )

    @defer.inlineCallbacks
    def init_migrations_table(self):
        sql = '''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT NOW()
            )
        '''
        yield self.db_pool.runOperation(sql)
        log.msg("Migrations table initialized")

    @defer.inlineCallbacks
    def is_migration_applied(self, version):
        result = yield self.db_pool.runQuery(
            "SELECT version FROM schema_migrations WHERE version = %s",
            (version,)
        )
        defer.returnValue(len(result) > 0)

    @defer.inlineCallbacks
    def apply_migration(self, version, sql_file_path):
        def _apply_in_transaction(txn):
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement and not statement.startswith('--'):
                    txn.execute(statement)

            txn.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,)
            )

        is_applied = yield self.is_migration_applied(version)
        if not is_applied:
            yield self.db_pool.runInteraction(_apply_in_transaction)
            log.msg(f"Applied migration: {version}")
        else:
            log.msg(f"Migration {version} already applied")

    @defer.inlineCallbacks
    def create_initial_schema(self):
        schema_sql = '''
        CREATE TABLE IF NOT EXISTS configurations (
            id SERIAL PRIMARY KEY,
            service VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL,
            payload JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(service, version)
        );

        CREATE INDEX IF NOT EXISTS idx_configurations_service ON configurations(service);
        CREATE INDEX IF NOT EXISTS idx_configurations_service_version ON configurations(service, version);
        CREATE INDEX IF NOT EXISTS idx_configurations_created_at ON configurations(created_at);
        '''

        is_applied = yield self.is_migration_applied('000_initial_schema')
        if not is_applied:
            def _apply_schema(txn):
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        txn.execute(statement)
                txn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    ('000_initial_schema',)
                )

            yield self.db_pool.runInteraction(_apply_schema)
            log.msg("Created initial database schema")
        else:
            log.msg("Initial schema already exists")

    @defer.inlineCallbacks
    def run_all_migrations(self):
        yield self.init_migrations_table()

        yield self.create_initial_schema()

        if os.path.exists(self.migrations_dir):
            migration_files = sorted([
                f for f in os.listdir(self.migrations_dir)
                if f.endswith('.sql')
            ])

            for migration_file in migration_files:
                version = migration_file.replace('.sql', '')
                file_path = os.path.join(self.migrations_dir, migration_file)
                yield self.apply_migration(version, file_path)
        else:
            log.msg(f"Migrations directory not found: {self.migrations_dir}")

        log.msg("All migrations completed")
