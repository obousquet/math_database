"""
Render equations data to HTML format.
"""

def render_row(data):
    """Render a single equation row to HTML."""
    html = f"""
    <div class="equation-card" id="eq-{data['id']}">
        <h3>{data['name']}</h3>
        <div class="equation-display">
            <div class="latex-equation" data-latex="{data['equation']}">
                {data['equation']}
            </div>
        </div>
        <div class="equation-details">
            <p><strong>Category:</strong> {data['category']}</p>
            {f'<p><strong>Description:</strong> {data["description"]}</p>' if data.get('description') else ''}
            {render_applications(data.get('applications', [])) if data.get('applications') else ''}
        </div>
    </div>
    """
    return html

def render_applications(applications):
    """Render applications list to HTML."""
    if not applications:
        return ""
    
    apps_html = "<ul class='applications-list'>"
    for app in applications:
        apps_html += f"<li>{app}</li>"
    apps_html += "</ul>"
    
    return f"""
    <div class="applications">
        <strong>Applications:</strong>
        {apps_html}
    </div>
    """

def render_table_page(rows, schema):
    """Render the complete equations table page."""
    rows_html = ""
    for row in rows:
        rows_html += render_row(row)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mathematical Equations - Math Database</title>
        <link rel="stylesheet" href="../styles.css">
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }}
            }};
        </script>
    </head>
    <body>
        <header>
            <h1>Mathematical Equations</h1>
            <nav>
                <a href="../index.html">Home</a>
                <a href="../mathematicians/index.html">Mathematicians</a>
            </nav>
        </header>
        <main class="equations-container">
            <div class="table-description">
                <p>{schema['description']}</p>
            </div>
            <div class="equations-grid">
                {rows_html}
            </div>
        </main>
        <script>
            // Initialize MathJax for LaTeX rendering
            document.addEventListener('DOMContentLoaded', function() {{
                const equations = document.querySelectorAll('.latex-equation');
                equations.forEach(eq => {{
                    const latex = eq.getAttribute('data-latex');
                    eq.innerHTML = '$$' + latex + '$$';
                }});
                if (window.MathJax) {{
                    MathJax.typesetPromise();
                }}
            }});
        </script>
    </body>
    </html>
    """