"""
Render equations data to HTML format.
"""

import sys
from pathlib import Path

# Add parent directory to path to import render_utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from render_utils import render_list_section, render_base_page_template, render_table_content

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
            {render_list_section(data.get('applications', []), 'Applications', 'applications') if data.get('applications') else ''}
        </div>
    </div>
    """
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
        title="Mathematical Equations - Math Database",
        table_name="equations", 
        other_tables=["mathematicians"],
        content=content,
        extra_head=mathjax_head,
        extra_scripts=mathjax_scripts
    )