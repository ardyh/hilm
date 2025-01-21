from config import load_config

# Load configuration
config = load_config()

# Snowflake Configuration Constants
CORTEX_SEARCH_DATABASE = "CC_QUICKSTART_CORTEX_SEARCH_DOCS"
CORTEX_SEARCH_SCHEMA = "DATA"
CORTEX_SEARCH_SERVICE_CONSULTING = "CC_SEARCH_SERVICE_CS_CONSULTING"
CORTEX_SEARCH_SERVICE_WEBPAGES = "CC_SEARCH_SERVICE_CS_WEBPAGES"
NUM_CHUNKS = 2
NUM_CHUNKS_WEBPAGES = 7
COLUMNS = ["chunk", "relative_path", "category"]
MODEL_NAME = "mistral-large2"
ADVANCED_FEATURES = False

def get_snowflake_config():
    return {
        "account": config.snowflake.account,
        "user": config.snowflake.user,
        "password": config.snowflake.password,
        "warehouse": config.snowflake.warehouse,
        "role": config.snowflake.role,
        "database": config.snowflake.database,
        "schema": config.snowflake.schema
    } 