import json
from twisted.python import log
from twisted.internet import defer
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET

from src.validators.api_validator import APIValidator
from src.services.configuration_service import ConfigService


class BaseHandler(Resource):
    def __init__(self, db_pool):
        Resource.__init__(self)
        self.config_service = ConfigService(db_pool)

    def send_json(self, request, data, status=200):
        request.setResponseCode(status)
        request.setHeader(b'Content-Type', b'application/json')
        response = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
        request.write(response)
        request.finish()

    def send_error(self, request, message, status=400):
        self.send_json(request, {'error': message}, status)

    def get_query_param(self, request, name):
        args = request.args
        if name.encode() in args:
            return args[name.encode()][0].decode('utf-8')
        return None

    def handle_error(self, failure, request):
        log.err(failure)
        if not request.finished:
            self.send_error(request, "Internal server error", 500)


class ConfigHandler(BaseHandler):
    def getChild(self, path, request):
        if path:
            return ServiceHandler(self.config_service, path.decode('utf-8'))
        self.send_error(request, "Service name is required")
        return self

    def render_GET(self, request):
        return b''


class ServiceHandler(BaseHandler):
    def __init__(self, config_service, service_name):
        Resource.__init__(self)
        self.config_service = config_service
        self.service_name = service_name

    def getChild(self, path, request):
        if path == b'history':
            return HistoryHandler(self.config_service, self.service_name)
        return Resource.getChild(self, path, request)

    def render_POST(self, request):
        d = self._save_config(request)
        d.addErrback(self.handle_error, request)
        return NOT_DONE_YET

    @defer.inlineCallbacks
    def _save_config(self, request):
        try:
            content = request.content.read()
            if not content:
                self.send_error(request, "Request body is required", 400)
                return

            valid, error = APIValidator.validate_content_length(content)
            if not valid:
                self.send_error(request, error, 413)
                return

            yaml_content = content.decode('utf-8')
            result = yield self.config_service.save_config(self.service_name, yaml_content)
            self.send_json(request, result, 201)

        except ValueError as e:
            error_msg = str(e)
            if "already exists" in error_msg:
                status = 409
            elif "validation failed" in error_msg.lower():
                status = 422
            else:
                status = 400
            self.send_error(request, error_msg, status)

        except Exception as e:
            log.err(f"Error saving config for {self.service_name}: {e}")
            self.send_error(request, "Internal server error", 500)

    def render_GET(self, request):
        d = self._get_config(request)
        d.addErrback(self.handle_error, request)
        return NOT_DONE_YET

    @defer.inlineCallbacks
    def _get_config(self, request):
        try:
            version_param = self.get_query_param(request, 'version')
            template_param = self.get_query_param(request, 'template')

            version = None
            if version_param:
                valid, result = APIValidator.validate_version_param(version_param)
                if not valid:
                    self.send_error(request, result, 400)
                    return
                version = result

            use_template = APIValidator.validate_template_param(template_param)

            template_vars = {}
            if use_template:
                try:
                    content = request.content.read()
                    if content:
                        template_vars = json.loads(content.decode('utf-8'))
                        if not isinstance(template_vars, dict):
                            template_vars = {}
                except (json.JSONDecodeError, UnicodeDecodeError):
                    template_vars = {}

            config = yield self.config_service.get_config(
                self.service_name, version, use_template, template_vars
            )

            if config is None:
                self.send_error(request, "Configuration not found", 404)
                return

            self.send_json(request, config)

        except ValueError as e:
            self.send_error(request, str(e), 400)
        except Exception as e:
            log.err(f"Error getting config for {self.service_name}: {e}")
            self.send_error(request, "Internal server error", 500)


class HistoryHandler(BaseHandler):

    def __init__(self, config_service, service_name):
        Resource.__init__(self)
        self.config_service = config_service
        self.service_name = service_name

    def render_GET(self, request):
        d = self._get_history(request)
        d.addErrback(self.handle_error, request)
        return NOT_DONE_YET

    @defer.inlineCallbacks
    def _get_history(self, request):
        try:
            history = yield self.config_service.get_config_history(self.service_name)

            if history is None:
                self.send_error(request, "Service not found", 404)
                return

            self.send_json(request, history)

        except ValueError as e:
            self.send_error(request, str(e), 400)
        except Exception as e:
            log.err(f"Error getting history for {self.service_name}: {e}")
            self.send_error(request, "Internal server error", 500)