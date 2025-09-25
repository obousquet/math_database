"""
Common rendering utilities for HTML generation.
"""

def render_list_section(items, title, css_class):
    """Render a list of items as an HTML section with title."""
    if not items:
        return ""
    
    items_html = f"<ul class='{css_class}-list'>"
    for item in items:
        items_html += f"<li>{item}</li>"
    items_html += "</ul>"
    
    return f"""
    <div class="{css_class}">
        <strong>{title}:</strong>
        {items_html}
    </div>
    """

def render_base_page_template(title, table_name, other_tables, content, extra_head="", extra_scripts=""):
    """Render the base HTML page template with common structure."""
    # Generate navigation links
    nav_links = ['<a href="../index.html">Home</a>']
    for other_table in other_tables:
        if other_table != table_name:
            nav_links.append(f'<a href="../{other_table}/index.html">{other_table.title()}</a>')
    
    nav_html = "\n                ".join(nav_links)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link rel="stylesheet" href="../styles.css">
        {extra_head}
    </head>
    <body>
        <header>
            <h1>{title}</h1>
            <nav>
                {nav_html}
            </nav>
        </header>
        <main class="{table_name}-container">
            {content}
        </main>
        {extra_scripts}
    </body>
    </html>
    """

def render_table_content(rows_html, schema):
    """Render the main table content with description."""
    description = schema.get('description', '') if schema else ''
    
    return f"""
            <div class="table-description">
                <p>{description}</p>
            </div>
            <div class="{schema.get('table_name', 'items') if schema else 'items'}-grid">
                {rows_html}
            </div>
    """