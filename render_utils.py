"""
Common rendering utilities for HTML generation.
"""
import json
from pathlib import Path

def lookup_table_entry_by_short_name(table, short_name, data_dir):
    """Lookup a table entry by its short_name. Returns the entry dict or None."""
    table_dir = Path(data_dir) / table
    for file in table_dir.glob("*.json"):
        if file.name == "schema.json":
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if entry.get("short_name") == short_name:
                return entry
        except Exception:
            continue
    return None


def lookup_table_entry_by_id(table, id_value, data_dir):
    """Lookup a table entry by its id. Returns the entry dict or None."""
    table_dir = Path(data_dir) / table
    for file in table_dir.glob("*.json"):
        if file.name == "schema.json":
            continue
        try:
            with open(file, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if entry.get("id") == id_value:
                return entry
        except Exception:
            continue
    return None

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
    all_tables = other_tables + [table_name]
    for other_table in sorted(all_tables):
        nav_links.append(f'<a href="../{other_table}/index.html">{other_table.title()}</a>')
    nav_html = "\n                ".join(nav_links)

    # Try to get site-wide title from main.json
    site_title = None
    try:
        main_json_path = Path(data_dir) / "main.json"
        if main_json_path.exists():
            with open(main_json_path, "r", encoding="utf-8") as f:
                main_info = json.load(f)
                site_title = main_info.get("title")
    except Exception:
        pass

    # Try to get table title/description from schema.json
    table_title = None
    if table_name:
        try:
            schema_path = Path(data_dir) / table_name / "schema.json"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                    table_title = schema.get("description") or schema.get("table_name")
        except Exception:
            pass

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
        <main class=\"{table_name}-container\">
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