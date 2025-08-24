from typing import Optional, Dict, Any, List, Tuple

from twisted.internet import defer
from twisted.enterprise.adbapi import ConnectionPool


class ConfigurationRepository:

    def __init__(self, db_pool: ConnectionPool) -> None:
        self.db_pool: ConnectionPool = db_pool

    @defer.inlineCallbacks
    def save(self, service: str, version: Optional[int], payload_json: str) -> defer.Deferred[Dict[str, Any]]:
        def _save_config(txn: Any) -> Dict[str, Any]:
            if version is None:
                txn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM configurations WHERE service = %s",
                    (service,)
                )
                next_version: int = txn.fetchone()[0]
            else:
                next_version: int = version

            txn.execute(
                """INSERT INTO configurations (service, version, payload, created_at) 
                   VALUES (%s, %s, %s, NOW()) RETURNING id, created_at""",
                (service, next_version, payload_json)  # Принимаем уже готовый JSON
            )
            result: Tuple[Any, ...] = txn.fetchone()
            return {
                'id': result[0],
                'service': service,
                'version': next_version,
                'created_at': result[1]
            }

        try:
            result: Dict[str, Any] = yield self.db_pool.runInteraction(_save_config)
            defer.returnValue(result)
        except Exception as e:
            if 'duplicate key' in str(e):
                raise ValueError(f"Version {version} already exists for service {service}")
            raise e

    @defer.inlineCallbacks
    def get(self, service: str, version: Optional[int] = None) -> defer.Deferred[Optional[Dict[str, Any]]]:
        if version:
            sql: str = """
                SELECT id, service, version, payload, created_at 
                FROM configurations 
                WHERE service = %s AND version = %s
            """
            params: Tuple[str, int] = (service, version)
        else:
            sql: str = """
                SELECT id, service, version, payload, created_at 
                FROM configurations 
                WHERE service = %s 
                ORDER BY version DESC 
                LIMIT 1
            """
            params: Tuple[str, ...] = (service,)

        result: List[Tuple[Any, ...]] = yield self.db_pool.runQuery(sql, params)

        if not result:
            defer.returnValue(None)

        row: Tuple[Any, ...] = result[0]
        config: Dict[str, Any] = {
            'id': row[0],
            'service': row[1],
            'version': row[2],
            'payload': row[3],
            'created_at': row[4]
        }
        defer.returnValue(config)

    @defer.inlineCallbacks
    def get_history(self, service: str, limit: int = 10) -> defer.Deferred[Optional[List[Dict[str, Any]]]]:
        sql: str = """
            SELECT version, created_at 
            FROM configurations 
            WHERE service = %s 
            ORDER BY version DESC 
            LIMIT %s
        """
        result: List[Tuple[Any, ...]] = yield self.db_pool.runQuery(sql, (service, limit))

        history: List[Dict[str, Any]] = [
            {
                'version': row[0],
                'created_at': row[1]  # Сериализацию даты делаем в сервисе
            }
            for row in result
        ]
        defer.returnValue(history)
