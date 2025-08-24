import re
import yaml
from typing import Tuple, List, Dict, Any, Union, Optional
from jsonschema import validate, ValidationError


class ConfigValidator:

    CONFIG_SCHEMA = {
        "type": "object",
        "required": ["database"],
        "properties": {
            "version": {"type": "integer", "minimum": 1},
            "database": {
                "type": "object",
                "required": ["host", "port"],
                "properties": {
                    "host": {"type": "string", "minLength": 1},
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535}
                }
            }
        },
        "additionalProperties": True
    }

    @staticmethod
    def validate_yaml(yaml_content: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
        try:
            data: Any = yaml.safe_load(yaml_content)
            if data is None:
                return False, "Empty YAML content"
            return True, data
        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {str(e)}"

    @staticmethod
    def validate_config_structure(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        try:
            validate(instance=data, schema=ConfigValidator.CONFIG_SCHEMA)
            return True, []
        except ValidationError as e:
            errors: List[str] = []
            errors.append(f"Validation error: {e.message}")

            if e.absolute_path:
                path: str = ".".join(str(p) for p in e.absolute_path)
                errors.append(f"Error path: {path}")

            return False, errors

    @staticmethod
    def validate_service_name(service_name: str) -> Tuple[bool, str]:
        if not service_name:
            return False, "Service name cannot be empty"

        if len(service_name) > 100:
            return False, "Service name too long (max 100 characters)"

        if not re.match(r'^[a-zA-Z0-9_-]+$', service_name):
            return False, "Service name can only contain letters, numbers, underscores and hyphens"

        return True, ""

    @staticmethod
    def extract_version_from_config(config_data: Dict[str, Any]) -> Optional[int]:
        if isinstance(config_data, dict) and 'version' in config_data:
            version: Any = config_data['version']
            if isinstance(version, int) and version > 0:
                return version
        return None

    @staticmethod
    def validate_config_size(config_data: Dict[str, Any], max_size: int = 1024 * 1024) -> Tuple[bool, str]:
        try:
            config_str: str = str(config_data)
            if len(config_str.encode('utf-8')) > max_size:
                return False, f"Configuration too large (max {max_size} bytes)"
            return True, ""
        except Exception as e:
            return False, f"Error validating config size: {str(e)}"

    @staticmethod
    def get_validation_summary(config_data: Dict[str, Any]) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }

        struct_valid, struct_errors = ConfigValidator.validate_config_structure(config_data)
        if not struct_valid:
            summary['errors'].extend(struct_errors)
        else:
            summary['valid'] = True

        summary['metadata'] = {
            'version': config_data.get('version'),
            'keys_count': len(config_data.keys()),
            'has_database_config': 'database' in config_data,
            'has_custom_fields': len([k for k in config_data.keys() if k not in ['version', 'database']]) > 0
        }

        return summary
