#!/usr/bin/env python3
import os
import sys

from twisted.python import log
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, defer

src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_path)

from config.settings import settings
from api.handlers import ConfigHandler
from config.database import db_manager
from utils.migrations import MigrationManager


class HealthHandler(Resource):

    def render_GET(self, request):
        request.setHeader(b'Content-Type', b'application/json')
        return b'{"status": "healthy", "service": "config-service"}'


class ConfigServiceApp:
    def __init__(self):
        self.site = None

    @defer.inlineCallbacks
    def initialize(self):
        try:
            log.msg("Starting Configuration Service...")
            db_pool = db_manager.connect()
            yield db_manager.test_connection()
            log.msg("Database connected")

            migration_manager = MigrationManager(db_pool)
            yield migration_manager.run_all_migrations()
            log.msg("Migrations completed")

            root = Resource()

            config_handler = ConfigHandler(db_pool)

            root.putChild(b'config', config_handler)

            root.putChild(b'health', HealthHandler())

            self.site = Site(root)

            reactor.listenTCP(settings.HTTP_PORT, self.site)
            log.msg(f"Config service started on port {settings.HTTP_PORT}")

        except Exception as e:
            log.err(f"Failed to initialize application: {str(e)}")
            import traceback
            traceback.print_exc()
            reactor.stop()

    @defer.inlineCallbacks
    def shutdown(self):
        try:
            yield db_manager.close()
            log.msg("Application shutdown completed")
        except Exception as e:
            log.err(f"Error during shutdown: {str(e)}")


@defer.inlineCallbacks
def main():
    try:
        log.startLogging(sys.stdout)

        settings.validate()

        app = ConfigServiceApp()
        yield app.initialize()

        reactor.addSystemEventTrigger('before', 'shutdown', app.shutdown)

    except Exception as e:
        log.err(f"Failed to start application: {str(e)}")
        reactor.stop()


if __name__ == '__main__':
    reactor.callWhenRunning(main)
    reactor.run()
