import streamlit as st
import time
import json
from snowflake.snowpark import Session
from snowflake.core import Root
from ..config.snowflake_config import get_snowflake_config, CORTEX_SEARCH_SERVICE_CONSULTING, CORTEX_SEARCH_SERVICE_WEBPAGES, COLUMNS, NUM_CHUNKS, NUM_CHUNKS_WEBPAGES

# Global variables for Snowflake services
consulting_svc = None
webpages_svc = None
snowflake_session = None  # Add global session variable

def init_snowflake_session():
    """Initialize Snowflake session and services based on environment"""
    try:
        global consulting_svc, webpages_svc, snowflake_session
        
        # Create new session if not exists
        if not snowflake_session:
            snowflake_session = Session.builder.configs(get_snowflake_config()).create()
        
        # Initialize Root
        root = Root(snowflake_session)
        db = root.databases[get_snowflake_config()['database']]
        schema = db.schemas[get_snowflake_config()['schema']]
        
        # Initialize both Cortex Search services
        consulting_svc = schema.cortex_search_services[CORTEX_SEARCH_SERVICE_CONSULTING]
        webpages_svc = schema.cortex_search_services[CORTEX_SEARCH_SERVICE_WEBPAGES]
        
        return snowflake_session
    except Exception as e:
        st.error(f"Failed to initialize Snowflake session: {str(e)}")
        return None


def get_similar_cases(query: str) -> dict:
    """Retrieve similar business cases from Snowflake using consulting service"""
    try:
        if not consulting_svc:
            st.error("Snowflake consulting service not initialized")
            return None
            
        if st.session_state.get('category_value', "ALL") == "ALL":
            response = consulting_svc.search(query, COLUMNS, limit=NUM_CHUNKS)
        else:
            filter_obj = {"@eq": {"category": st.session_state.category_value}}
            response = consulting_svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS)
        
        raw_json = response.model_dump_json()
        search_results = json.loads(raw_json)
        similar_cases = {"results": []}
        
        if not search_results or "results" not in search_results:
            return similar_cases
        
        unique_paths = set([result["relative_path"] for result in search_results["results"]])
        
        for path in unique_paths:
            doc_query = f"""
            SELECT LISTAGG(CHUNK, '\n\n') as FULL_DOCUMENT
            FROM CC_QUICKSTART_CORTEX_SEARCH_DOCS.DATA.DOCS_CHUNKS_TABLE_CONSULTING
            WHERE RELATIVE_PATH = '{path}'
            GROUP BY RELATIVE_PATH
            """
            
            result = snowflake_session.sql(doc_query).collect()
            doc_result = result[0] if result else None
            
            if doc_result:
                similar_cases["results"].append({
                    "relative_path": path,
                    "content": doc_result["FULL_DOCUMENT"],
                })

        return similar_cases
            
    except Exception as e:
        st.write(f"Error in get_similar_cases: {str(e)}")
        return None

def get_webpages_data(query: str) -> dict:
    """Get similar chunks from webpages search service for data collection"""
    try:
        if not webpages_svc:
            st.error("Snowflake webpages service not initialized")
            return None
            
        if st.session_state.get('category_value', "ALL") == "ALL":
            response = webpages_svc.search(query, COLUMNS, limit=NUM_CHUNKS_WEBPAGES)
        else:
            filter_obj = {"@eq": {"category": st.session_state.category_value}}
            response = webpages_svc.search(query, COLUMNS, filter=filter_obj, limit=NUM_CHUNKS_WEBPAGES)
        
        return response.json()
    except Exception as e:
        st.error(f"Error retrieving chunks: {str(e)}")
        return None

def get_llm_response(session, prompt: str, temperature: float = 0.7, stream: bool = True):
    """Get response from Snowflake's LLM with optional RAG"""
    try:
        cmd = "select snowflake.cortex.complete(?, ?) as response"
        df_response = session.sql(cmd, params=[st.session_state.model_name, prompt]).collect()
        
        if stream:
            return stream_response(df_response[0].RESPONSE)
        return df_response[0].RESPONSE
            
    except Exception as e:
        st.error(f"Error getting LLM response: {str(e)}")
        return None

def stream_response(response: str):
    """Stream the response with visual effect"""
    placeholder = st.empty()
    words = response.split()
    current_response = ""
    
    # Stream the response first
    for word in words:
        current_response += word + " "
        formatted_response = f"""
        <div style="font-size: 1rem; line-height: 1.5;">
        {current_response}▌
        </div>
        <br>
        """
        placeholder.markdown(formatted_response, unsafe_allow_html=True)
        time.sleep(0.01)
    
    # Clear the streaming placeholder
    placeholder.empty()
    
    # Return the response without displaying it again
    return response 