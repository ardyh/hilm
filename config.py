import streamlit as st
from dataclasses import dataclass
from typing import Optional

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
    """Load configuration from Streamlit secrets"""
    try:
        # Get Snowflake configuration from secrets.toml
        snowflake_config = SnowflakeConfig(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            role=st.secrets["snowflake"]["role"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )

        return AppConfig(
            snowflake=snowflake_config,
            environment=st.secrets.get("environment", "development")
        )
    except Exception as e:
        st.error(f"Failed to load configuration: {str(e)}")
        st.info("Please ensure your .streamlit/secrets.toml file is properly configured")
        raise 