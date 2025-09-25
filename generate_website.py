#!/usr/bin/env python3
"""
Math Database HTML Generator

This script processes data files in the data/ directory and generates
an HTML website suitable for hosting on GitHub Pages.
"""

import os
import json
import importlib.util
import sys
from pathlib import Path


def load_json_file(filepath):
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None


def load_render_module(table_path, table_name):
    """Dynamically load the render module for a table."""
    render_file = table_path / f"render_{table_name}.py"
    if not render_file.exists():
        print(f"Warning: render file {render_file} not found")
        return None
    
    spec = importlib.util.spec_from_file_location(f"render_{table_name}", render_file)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading render module for {table_name}: {e}")
        return None


def get_table_data(table_path):
    """Load all data files for a table."""
    data_files = []
    schema = None
    
    # Load schema
    schema_file = table_path / "schema.json"
    if schema_file.exists():
        schema = load_json_file(schema_file)
    else:
        print(f"Warning: schema.json not found in {table_path}")
    
    # Load all JSON data files (excluding schema.json)
    for file_path in table_path.glob("*.json"):
        if file_path.name != "schema.json":
            data = load_json_file(file_path)
            if data:
                data_files.append(data)
    
    return data_files, schema


def generate_table_html(table_name, table_path, output_dir):
    """Generate HTML for a single table."""
    print(f"Processing table: {table_name}")
    
    # Load data and schema
    data_rows, schema = get_table_data(table_path)
    
    if not data_rows:
        print(f"No data found for table {table_name}")
        return False
    
    # Load render module
    render_module = load_render_module(table_path, table_name)
    if not render_module or not hasattr(render_module, 'render_table_page'):
        print(f"No valid render module found for table {table_name}")
        return False
    
    # Generate HTML
    try:
        html_content = render_module.render_table_page(data_rows, schema or {})
        
        # Create output directory
        table_output_dir = output_dir / table_name
        table_output_dir.mkdir(exist_ok=True)
        
        # Write HTML file
        output_file = table_output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated HTML for {table_name}: {output_file}")
        return True
        
    except Exception as e:
        print(f"Error generating HTML for table {table_name}: {e}")
        return False


def generate_main_index(tables_info, output_dir):
    """Generate the main index.html page."""
    tables_html = ""
    for table_name, info in tables_info.items():
        description = info.get('description', f'{table_name.title()} data')
        count = info.get('count', 0)
        tables_html += f"""
        <div class="table-card">
            <h3><a href="{table_name}/index.html">{table_name.title()}</a></h3>
            <p>{description}</p>
            <p class="record-count">{count} records</p>
        </div>
        """
    
    main_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Math Database</title>
        <link rel="stylesheet" href="styles.css">
    </head>
    <body>
        <header>
            <h1>Mathematics Database</h1>
            <p>A comprehensive collection of mathematical knowledge</p>
        </header>
        <main class="main-container">
            <div class="intro">
                <p>Welcome to the Mathematics Database! Explore our collections of mathematical equations, famous mathematicians, and more.</p>
            </div>
            <div class="tables-grid">
                {tables_html}
            </div>
        </main>
        <footer>
            <p>Generated with Python • Hosted on GitHub Pages</p>
        </footer>
    </body>
    </html>
    """
    
    # Write main index file
    index_file = output_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(main_html)
    
    print(f"Generated main index: {index_file}")


def generate_css(output_dir):
    """Generate the CSS stylesheet."""
    css_content = """
/* Math Database Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem 0;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

nav {
    margin-top: 1rem;
}

nav a {
    color: white;
    text-decoration: none;
    margin: 0 1rem;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    transition: background-color 0.3s;
}

nav a:hover {
    background-color: rgba(255,255,255,0.2);
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.intro {
    text-align: center;
    margin-bottom: 3rem;
    font-size: 1.1rem;
}

.tables-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.table-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s, box-shadow 0.3s;
}

.table-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.2);
}

.table-card h3 a {
    color: #667eea;
    text-decoration: none;
    font-size: 1.5rem;
}

.table-card h3 a:hover {
    color: #764ba2;
}

.record-count {
    color: #666;
    font-style: italic;
    margin-top: 1rem;
}

/* Table-specific styles */
.equations-grid, .mathematicians-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
}

.equation-card, .mathematician-card {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.equation-card:hover, .mathematician-card:hover {
    transform: translateY(-3px);
}

.equation-display {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    text-align: center;
    border-left: 4px solid #667eea;
}

.latex-equation {
    font-size: 1.2rem;
    color: #333;
}

.equation-details, .mathematician-details {
    margin-top: 1rem;
}

.applications, .contributions {
    margin-top: 1rem;
}

.applications-list, .contributions-list {
    margin-left: 1.5rem;
    margin-top: 0.5rem;
}

.applications-list li, .contributions-list li {
    margin-bottom: 0.3rem;
}

.biography {
    margin-top: 1rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 5px;
    border-left: 4px solid #28a745;
}

.table-description {
    text-align: center;
    margin-bottom: 2rem;
    font-size: 1.1rem;
    color: #666;
}

footer {
    text-align: center;
    padding: 2rem;
    background: #333;
    color: white;
    margin-top: 3rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .equations-grid, .mathematicians-grid {
        grid-template-columns: 1fr;
    }
    
    .equation-card, .mathematician-card {
        padding: 1.5rem;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    nav a {
        margin: 0 0.5rem;
        padding: 0.3rem 0.8rem;
    }
}
"""
    
    css_file = output_dir / "styles.css"
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print(f"Generated CSS: {css_file}")


def main():
    """Main function to generate the website."""
    # Set up paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    output_dir = script_dir / "docs"  # GitHub Pages default directory
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} not found")
        sys.exit(1)
    
    print(f"Generating website from {data_dir} to {output_dir}")
    
    # Find all table directories
    tables_info = {}
    successful_tables = 0
    
    for table_path in data_dir.iterdir():
        if table_path.is_dir():
            table_name = table_path.name
            
            # Get table info
            data_rows, schema = get_table_data(table_path)
            tables_info[table_name] = {
                'description': schema.get('description', f'{table_name.title()} data') if schema else f'{table_name.title()} data',
                'count': len(data_rows)
            }
            
            # Generate HTML for this table
            if generate_table_html(table_name, table_path, output_dir):
                successful_tables += 1
    
    if successful_tables == 0:
        print("No tables were successfully processed")
        sys.exit(1)
    
    # Generate main index page
    generate_main_index(tables_info, output_dir)
    
    # Generate CSS
    generate_css(output_dir)
    
    print(f"\nWebsite generation complete!")
    print(f"Successfully processed {successful_tables} tables")
    print(f"Output directory: {output_dir}")
    print(f"Open {output_dir}/index.html in a browser to view the website")


if __name__ == "__main__":
    main()