def render_task_card(task):
    """Render a single task card using the task configuration"""
    # Generate the tags HTML first
    tags_html = []
    for tag in task['tags']:
        tag_html = f"""<span style='background-color: {tag['bg_color']}; color: {tag['text_color']}; padding: 4px 8px; border-radius: 3px; font-size: 12px; margin-right: 8px;'>{tag['text']}</span>"""
        tags_html.append(tag_html)
    
    # Return the complete card HTML with minimal whitespace
    return f"""<div style='background-color: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
        <div style='display: flex; align-items: center; margin-bottom: 12px;'>
            <span style='background-color: #0052CC; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; margin-right: 10px;'>{task['status']}</span>
            <span style='color: #5E6C84; font-size: 13px;'>{task['type']} • {task['priority']}</span>
        </div>
        <h3 style='margin: 0 0 12px 0; font-size: 1.2rem; color: #172B4D;'>{task['title']}</h3>
        <p style='color: #172B4D; margin-bottom: 16px;'>{task['description']}</p>
        <div style='display: flex; align-items: center;'>{''.join(tags_html)}</div>
    </div>"""

import html

def render_query_section(problem_text: str) -> str:
    """Render the query section with consistent styling"""
    # Handle different query formats
    if "Query:" in problem_text:
        # Format: "Title: Description\nQuery: Details"
        title_part = problem_text.split("\nQuery:")[0]
        query_part = problem_text.split("\nQuery:")[1].strip() if "\nQuery:" in problem_text else ""
        
        # Further split title if it contains a colon
        title = title_part.strip()
    else:
        # No explicit Query section
        title = problem_text.strip()
        query_part = ""
    
    # Escape HTML and convert newlines to <br> tags
    title = html.escape(title).replace('\n', '<br>')
    query_part = html.escape(query_part).replace('\n', '<br>')
    
    # Add line breaks between sentences in query_part
    if query_part:
        query_part = query_part.replace('. ', '.<br>')
    
    return f"""
    <div style='margin: 2rem 0; padding: 1.5rem; border-left: 4px solid #e0e0e0; background: #f8f9fa;'>
        <div style='font-size: 1.2rem; color: #333; font-weight: 500; line-height: 1.5;'>
            {title}
        </div>
        {f"<div style='margin-top: 1rem; color: #555; font-size: 1rem; line-height: 1.6;'>{query_part}</div>" if query_part else ''}
    </div>
    """