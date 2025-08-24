from typing import Optional, Any

from twisted.python import log
from twisted.internet import defer
from twisted.enterprise import adbapi
from twisted.enterprise.adbapi import ConnectionPool

from src.config.settings import settings


class DatabaseManager:

    def __init__(self) -> None:
        self.pool: Optional[ConnectionPool] = None
        self._connected: bool = False

    def connect(self) -> ConnectionPool:
        if self._connected:
            return self.pool

        try:
            settings.validate()

            self.pool = adbapi.ConnectionPool(
                'psycopg2',
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                cp_min=settings.DB_POOL_MIN,
                cp_max=settings.DB_POOL_MAX,
                cp_reconnect=True,
                cp_noisy=False
            )

            self._connected = True
            log.msg(
                f"Database pool initialized: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

            return self.pool

        except Exception as e:
            log.err(f"Failed to initialize database pool: {str(e)}")
            raise

    @defer.inlineCallbacks
    def test_connection(self) -> defer.Deferred[bool]:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        try:
            result: list[tuple[Any, ...]] = yield self.pool.runQuery("SELECT 1")
            log.msg("Database connection test successful")
            defer.returnValue(True)
        except Exception as e:
            log.err(f"Database connection test failed: {str(e)}")
            raise

    @defer.inlineCallbacks
    def close(self) -> defer.Deferred[None]:
        if self.pool and self._connected:
            yield self.pool.close()
            self.pool = None
            self._connected = False
            log.msg("Database connection pool closed")

db_manager = DatabaseManager()
