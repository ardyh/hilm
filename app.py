import streamlit as st
import base64
from pathlib import Path
from src.utils.snowflake_utils import init_snowflake_session
from src.handlers.stage_handlers import (
    handle_welcome_screen,
    handle_problem_definition,
    handle_data_collection,
    handle_analysis
)
from src.models.consulting_session import ConsultingSession
from src.config.snowflake_config import MODEL_NAME, ADVANCED_FEATURES
from src.config.business_config import BUSINESS_CONFIG

def get_base64_encoded_image(image_path):
    """Get base64 encoded image data"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def setup_page():
    """Setup page configuration and layout"""
    st.set_page_config(
        page_title="MyTea Business Consultant",
    )        
    
    # Get encoded logo
    try:
        root_dir = Path(__file__).parent
        logo_path = root_dir / "assets" / "hilm_logo5-removebg.png"
        
        if logo_path.exists():
            encoded_logo = get_base64_encoded_image(logo_path)
            
            # Custom CSS with updated logo styling
            st.markdown("""
                <style>
                /* Logo container */
                .logo-container {
                    position: fixed;
                    top: 0.25rem;
                    left: 0.25rem;
                    padding: 0.5rem;
                    background: white;
                    z-index: 9999;
                    border-radius: 7px;
                    min-width: 200px;  /* Ensure minimum width */
                    min-height: 160px;  /* Ensure minimum height */
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                /* Logo image specific styling */
                .logo-image {
                    display: block;
                    height: 120px;  /* Increased height */
                    width: auto;
                    object-fit: contain;
                }
                
                /* Main content padding */
                .block-container {
                    padding-top: 3rem;  /* Increased to accommodate larger logo */
                }
                
                /* Hide Streamlit's default menu button */
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                
                /* Ensure logo container is visible */
                div[data-testid="stAppViewContainer"] > div:first-child {
                    z-index: auto;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Add the logo container with more specific styling
            st.markdown(f"""
                <div class="logo-container">
                    <img class="logo-image" 
                         src="data:image/png;base64,{encoded_logo}" 
                         alt="HILM Logo"
                    >
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Logo file not found!")
        
        if st.session_state.get('advanced_features', False):
            with st.sidebar:
                st.session_state['advanced_features'] = st.checkbox(
                    "Enable Debug Mode", 
                    value=st.session_state.get('advanced_features', False)
                )
    except Exception as e:
        st.error(f"Error loading logo: {str(e)}")

def main():
    # Setup page configuration and logo
    setup_page()
    
    # Initialize Snowflake session
    st.session_state.model_name = MODEL_NAME
    # Debug mode config
    st.session_state['advanced_features'] = ADVANCED_FEATURES

    session = init_snowflake_session()
    if not session:
        st.error("Failed to initialize Snowflake connection")
        st.stop()
    
    # Initialize session state if not exists
    if 'consulting_session' not in st.session_state:
        st.session_state.consulting_session = ConsultingSession()
    
    # Handle different stages
    if st.session_state.consulting_session.stage == "welcome":
        handle_welcome_screen(session)
    elif st.session_state.consulting_session.stage == "problem_definition":
        handle_problem_definition(session)
    elif st.session_state.consulting_session.stage == "data_collection":
        handle_data_collection(session)
    elif st.session_state.consulting_session.stage == "analysis":
        handle_analysis(session)

if __name__ == "__main__":
    main() 