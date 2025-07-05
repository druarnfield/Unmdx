"""
Configuration for the UnMDX MCP Server.
"""

import os
from pathlib import Path
from typing import Optional


class ServerConfig:
    """Configuration class for the UnMDX MCP Server."""
    
    def __init__(self):
        """Initialize configuration with defaults and environment overrides."""
        self.db_path = self._get_db_path()
        self.log_level = os.getenv("UNMDX_LOG_LEVEL", "INFO")
        self.log_file = os.getenv("UNMDX_LOG_FILE")
        self.server_name = os.getenv("UNMDX_SERVER_NAME", "unmdx-tracker")
        self.server_version = os.getenv("UNMDX_SERVER_VERSION", "0.1.0")
        self.development_mode = os.getenv("UNMDX_DEVELOPMENT", "false").lower() == "true"
    
    def _get_db_path(self) -> str:
        """Get database path from environment or use default."""
        db_path = os.getenv("UNMDX_DB_PATH")
        if db_path:
            return db_path
        
        # Default to current directory
        return "unmdx_tracking.db"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.development_mode
    
    def get_log_config(self) -> dict:
        """Get logging configuration."""
        config = {
            "level": self.log_level,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
        
        if self.log_file:
            config["filename"] = self.log_file
        
        return config
    
    def validate(self) -> None:
        """Validate configuration."""
        # Ensure database directory exists
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"""ServerConfig(
    db_path='{self.db_path}',
    log_level='{self.log_level}',
    log_file='{self.log_file}',
    server_name='{self.server_name}',
    server_version='{self.server_version}',
    development_mode={self.development_mode}
)"""


# Global config instance
config = ServerConfig()