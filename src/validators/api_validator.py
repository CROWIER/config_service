from twisted.web.http import Request
from typing import Tuple, List, Optional, Any, Dict


class APIValidator:
    @staticmethod
    def validate_version_param(version_str: Optional[str]) -> Tuple[bool, Optional[int]]:
        if not version_str:
            return True, None

        try:
            version: int = int(version_str)
            if version < 1:
                return False, None
            return True, version
        except ValueError:
            return False, None

    @staticmethod
    def validate_template_param(template_str: Optional[str]) -> bool:
        if not template_str:
            return False

        return template_str.lower() in ('1', 'true', 'yes')

    @staticmethod
    def validate_content_length(content: bytes, max_size: int = 1024 * 1024) -> Tuple[bool, str]:
        if len(content) > max_size:
            return False, f"Content too large (max {max_size} bytes)"
        return True, ""

    @staticmethod
    def validate_content_type(request: Request, expected_types: List[str] = None) -> Tuple[bool, str]:
        if expected_types is None:
            expected_types = ['text/plain', 'application/x-yaml']
            
        content_type: Optional[bytes] = request.getHeader(b'content-type')
        if content_type:
            content_type_str: str = content_type.decode('utf-8').split(';')[0].strip()
            if content_type_str in expected_types:
                return True, ""
        return False, f"Invalid content type. Expected: {', '.join(expected_types)}"
