"""
Render mathematicians data to HTML format.
"""
from render_utils import render_list_section, render_base_page_template, render_table_content

def render_row(data, data_dir):
    """Render a single mathematician row to HTML."""
    birth_year = data.get('birth_year', 'Unknown')
    death_year = data.get('death_year', 'Present')
    lifespan = f"({birth_year} - {death_year})"
    
    # Make the whole card clickable, linking to the row page
    row_link = f"{data['short_name']}.html" if data.get('short_name') else None
    if row_link:
        title_html = f'<h3><a href="{row_link}" class="mathematician-title-link">{data["name"]} {lifespan}</a></h3>'
    else:
        title_html = f'<h3>{data["name"]} {lifespan}</h3>'
    html = f'''
    <div class="mathematician-card" id="math-{data['id']}">
        {title_html}
        <div class="mathematician-details">
            {f'<p><strong>Nationality:</strong> {data["nationality"]}</p>' if data.get('nationality') else ''}
            {render_list_section(data.get('contributions', []), 'Major Contributions', 'contributions') if data.get('contributions') else ''}
            {f'<div class="biography"><strong>Biography:</strong><p>{data["biography"]}</p></div>' if data.get('biography') else ''}
        </div>
    </div>
    '''
    return html

def render_table_page(rows, schema, data_dir):
    """Render the complete mathematicians table page."""
    rows_html = ""
    for row in rows:
        rows_html += render_row(row, data_dir=data_dir)
    content = render_table_content(rows_html, schema)
    return render_base_page_template(
        title="",
        table_name="mathematicians", 
        other_tables=["equations"],
        content=content,
        data_dir=data_dir,
        use_mathjax=False
    )


def render_row_page(row, schema, data_dir):
    """Render a standalone HTML page for a single mathematician row."""
    content = render_row(row, data_dir=data_dir)
    back_link = '<div class="back-link"><a href="index.html">&larr; Back to Mathematicians Table</a></div>'
    content = back_link + render_row(row, data_dir=data_dir)
    return render_base_page_template(
        title=f"{row.get('name', 'Mathematician')} - Math Database",
        table_name="mathematicians",
        other_tables=["equations", "mathematicians"],
        content=content,
        data_dir=data_dir,
        use_mathjax=False
    )
