import json
from typing import Dict, Any, Optional, Union, List, Tuple
from jinja2 import Environment, BaseLoader, TemplateError, TemplateSyntaxError, StrictUndefined


class TemplateService:

    def __init__(self):
        self.jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=False,
            undefined=StrictUndefined
        )

    def render_config(self, config_data: Dict[str, Any], template_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if template_vars is None:
            template_vars = {}

        try:
            config_json: str = json.dumps(config_data, indent=2, ensure_ascii=False)

            if not self._has_template_syntax(config_json):
                return config_data

            template: Any = self.jinja_env.from_string(config_json)

            rendered_json: str = template.render(**template_vars)

            rendered_config: Dict[str, Any] = json.loads(rendered_json)

            return rendered_config

        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
        except TemplateError as e:
            raise ValueError(f"Template rendering error: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parsing error after template rendering: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error during template rendering: {str(e)}")

    def _has_template_syntax(self, text: str) -> bool:
        jinja_patterns: List[str] = ['{{', '}}', '{%', '%}', '{#', '#}']
        return any(pattern in text for pattern in jinja_patterns)
