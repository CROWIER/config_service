import os
from typing import ClassVar, List, Tuple, Any

from dotenv import load_dotenv

load_dotenv()


class Settings:
    POSTGRES_HOST: ClassVar[str] = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: ClassVar[int] = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: ClassVar[str] = os.getenv('POSTGRES_DB', 'config_db')
    POSTGRES_USER: ClassVar[str] = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: ClassVar[str] = os.getenv('POSTGRES_PASSWORD', '')  # Убран захардкоженный пароль

    DB_POOL_MIN: ClassVar[int] = int(os.getenv('DB_POOL_MIN', '2'))
    DB_POOL_MAX: ClassVar[int] = int(os.getenv('DB_POOL_MAX', '10'))

    HTTP_PORT: ClassVar[int] = int(os.getenv('PORT', '8080'))

    @classmethod
    def get_db_connection_string(cls) -> str:
        return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"

    @classmethod
    def validate(cls) -> bool:
        required_settings: List[Tuple[str, Any]] = [
            ('POSTGRES_HOST', cls.POSTGRES_HOST),
            ('POSTGRES_DB', cls.POSTGRES_DB),
            ('POSTGRES_USER', cls.POSTGRES_USER),
            ('POSTGRES_PASSWORD', cls.POSTGRES_PASSWORD),
        ]

        for name, value in required_settings:
            if not value:
                raise ValueError(f"Required setting {name} is not set")

        return True


settings = Settings()
