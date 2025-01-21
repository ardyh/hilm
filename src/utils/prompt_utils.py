from ..config.business_config import BUSINESS_CONFIG
from typing import List, Dict
import json
import re
import streamlit as st

def create_consulting_prompt(query: str, similar_cases: dict, stage: str = "problem_definition") -> str:
    """Create stage-specific prompts with case examples"""
    cases_context = ""
    if similar_cases and isinstance(similar_cases, dict):
        cases_context = json.dumps(similar_cases, indent=2)

    base_prompt = f"""You are an experienced MBB (McKinsey, Bain, BCG) consulting case coach. 
    Your goal is to help analyze business problems using consulting frameworks and methodologies.
    
    Below is a list of similar cases that you can use as reference, but do not come up with data values by yourself:
    <context>
    {cases_context}
    </context>

    Context: You're advising {BUSINESS_CONFIG['name']}, {BUSINESS_CONFIG['description']} in the {BUSINESS_CONFIG['industry']} industry in {BUSINESS_CONFIG['location']}.
    """

    if stage == "problem_definition":
        prompt = f"""{base_prompt}

Analyze the following business challenge using consulting frameworks and methodologies. 
Structure your response in markdown format with clear headers (using # or ##) for each major section.

Business Challenge: {query}

Use markdown formatting for clear structure, and feel free to add any other relevant sections."""

    elif stage == "data_collection":
        prompt = f"""{base_prompt}

For {BUSINESS_CONFIG['name']}'s challenge: {query}

List exactly what data points we need to collect from the client. Format your response as a valid JSON object like this:
{{
    "market_size": {{
        "description": "Total market size in USD millions",
        "type": "number",
        "required": true
    }},
    "competitor_count": {{
        "description": "Number of direct competitors in target market",
        "type": "number",
        "required": true
    }}
}}

Only return the JSON object, no other text. Ensure all JSON keys and values are properly quoted."""

    elif stage == "analysis":
        prompt = f"""{base_prompt}

Based on the following data for {BUSINESS_CONFIG['name']}:
{query}

Provide a detailed analysis and specific recommendations. Structure your response in markdown format with clear headers (using # or ##) for each major section.
"""

    return prompt

def create_refinement_prompt(section_title: str, section_content: str, feedback: str, rag_context: dict = None) -> str:
    """Create a prompt for section refinement based on feedback and optional RAG context"""
    base_prompt = f"""You are an expert business consultant tasked with refining an analysis section.
    
    Original section: {section_title}
    
    Content:
    {section_content}
    
    User feedback:
    {feedback}
    """
    
    if rag_context:
        base_prompt += f"""
    
    Additional context from research:
    <context>
    {json.dumps(rag_context, indent=2)}
    </context>
    """
    
    base_prompt += """
    
    Please revise this section based on the user's feedback and available context.
    Maintain the same analytical structure but incorporate the user's suggestions and concerns

    If <context> is provided, incorporate also: Any relevant insights from the provided context and specific data points and evidence to support the analysis

    Only return the revised content for this specific section. No need to reiterate the section title.
    """
    
    return base_prompt

def create_webpages_prompt(field_name: str, field_details: dict, context: dict, user_comment: str = None, previous_response: dict = None) -> str:
    """Create RAG-enhanced prompt to find specific data value"""
    base_prompt = f"""You are an expert business consultant. You are to estimate the value for the following data using the context provided in the <context> tags. 
    You are free to make estimations if the data does not give you an exact value. Otherwise, stick to the data.
    
    <field>
    Name: {field_name}
    Description: {field_details['description']}
    Type: {field_details['type']}
    </field>
    """

    if previous_response:
        base_prompt += f"""
    Previous analysis:
    Value: {previous_response.get('value', 'Not found')}
    Confidence: {previous_response.get('confidence', 'N/A')}
    Source: {previous_response.get('source', 'N/A')}
    Explanation: {previous_response.get('explanation', 'N/A')}
    """

    if user_comment:
        base_prompt += f"""
    User feedback:
    {user_comment}
    
    Please revise your analysis based on the user's feedback and previous analysis while still grounding your response in the provided context.
    """
    
    base_prompt += f"""
    <context>          
    {json.dumps(context, indent=2)}
    </context>
    
    Return only a JSON object following this structure:
    {{
        "found": true/false,
        "value": "Extracted value or null if not found",
        "confidence": "HIGH/MEDIUM/LOW",
        "source": "Excerpt from the context that supports the argument",
        "explanation": "Your thought process and reasoning for deriving the value"
    }}
    """
    
    return base_prompt

def parse_markdown_sections(markdown_text: str, require_sections: bool = True) -> List[Dict[str, str]]:
    """
    Parse markdown text into sections based on main headers (#) only.
    
    Args:
        markdown_text (str): The markdown text to parse
        require_sections (bool): If True, requires headers for sections. If False, treats entire text as one section
        
    Returns:
        List[Dict[str, str]]: List of sections with title and content
    """
    if not markdown_text:
        st.error("Empty markdown text received")
        return []
    
    # Debug output
    if st.session_state.get('advanced_features', False):
        st.write("Raw markdown text:")
        st.code(markdown_text)
    
    header_pattern = r'^#{1,2}\s+(.+)$'
    sections = []
    current_section = {"title": "", "content": ""}
    current_content = []
    
    try:
        lines = markdown_text.split('\n')
        has_headers = any(re.match(header_pattern, line) for line in lines)
        
        # If no headers found and sections not required, treat entire text as one section
        if not has_headers and not require_sections:
            return [{
                "title": "Analysis",  # Default title
                "content": markdown_text.strip()
            }]
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save previous section if it exists
                if current_section["title"]:
                    current_section["content"] = '\n'.join(current_content).strip()
                    sections.append(current_section.copy())
                
                # Start new section
                current_section["title"] = header_match.group(1)
                current_content = []
            else:
                current_content.append(line)
        
        # Add the last section
        if current_section["title"]:
            current_section["content"] = '\n'.join(current_content).strip()
            sections.append(current_section.copy())
        elif current_content and not require_sections:
            # If there's content but no sections and sections aren't required
            sections.append({
                "title": "Analysis",
                "content": '\n'.join(current_content).strip()
            })
        
        # Debug output
        if not sections and st.session_state.get('advanced_features', False):
            st.warning("No sections found. Headers detected:")
            headers = [line for line in lines if re.match(header_pattern, line)]
            st.code("\n".join(headers) if headers else "No headers found")
        
        return sections
        
    except Exception as e:
        st.error(f"Error parsing markdown: {str(e)}")
        return [] 