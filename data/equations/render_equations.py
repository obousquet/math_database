"""
Render equations data to HTML format.
"""

import sys
from pathlib import Path

# Add parent directory to path to import render_utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from render_utils import render_list_section, render_base_page_template, render_table_content, lookup_table_entry_by_short_name

def render_row(data):
    """Render a single equation row to HTML."""
    # Author name always shown, link only if entry exists
    author_html = ''
    if data.get('author'):
        author_short = data['author']
        author_entry = None
        author_name = author_short.capitalize()
        if author_short:
            author_entry = lookup_table_entry_by_short_name('mathematicians', author_short)
            if author_entry:
                author_name = author_entry.get('name', author_short.capitalize())
        if author_entry:
            author_html = f'<p><strong>Author:</strong> <a href="../mathematicians/{author_short}.html">{author_name}</a></p>'
        else:
            author_html = f'<p><strong>Author:</strong> {author_name}</p>'
    # Make the whole card clickable, linking to the row page
    row_link = f"{data['short_name']}.html" if data.get('short_name') else None
    if row_link:
        title_html = f'<h3><a href="{row_link}" class="equation-title-link">{data["name"]}</a></h3>'
    else:
        title_html = f'<h3>{data["name"]}</h3>'
    html = f'''
    <div class="equation-card" id="eq-{data['id']}">
        {title_html}
        <div class="equation-display">
            <div class="latex-equation" data-latex="{data['equation']}">
                {data['equation']}
            </div>
        </div>
        <div class="equation-details">
            <p><strong>Category:</strong> {data['category']}</p>
            {author_html}
            {f'<p><strong>Description:</strong> {data["description"]}</p>' if data.get('description') else ''}
            {render_list_section(data.get('applications', []), 'Applications', 'applications') if data.get('applications') else ''}
        </div>
    </div>
    '''
    return html

def render_table_page(rows, schema):
    """Render the complete equations table page."""
    rows_html = ""
    for row in rows:
        rows_html += render_row(row)
    
    # MathJax setup for LaTeX rendering
    mathjax_head = """
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }
            };
        </script>"""
    
    mathjax_scripts = """
        <script>
            // Initialize MathJax for LaTeX rendering
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
    
    content = render_table_content(rows_html, schema)
    
    return render_base_page_template(
        title="",
        table_name="equations",
        other_tables=["mathematicians"],
        content=content,
        extra_head=mathjax_head,
        extra_scripts=mathjax_scripts
    )

def render_row_page(row, schema):
    """Render a standalone HTML page for a single equation row."""
    # MathJax setup for LaTeX rendering
    mathjax_head = """
        <script src=\"https://polyfill.io/v3/polyfill.min.js?features=es6\"></script>
        <script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }
            };
        </script>"""
    mathjax_scripts = """
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
    # Add a back link to the table page
    back_link = '<div class="back-link"><a href="index.html">&larr; Back to Equations Table</a></div>'
    content = back_link + render_row(row)
    return render_base_page_template(
        title=row.get('name', ''),
        table_name="equations",
        other_tables=["mathematicians"],
        content=content,
        extra_head=mathjax_head,
        extra_scripts=mathjax_scripts
    )
