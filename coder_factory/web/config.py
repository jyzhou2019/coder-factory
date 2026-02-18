"""
Web Interface Configuration
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


@dataclass
class WebConfig:
    """Web interface configuration"""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Paths
    workspace_dir: Path = Path("./workspace")
    data_dir: Path = Path("./data")
    static_dir: Path = Path("./coder_factory/web/static")

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/coder_factory.db"

    # WebSocket
    websocket_heartbeat: int = 30  # seconds

    @classmethod
    def from_env(cls) -> "WebConfig":
        """Create config from environment variables"""
        return cls(
            host=os.getenv("WEB_HOST", "0.0.0.0"),
            port=int(os.getenv("WEB_PORT", "8000")),
            debug=os.getenv("WEB_DEBUG", "false").lower() == "true",
            workspace_dir=Path(os.getenv("WORKSPACE_DIR", "./workspace")),
            data_dir=Path(os.getenv("DATA_DIR", "./data")),
            database_url=os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./data/coder_factory.db"
            ),
        )

    def ensure_dirs(self):
        """Ensure required directories exist"""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = WebConfig.from_env()
