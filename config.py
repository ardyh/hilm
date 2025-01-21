import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class SnowflakeConfig:
    account: str
    user: str
    password: str
    warehouse: str
    role: str
    database: str
    schema: str

@dataclass
class AppConfig:
    snowflake: SnowflakeConfig
    environment: str = "development"

def load_config() -> AppConfig:
    """Load configuration based on environment"""
    # Load Snowflake configuration from environment variables
    load_dotenv()
    snowflake_config = SnowflakeConfig(
        account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
        user=os.getenv("SNOWFLAKE_USER", ""),
        password=os.getenv("SNOWFLAKE_PASSWORD", ""),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        database=os.getenv("SNOWFLAKE_DATABASE", "CC_QUICKSTART_CORTEX_SEARCH_DOCS"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "DATA")
    )

    return AppConfig(
        snowflake=snowflake_config,
        environment=os.getenv("ENVIRONMENT", "development")
    ) 