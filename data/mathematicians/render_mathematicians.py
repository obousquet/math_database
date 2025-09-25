"""
Render mathematicians data to HTML format.
"""

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
            {render_contributions(data.get('contributions', [])) if data.get('contributions') else ''}
            {f'<div class="biography"><strong>Biography:</strong><p>{data["biography"]}</p></div>' if data.get('biography') else ''}
        </div>
    </div>
    """
    return html

def render_contributions(contributions):
    """Render contributions list to HTML."""
    if not contributions:
        return ""
    
    contrib_html = "<ul class='contributions-list'>"
    for contrib in contributions:
        contrib_html += f"<li>{contrib}</li>"
    contrib_html += "</ul>"
    
    return f"""
    <div class="contributions">
        <strong>Major Contributions:</strong>
        {contrib_html}
    </div>
    """

def render_table_page(rows, schema):
    """Render the complete mathematicians table page."""
    rows_html = ""
    for row in rows:
        rows_html += render_row(row)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Famous Mathematicians - Math Database</title>
        <link rel="stylesheet" href="../styles.css">
    </head>
    <body>
        <header>
            <h1>Famous Mathematicians</h1>
            <nav>
                <a href="../index.html">Home</a>
                <a href="../equations/index.html">Equations</a>
            </nav>
        </header>
        <main class="mathematicians-container">
            <div class="table-description">
                <p>{schema['description']}</p>
            </div>
            <div class="mathematicians-grid">
                {rows_html}
            </div>
        </main>
    </body>
    </html>
    """