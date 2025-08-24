from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Configuration:
    id: Optional[int] = None
    service: Optional[str] = None
    version: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"Configuration(service='{self.service}', version={self.version})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'service': self.service,
            'version': self.version,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
