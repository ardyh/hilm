import streamlit as st
import json
from ..utils.snowflake_utils import get_llm_response, get_similar_cases, get_webpages_data
from ..utils.prompt_utils import create_consulting_prompt, create_refinement_prompt, parse_markdown_sections, create_webpages_prompt
from ..utils.renderer_utils import render_task_card, render_query_section
from ..models.consulting_session import ConsultingSession
from ..config.business_config import BUSINESS_CONFIG, CONSULTING_SUGGESTIONS, TASK_CARDS
from typing import List, Dict
import re

def handle_welcome_screen(session):
    """Handle welcome screen display and interactions"""
    # Personal welcome header
    st.markdown(f"""
    <h1 style='font-size: 3rem; margin-bottom: 1rem;'>Welcome, {BUSINESS_CONFIG['user']}</h1>
    """, unsafe_allow_html=True)
    
    # Motivation message
    st.markdown(f"""
    <div style='font-size: 1.2rem; margin-bottom: 2rem; color: #555;'>
        {BUSINESS_CONFIG['motivation_text']}
    </div>
    """, unsafe_allow_html=True)
    
    # Ongoing research section
    st.markdown("""
    <div style='margin-bottom: 1rem;'>
        <h3>🎯 Current Research Agenda</h3>
        <p style='color: #666;'>Let's continue where we left off:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render all task cards
    for task in TASK_CARDS:
        st.markdown(render_task_card(task), unsafe_allow_html=True)
        
        # Add button below each card
        if st.button("Continue Research", key=f"continue_{task['title'].lower().replace(' ', '_')}"):
            query = f"{task['title']}: {task['description']}\nQuery: {task['query']}"
            similar_cases = get_similar_cases(query)
            st.session_state.consulting_session = ConsultingSession()
            st.session_state.consulting_session.stage = "problem_definition"
            st.session_state.consulting_session.current_problem = query
            st.session_state.consulting_session.similar_cases = similar_cases
            st.rerun()
    
    # Separator
    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Custom query section
    st.markdown("""
    <div style='margin-bottom: 1rem;'>
        <h3>🔍 New Research Query</h3>
    </div>
    """, unsafe_allow_html=True)
    
    custom_challenge = st.text_input(
        "Have a different business question in mind?",
        placeholder="Enter your question here...",
        help="Enter your specific business question or challenge"
    )
    
    if st.button("Start Analysis", type="primary"):
        if custom_challenge:
            # Get similar cases first
            similar_cases = get_similar_cases(custom_challenge)
            
            # Initialize new session
            st.session_state.consulting_session = ConsultingSession()
            st.session_state.consulting_session.stage = "problem_definition"
            st.session_state.consulting_session.current_problem = custom_challenge
            st.session_state.consulting_session.similar_cases = similar_cases
            st.rerun()
        else:
            st.warning("Please enter your question first.")

def handle_problem_definition(session):
    """Handle problem definition stage"""
    # Display query section
    st.markdown(
        render_query_section(st.session_state.consulting_session.current_problem),
        unsafe_allow_html=True
    )
    
    # Framework section header with subtle separator
    st.markdown("""
    <div style='margin: 2rem 0 1rem 0;'>
        <div style='height: 1px; background: linear-gradient(to right, #e0e0e0, transparent);'></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show similar cases reference in expander
    if st.session_state.consulting_session.similar_cases:
        if st.session_state.get('advanced_features', False):
            st.write("Raw Similar Cases:")
            st.code(st.session_state.consulting_session.similar_cases)
        with st.expander("📚 Similar Cases Reference", expanded=False):
            st.markdown(f"**Reference Cases:**")
            st.json(st.session_state.consulting_session.similar_cases)
    
    # Store initial framework in session state if not already there
    if 'framework_sections' not in st.session_state:
        prompt = create_consulting_prompt(
            st.session_state.consulting_session.current_problem,
            st.session_state.consulting_session.similar_cases,
            stage="problem_definition"
        )
        
        framework_response = get_llm_response(session, prompt, temperature=0.05, stream=False)
        
        try:
            sections = parse_markdown_sections(framework_response)
            st.session_state.framework_sections = sections
        except Exception as e:
            st.error(f"Error processing framework: {str(e)}")
            st.code(framework_response)
            return
    
    # Display sections from session state
    if st.session_state.framework_sections:
        for i, section in enumerate(st.session_state.framework_sections):
            # Add separator between sections (except for first one)
            if i > 0:
                st.markdown("---")
            
            # Display section title with larger font
            st.markdown(f"""
            <h1 style='font-size: 2rem; margin-bottom: 1rem;'>
                {section["title"]}
            </h1>
            """, unsafe_allow_html=True)
            
            # Display section content
            section_key = f"regenerated_section_{i}"
            if section_key in st.session_state:
                st.markdown(st.session_state[section_key])
            else:
                st.markdown(section["content"])
            
            # Add feedback in an expander
            with st.expander("💭 Comment on this", expanded=False):
                comment = st.text_area(
                    "Your thoughts:",
                    key=f"comment_{i}",
                    help="Share your insights or concerns about this section"
                )
                
                if st.button("Improve Section", key=f"regenerate_btn_{i}"):
                    regeneration_prompt = create_refinement_prompt(
                        section['title'],
                        section['content'],
                        comment
                    )
                    
                    # Get regenerated content
                    regenerated_content = get_llm_response(
                        session, 
                        regeneration_prompt,
                        temperature=0.3,
                        stream=False
                    )
                    
                    if regenerated_content:
                        st.session_state[section_key] = regenerated_content
                        st.rerun()
        
        # Navigation buttons
        col1, col2 = st.columns([1, 2])
        with col2:
            if st.button("Proceed to Data Collection", type="primary", use_container_width=True):
                # Store the final version of all sections
                final_sections = []
                for i, section in enumerate(st.session_state.framework_sections):
                    section_key = f"regenerated_section_{i}"
                    if section_key in st.session_state:
                        final_sections.append({
                            "title": section["title"],
                            "content": st.session_state[section_key]
                        })
                    else:
                        final_sections.append(section)
                
                st.session_state.consulting_session.agreed_framework = True
                st.session_state.consulting_session.framework_sections = final_sections
                st.session_state.consulting_session.stage = "data_collection"
                st.rerun()
        
        with col1:
            if st.button("Start Over", use_container_width=True):
                # Clear all session state related to sections
                for key in list(st.session_state.keys()):
                    if key.startswith(("regenerated_section_", "framework_")):
                        del st.session_state[key]
                st.session_state.consulting_session = ConsultingSession()
                st.rerun()

def handle_data_collection(session):
    """Handle data collection stage"""
    st.header("Required Information")
    
    if not st.session_state.consulting_session.required_data:
        # First get required data fields without RAG
        prompt = create_consulting_prompt(
            st.session_state.consulting_session.current_problem,
            st.session_state.consulting_session.similar_cases,
            stage="data_collection"
        )
        
        data_requirements_response = get_llm_response(
            session, 
            prompt, 
            temperature=0.1, 
            stream=False,
        )
        
        try:
            json_str = data_requirements_response.strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            
            data_requirements = json.loads(json_str)
            st.session_state.consulting_session.required_data = data_requirements
            
        except Exception as e:
            st.error(f"Error processing data requirements: {str(e)}")
            st.code(data_requirements_response)
            return

    # Display data collection form
    st.markdown("Please provide the following information for analysis:")
    
    # Store found values in session state if not already present
    if 'found_values' not in st.session_state:
        st.session_state.found_values = {}
        
        # Search for each required field in the database
        for field, details in st.session_state.consulting_session.required_data.items():
            # First get relevant chunks from webpages database
            webpages_results = get_webpages_data(f"{field} {details['description']}")
            
            if webpages_results:
                # Create prompt to extract specific value
                prompt = create_webpages_prompt(field, details, webpages_results)
                
                # Get LLM response
                response = get_llm_response(session, prompt, temperature=0.1, stream=False)
                
                try:
                    # Clean up the response before parsing
                    cleaned_response = response.strip()
                    # Remove any potential markdown code block markers
                    cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
                    
                    # Parse cleaned LLM response
                    result = json.loads(cleaned_response)
                    
                    # Handle numeric values that might be lists or complex strings
                    value = result['value']
                    if details["type"] == "number" and isinstance(value, str):
                        # Remove any commas from number strings
                        value = value.replace(',', '')
                        try:
                            value = float(value.split()[0].strip())  # Take first number if multiple
                        except ValueError:
                            continue
                    
                    st.session_state.found_values[field] = {
                        'value': value,
                        'source': result.get('source', 'N/A'),
                        'confidence': result.get('confidence', 'N/A'),
                        'explanation': result.get('explanation', 'N/A')
                    }
                except Exception as e:
                    if st.session_state.get('advanced_features', False):
                        st.error(f"Error parsing LLM response for {field}: {str(e)}")
                        st.write("Raw response:")
                        st.code(response)
                        st.write("Cleaned response:")
                        st.code(cleaned_response)
    
    with st.form("data_collection_form", clear_on_submit=False):
        collected_data = {}
        first_field = True
        
        # Store which field to refine
        if 'field_to_refine' not in st.session_state:
            st.session_state.field_to_refine = None
        
        for field, details in st.session_state.consulting_session.required_data.items():
            # Create a visual separator between fields
            if not first_field:
                st.markdown("---")
            first_field = False
            
            # Display field title with larger font and emphasis
            st.markdown(f"""
            <h3 style='margin-bottom: 0px; font-size: 20px;'>
                {details['description']}
                {" (Required)" if details['required'] else ""}
            </h3>
            """, unsafe_allow_html=True)
            
            found_data = st.session_state.found_values.get(field)
            
            # Input field
            try:
                if details["type"] == "number":
                    default_value = 0.0
                    if found_data:
                        try:
                            default_value = float(found_data['value'])
                        except (ValueError, TypeError):
                            pass
                            
                    value = st.number_input(
                        "Enter value",  # Simplified label since we have the title above
                        value=default_value,
                        help=f"Enter {'a different ' if found_data else 'a '}number for {field}",
                        key=f"input_{field}"
                    )
                elif details["type"] == "date":
                    value = st.date_input(
                        "Select date",  # Simplified label
                        help=f"Select {'a different ' if found_data else 'a '}date for {field}",
                        key=f"input_{field}"
                    )
                else:
                    default_value = str(found_data['value']) if found_data else ""
                    value = st.text_input(
                        "Enter text",  # Simplified label
                        value=default_value,
                        help=f"Enter {'different ' if found_data else ''}text for {field}",
                        key=f"input_{field}"
                    )
                
                collected_data[field] = value
                
                # Display source info in an expander if available
                if found_data:
                    with st.expander("📚 Source Reference", expanded=False):
                        st.markdown(f"**Found Value:** {found_data.get('value', 'Not found')}")
                        st.markdown(f"**Confidence:** {found_data.get('confidence', 'N/A')}")
                        st.markdown(f"**Source:** {found_data.get('source', 'N/A')}")
                        st.markdown(f"**Explanation:** {found_data.get('explanation', 'N/A')}")
                    
                    # Move comment expander below source reference
                    with st.expander("💭 Comment on this", expanded=False):
                        comment = st.text_area(
                            "Your thoughts:",
                            key=f"data_comment_{field}",
                            help="Share your insights or concerns about this data point"
                        )
                        
                        # Single form submit button for refinement
                        if st.form_submit_button(f"Refine {field}"):
                            st.session_state.field_to_refine = (field, comment)
            
            except Exception as e:
                st.error(f"Error displaying input for {field}: {str(e)}")
                collected_data[field] = None
        
        # Add some space before the submit button
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Main form submit button
        submit_button = st.form_submit_button("Submit Data", type="primary", use_container_width=True)
        
        # Handle form submission
        if submit_button:
            # Validate required fields
            missing_fields = [
                field for field, details in st.session_state.consulting_session.required_data.items()
                if details["required"] and not collected_data.get(field)
            ]
            
            if missing_fields:
                st.error(f"Please fill in all required fields: {', '.join(missing_fields)}")
            else:
                # Store collected data and proceed
                st.session_state.consulting_session.collected_data = collected_data
                st.session_state.consulting_session.stage = "analysis"
                st.rerun()
        
        # Handle refinement if requested
        if st.session_state.field_to_refine:
            field, comment = st.session_state.field_to_refine
            details = st.session_state.consulting_session.required_data[field]
            found_data = st.session_state.found_values.get(field)
            
            webpages_results = get_webpages_data(f"{field} {details['description']}")
            
            if webpages_results:
                prompt = create_webpages_prompt(
                    field, 
                    details, 
                    webpages_results,
                    user_comment=comment,
                    previous_response=found_data
                )
                
                response = get_llm_response(session, prompt, temperature=0.1, stream=False)
                
                try:
                    cleaned_response = response.strip().replace('```json', '').replace('```', '').strip()
                    result = json.loads(cleaned_response)
                    
                    st.session_state.found_values[field] = {
                        'value': result.get('value'),
                        'confidence': result.get('confidence', 'N/A'),
                        'source': result.get('source', 'N/A'),
                        'explanation': result.get('explanation', 'N/A')
                    }
                    
                except Exception as e:
                    if st.session_state.get('advanced_features', False):
                        st.error(f"Error parsing refined analysis: {str(e)}")
                        st.code(response)
            
            # Clear the refinement state
            st.session_state.field_to_refine = None
            st.rerun()

def handle_analysis(session):
    """Handle analysis stage"""

    # Analysis section header
    st.markdown("""
    <h1 style='font-size: 2.5rem; margin: 2rem 0; color: #333;'>
        Analysis Results
    </h1>
    """, unsafe_allow_html=True)

    # Initialize share state if needed
    if 'share_state' not in st.session_state:
        st.session_state.share_state = {
            'show_popup': False,
            'show_success': False
        }
    
    # Show success message if needed
    if st.session_state.share_state['show_success']:
        st.success("✅ Report has been shared successfully!")
        st.session_state.share_state['show_success'] = False
    
    # Initialize session state variables if they don't exist
    if 'analysis_response' not in st.session_state:
        st.session_state.analysis_response = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    # Create container for streaming output
    stream_container = st.empty()
    
    # Get analysis if not already done
    if not st.session_state.analysis_complete:
        prompt = create_consulting_prompt(
            f"""Challenge: {st.session_state.consulting_session.current_problem}
            Collected Data: {json.dumps(st.session_state.consulting_session.collected_data, indent=2)}""",
            st.session_state.consulting_session.similar_cases,
            stage="analysis"
        )
        
        if not st.session_state.analysis_response:
            with stream_container:
                response = get_llm_response(session, prompt, temperature=0.3, stream=False)
                if response:
                    st.session_state.analysis_response = response
                    st.session_state.analysis_complete = True
    
    # Display sections if we have a response
    if st.session_state.analysis_response:
        stream_container.empty()
        
        try:
            sections = parse_markdown_sections(st.session_state.analysis_response)
            
            # Show similar cases reference in expander
            if st.session_state.consulting_session.similar_cases:
                with st.expander("📚 Similar Cases Reference", expanded=False):
                    st.markdown(f"**Reference Cases:**")
                    st.json(st.session_state.consulting_session.similar_cases)
            
            # Display sections with proper header hierarchy
            for i, section in enumerate(sections):
                # Add separator between sections (except for first one)
                if i > 0:
                    st.markdown("---")
                
                # Get header level and clean title
                header_match = re.match(r'^(#+)\s+(.+)$', section["title"])
                if header_match:
                    header_level = len(header_match.group(1))
                    clean_title = header_match.group(2)
                    
                    # Adjust font size based on header level
                    font_size = {
                        1: "2.5rem",
                        2: "2rem",
                        3: "1.5rem"
                    }.get(header_level, "1.2rem")
                    
                    st.markdown(f"""
                    <h{header_level} style='font-size: {font_size}; margin-bottom: 16px;'>
                        {clean_title}
                    </h{header_level}>
                    """, unsafe_allow_html=True)
                
                # Display section content with refinement option
                section_key = f"regenerated_analysis_{i}"
                if section_key in st.session_state:
                    st.markdown(st.session_state[section_key])
                else:
                    st.markdown(section["content"])
                
                # Add feedback expander
                with st.expander("💭 Comment on this", expanded=False):
                    comment = st.text_area(
                        "Your thoughts:",
                        key=f"analysis_comment_{i}",
                        help="Share your insights or concerns about this section"
                    )
                    
                    if st.button("Improve Section", key=f"regenerate_analysis_btn_{i}"):
                        webpages_results = get_webpages_data(section["content"])
                        if webpages_results:
                            regeneration_prompt = create_refinement_prompt(
                                section['title'],
                                section['content'],
                                comment,
                                rag_context=webpages_results
                            )
                            
                            regenerated_content = get_llm_response(
                                session,
                                regeneration_prompt,
                                temperature=0.3,
                                stream=False
                            )
                            
                            if regenerated_content:
                                st.session_state[section_key] = regenerated_content
                                st.rerun()

        except Exception as e:
            st.error(f"Error processing analysis: {str(e)}")
            st.code(st.session_state.analysis_response)
    
    if st.button("Start New Consultation", use_container_width=True):
        # Clear all session state related to analysis
        keys_to_delete = [
            key for key in st.session_state.keys()
            if key.startswith(("analysis_", "regenerated_analysis_")) or key in ["analysis_complete", "analysis_response"]
        ]
        for key in keys_to_delete:
            del st.session_state[key]
        st.session_state.consulting_session = ConsultingSession()
        st.rerun()

    # Share Report button and popup logic
    if st.button("Share Report", type="primary", use_container_width=True):
        st.session_state.share_state['show_popup'] = True
        st.rerun()
    
    # Show popup if state indicates
    if st.session_state.share_state['show_popup']:
        popup_container = st.empty()
        
        with popup_container.container():
            st.markdown("""
            <div>
                <h3 style='margin-bottom: 16px;'>Share Analysis Report</h3>
            </div>
            """, unsafe_allow_html=True)
            
            email = st.text_input("Enter recipient's email address:", key="share_email")
            
            if st.button("Send", key="send_report"):
                # Show success message in main UI
                st.success("✅ Report has been shared successfully!")
                
                # Close share popup and show success popup
                st.session_state.share_state['show_popup'] = False
                st.session_state.share_state['show_success'] = True
                
                # Show success popup in new container
                success_popup = st.empty()
                with success_popup.container():
                    st.markdown("""
                    <div style='padding: 20px; background-color: #f0f9f0; border-radius: 8px; border: 1px solid #90EE90;'>
                        <h4 style='color: #2E7D32; margin: 0;'>Report Shared Successfully!</h4>
                        <p style='margin: 8px 0 0 0;'>The report has been sent to the recipient's email address.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.rerun()