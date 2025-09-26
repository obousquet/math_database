#!/usr/bin/env python3
"""
Math Database HTML Generator

This script processes data files in the data/ directory and generates
an HTML website suitable for hosting on GitHub Pages.
"""

import functools
import sys
from pathlib import Path
import argparse
import load_utils

def generate_table_html(table_name, table_path, data_dir, output_dir):
    """Generate HTML for a single table."""
    print(f"Processing table: {table_name}")
    
    # Load data and schema
    data_rows, schema = load_utils.get_table_data(table_name, data_dir)
    
    if not data_rows:
        print(f"No data found for table {table_name}")
        return False
    
    # Load render module
    render_module = load_utils.load_render_module(table_path, table_name)
    if not render_module or not hasattr(render_module, 'render_table_page'):
        print(f"No valid render module found for table {table_name}")
        return False
    
    # Generate table HTML
    try:
        html_content = render_module.render_table_page(data_rows, schema or {}, data_dir=data_dir)
        # Create output directory
        table_output_dir = output_dir / table_name
        table_output_dir.mkdir(exist_ok=True)
        # Write table index.html
        output_file = table_output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Generated HTML for {table_name}: {output_file}")

        # Generate individual row pages if supported
        if hasattr(render_module, 'render_row_page'):
            for row in data_rows:
                row_short_name = row.get('short_name') or row.get('id')
                if not row_short_name:
                    continue
                row_html = render_module.render_row_page(row, schema or {}, data_dir=data_dir)
                row_file = table_output_dir / f"{row_short_name}.html"
                with open(row_file, 'w', encoding='utf-8') as rf:
                    rf.write(row_html)
                print(f"Generated row page: {row_file}")
        else:
            print(f"render_row_page not found in render module for {table_name}, skipping row pages.")
        return True
    except Exception as e:
        print(f"Error generating HTML for table {table_name}: {e}")
        return False


def generate_main_index(tables_info, data_dir, output_dir):
    """Generate the main index.html page."""
    # Load main.json for main page info
    main_info = load_utils.get_main_json(data_dir)

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
        <title>{main_info['title']}</title>
        <link rel="stylesheet" href="styles.css">
    </head>
    <body>
        <header>
            <h1>{main_info['header']}</h1>
            <p>{main_info['subtitle']}</p>
        </header>
        <main class="main-container">
            <div class="intro">
                <p>{main_info['description']}</p>
            </div>
            <div class="tables-grid">
                {tables_html}
            </div>
        </main>
        <footer>
            <p>{main_info['footer']}</p>
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
    """Generate the CSS stylesheet by copying from the template file."""
    script_dir = Path(__file__).parent
    css_template = script_dir / "styles.css"
    css_output = output_dir / "styles.css"
    
    if not css_template.exists():
        print(f"Warning: CSS template file {css_template} not found")
        return
    
    try:
        with open(css_template, 'r', encoding='utf-8') as src:
            css_content = src.read()
        
        with open(css_output, 'w', encoding='utf-8') as dst:
            dst.write(css_content)
        
        print(f"Generated CSS: {css_output}")
    except Exception as e:
        print(f"Error generating CSS: {e}")

def main():
    """Main function to generate the website."""
    # Set up paths
    parser = argparse.ArgumentParser(description="Generate Math Database static website.")
    parser.add_argument("data_dir", type=str, help="Path to the data directory.")
    parser.add_argument("--output_dir", type=str, default=None, help="Path to the output directory (default: <data_dir>/../docs)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (data_dir.parent / "docs")

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} not found")
        sys.exit(1)

    print(f"Generating website from {data_dir} to {output_dir}")

    # Find all table directories
    tables_info = load_utils.get_table_infos(data_dir)
    successful_tables = 0

    for table_name, info in tables_info.items():
        table_path = data_dir / table_name
        if table_path.is_dir():
            # Generate HTML for this table
            if generate_table_html(table_name, table_path, data_dir, output_dir):
                successful_tables += 1

    if successful_tables == 0:
        print("No tables were successfully processed")
        sys.exit(1)

    # Generate main index page
    generate_main_index(tables_info, data_dir, output_dir)

    # Generate CSS
    generate_css(output_dir)

    print(f"\nWebsite generation complete!")
    print(f"Successfully processed {successful_tables} tables")
    print(f"Output directory: {output_dir}")
    print(f"Open {output_dir}/index.html in a browser to view the website")


if __name__ == "__main__":
    main()