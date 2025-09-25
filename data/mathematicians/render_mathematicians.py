"""
Render mathematicians data to HTML format.
"""

import sys
from pathlib import Path

# Add parent directory to path to import render_utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from render_utils import render_list_section, render_base_page_template, render_table_content

def render_row(data):
    """Render a single mathematician row to HTML."""
    birth_year = data.get('birth_year', 'Unknown')
    death_year = data.get('death_year', 'Present')
    lifespan = f"({birth_year} - {death_year})"
    
    html = f"""
    <div class="mathematician-card" id="math-{data['id']}">
        <h3>{data['name']} {lifespan}</h3>
        <div class="mathematician-details">
            {f'<p><strong>Nationality:</strong> {data["nationality"]}</p>' if data.get('nationality') else ''}
            {render_list_section(data.get('contributions', []), 'Major Contributions', 'contributions') if data.get('contributions') else ''}
            {f'<div class="biography"><strong>Biography:</strong><p>{data["biography"]}</p></div>' if data.get('biography') else ''}
        </div>
    </div>
    """
    return html

def render_table_page(rows, schema):
    """Render the complete mathematicians table page."""
    rows_html = ""
    for row in rows:
        rows_html += render_row(row)
    
    content = render_table_content(rows_html, schema)
    
    return render_base_page_template(
        title="Famous Mathematicians - Math Database",
        table_name="mathematicians", 
        other_tables=["equations"],
        content=content
    )