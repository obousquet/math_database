"""
Common rendering utilities for HTML generation.
"""
import load_utils

def render_list_section(items, title):
    """Render a list of items as an HTML section with title."""
    if not items:
        return ""
    
    items_html = f"<ul class='fields-list'>"
    for item in items:
        items_html += f"<li>{item}</li>"
    items_html += "</ul>"
    
    return f"""
    <div class="fields">
        <strong>{title}:</strong>
        {items_html}
    </div>
    """

def get_mathjax_head():
    return """
        <script src=\"https://polyfill.io/v3/polyfill.min.js?features=es6\"></script>
        <script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\(', '\\)']],
                    displayMath: [['$$', '$$'], ['\\[', '\\]']]
                }
            };</script>"""

def get_mathjax_scripts():
    return """
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const equations = document.querySelectorAll('.latex-equation');
                equations.forEach(eq => {
                    const latex = eq.getAttribute('data-latex');
                    eq.innerHTML = '$$' + latex + '$$';
                });
                if (window.MathJax) {
                    MathJax.typesetPromise();
                }
            });
        </script>"""

def render_base_page_template(title, table_name, other_tables, content, data_dir, extra_head="", extra_scripts="", use_mathjax=False):
    """Render the base HTML page template with common structure."""
    # Generate navigation links
    nav_links = ['<a href="../index.html">Home</a>']
    all_tables = load_utils.get_table_infos(data_dir)
    for table, info in sorted(all_tables.items(), key=lambda v: v[1]['name']):
        nav_links.append(f'<a href="../{table}/index.html">{info["name"]}</a>')
    nav_html = "\n                ".join(nav_links)

    # Try to get site-wide title from main.json
    site_title = None
    main_json = load_utils.get_main_json(data_dir)
    site_title = main_json.get("title")

    # Use get_table_schema for table title/description
    table_title = None
    schema = None
    if table_name:
        schema = load_utils.get_table_schema(table_name, data_dir)
        if schema:
            table_title = schema.get("description") or schema.get("table_name")

    # Compose the <title> tag
    if table_title and site_title:
        page_title = f"{table_title} - {site_title}"
    elif table_title:
        page_title = table_title
    elif site_title:
        page_title = site_title
    else:
        page_title = title

    # Add MathJax if requested
    if use_mathjax:
        extra_head = get_mathjax_head() + (extra_head or "")
        extra_scripts = get_mathjax_scripts() + (extra_scripts or "")

    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>{page_title}</title>
        <link rel=\"stylesheet\" href=\"../styles.css\">
        {extra_head}
    </head>
    <body>
        <header>
            <h1>{page_title}</h1>
            <nav>
                {nav_html}
            </nav>
        </header>
        <main class=\"table-container\">
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
            <div class="table-grid">
                {rows_html}
            </div>
    """

def maybe_linked(table, value, data_dir):
    """If value starts with #, look up as id or short_name in table and return an HTML link to the entry (using its name). Otherwise, return value as is."""
    if not isinstance(value, str) or not value.startswith('#'):
        return value
    key = value[1:]
    # Try id lookup first
    entry = load_utils.lookup_table_entry_by_id(table, key, data_dir)
    if not entry:
        entry = load_utils.lookup_table_entry_by_short_name(table, key, data_dir)
    if entry:
        short_name = entry.get('short_name', key)
        name = entry.get('name', key)
        return f'<a href="../{table}/{short_name}.html">{name}</a>'
    return '?' + value