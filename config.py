import os
import argparse
import sqlite3
from typing import Optional
from dataclasses import dataclass


@dataclass
class BotConfig:
    """Configuration class for Marcie Discord bot."""
    
    # Required fields (no defaults) - must be provided
    api_base_url: str
    api_key: str
    discord_token: str
    
    # Fields with defaults - required for operation but have sensible defaults
    database_path: str = 'marcie.db'   # SQLite database file path
    first_run: bool = True             # Bot startup state flag
    
    @property
    def api_complete_url(self) -> str:
        """Complete API URL with authentication."""
        return f"{self.api_base_url}?api_key={self.api_key}"
    
    def get_database_connection(self) -> sqlite3.Connection:
        """Get a SQLite database connection."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def initialize_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with self.get_database_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    guildid INTEGER PRIMARY KEY,
                    prefix TEXT NOT NULL DEFAULT '?',
                    name TEXT NOT NULL
                )
            ''')
    
    @classmethod
    def from_args_and_env(cls) -> 'BotConfig':
        """Create configuration from command line arguments and environment variables.
        
        Environment variables take precedence over command line arguments for secrets.
        """
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Run Marcie Discord bot')
        parser.add_argument('-d', '--db', type=str, help='SQLite database file path', 
                          default=os.getenv('MARCIE_DB_PATH', 'marcie.db'))
        parser.add_argument('-a', '--api', type=str, help='Card API address Ex: http://dev.tawa.wtf:8000',
                          default=os.getenv('MARCIE_API_URL'))
        parser.add_argument('-t', '--token', type=str, help='Discord bot token',
                          default=os.getenv('MARCIE_DISCORD_TOKEN'))
        parser.add_argument('-k', '--key', type=str, help='Card API key',
                          default=os.getenv('MARCIE_API_KEY'))
        
        args = parser.parse_args()
        
        # Validate required configuration
        if not args.api:
            raise ValueError("API URL is required. Provide via --api or MARCIE_API_URL environment variable.")
        if not args.token:
            raise ValueError("Discord token is required. Provide via --token or MARCIE_DISCORD_TOKEN environment variable.")
        if not args.key:
            raise ValueError("API key is required. Provide via --key or MARCIE_API_KEY environment variable.")
        
        # Create config instance
        config = cls(
            api_base_url=args.api,
            api_key=args.key,
            discord_token=args.token,
            database_path=args.db
        )
        
        # Initialize database
        config.initialize_database()
        
        return config
    
    def close_database_connection(self) -> None:
        """Close database connections (SQLite auto-closes with context managers)."""
        pass  # SQLite connections are auto-closed when using 'with' statements


# Global configuration instance
config: Optional[BotConfig] = None


def get_config() -> BotConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = BotConfig.from_args_and_env()
    return config


def initialize_config() -> BotConfig:
    """Initialize and return the global configuration."""
    global config
    config = BotConfig.from_args_and_env()
    return config