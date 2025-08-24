import json

from twisted.python import log
from twisted.internet import defer
from typing import Optional, Dict, Any, List

from src.services.template_service import TemplateService
from src.validators.config_validator import ConfigValidator
from src.repositories.configuration_repository import ConfigurationRepository


class ConfigService:

    def __init__(self, db_pool: Any) -> None:
        self.repository: ConfigurationRepository = ConfigurationRepository(db_pool)
        self.template_service: TemplateService = TemplateService()

    @defer.inlineCallbacks
    def save_config(self, service_name: str, yaml_content: str) -> defer.Deferred[Dict[str, Any]]:
        valid: bool
        error: str
        valid, error = ConfigValidator.validate_service_name(service_name)
        if not valid:
            raise ValueError(error)

        yaml_valid: bool
        yaml_result: Any
        yaml_valid, yaml_result = ConfigValidator.validate_yaml(yaml_content)
        if not yaml_valid:
            raise ValueError(yaml_result)

        config_data: Dict[str, Any] = yaml_result

        struct_valid: bool
        struct_errors: List[str]
        struct_valid, struct_errors = ConfigValidator.validate_config_structure(config_data)
        if not struct_valid:
            raise ValueError(f"Configuration validation failed: {'; '.join(struct_errors)}")

        config_version: Optional[int] = ConfigValidator.extract_version_from_config(config_data)

        try:
            payload_json: str = json.dumps(config_data)

            saved_config: Dict[str, Any] = yield self.repository.save(
                service=service_name,
                version=config_version,
                payload_json=payload_json
            )

            result: Dict[str, Any] = {
                'service': service_name,
                'version': saved_config['version'],
                'status': 'saved'
            }

            log.msg(f"Saved configuration for service '{service_name}', version {saved_config['version']}")
            defer.returnValue(result)

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            log.err(f"Error saving configuration: {str(e)}")
            raise Exception(f"Internal error saving configuration: {str(e)}")

    @defer.inlineCallbacks
    def get_config(self, service_name: str, version: Optional[int] = None, use_template: bool = False,
                   template_vars: Optional[Dict[str, Any]] = None) -> defer.Deferred[Optional[Dict[str, Any]]]:
        valid: bool
        error: str
        valid, error = ConfigValidator.validate_service_name(service_name)
        if not valid:
            raise ValueError(error)

        config: Optional[Dict[str, Any]] = yield self.repository.get(service_name, version)

        if not config:
            defer.returnValue(None)

        config_data: Dict[str, Any] = config['payload']

        if use_template:
            try:
                if template_vars is None:
                    template_vars = {}

                config_data = self.template_service.render_config(config_data, template_vars)
                log.msg(f"Applied template rendering for service '{service_name}', version {config['version']}")
            except ValueError as e:
                log.err(f"Template rendering error: {str(e)}")
                raise ValueError(f"Template rendering failed: {str(e)}")

        defer.returnValue(config_data)

    @defer.inlineCallbacks
    def get_config_history(self, service_name: str, limit: int = 10) -> defer.Deferred[Optional[List[Dict[str, Any]]]]:
        valid: bool
        error: str
        valid, error = ConfigValidator.validate_service_name(service_name)
        if not valid:
            raise ValueError(error)

        history: Optional[List[Dict[str, Any]]] = yield self.repository.get_history(service_name, limit)

        if history is None:
            defer.returnValue(None)

        formatted_history: List[Dict[str, Any]] = []
        for item in history:
            formatted_item: Dict[str, Any] = {
                'version': item['version'],
                'created_at': item['created_at'].isoformat() if item['created_at'] else None
            }
            formatted_history.append(formatted_item)

        defer.returnValue(formatted_history)
