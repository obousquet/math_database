#!/usr/bin/env python3
"""
Math Database HTML Generator

This script processes data files in the data/ directory and generates
an HTML website suitable for hosting on GitHub Pages.
"""

import sys
from pathlib import Path
import argparse
import load_utils
import render_utils


def generate_main_index(tables_info, data_dir, output_dir):
    """Generate the main index.html page."""
    main_html = render_utils.render_main_index_html(tables_info, data_dir)
    index_file = output_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(main_html)
    return index_file


def generate_css(output_dir):
    """Generate the CSS stylesheet by copying from the template file."""
    css_content = render_utils.render_css()
    css_output = output_dir / "styles.css"
    with open(css_output, 'w', encoding='utf-8') as dst:
        dst.write(css_content)
    return css_output


def generate_row_html(table_name, schema, row, data_dir, output_dir):
    title = schema.get('title', table_name.title())
    row_short_name = row.get('short_name') or row.get('id')
    row_html = render_utils.render_row_page_template(
        title=title,
        table_name=table_name,
        row=row,
        data_dir=data_dir,
        mode="static",
        use_mathjax=True
    )
    row_file = output_dir / f"{row_short_name}.html"
    with open(row_file, 'w', encoding='utf-8') as rf:
        rf.write(row_html)
    return row_file


def generate_table_index(table_name, data_rows, schema, data_dir, output_dir, make_title=None):
    """Generate the index.html page for a single table."""
    html_content = render_utils.render_table_index_html(table_name, data_rows, schema, data_dir, mode="static", make_title=make_title)
    output_file = output_dir / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return output_file


def generate_table_html(table_name, table_path, data_dir, output_dir):
    """Generate all HTML files for a single table (index, add, row, edit)."""
    print(f"Processing table: {table_name}")
    data_rows, schema = load_utils.get_table_data(table_name, data_dir)
    render_module = load_utils.load_render_module(table_path, table_name)
    make_title = getattr(render_module, 'make_title', None) if render_module else None
    table_output_dir = output_dir / table_name
    table_output_dir.mkdir(exist_ok=True)
    try:
        # Table index
        output_file = generate_table_index(table_name, data_rows, schema, data_dir, table_output_dir, make_title)
        print(f"Generated HTML for {table_name}: {output_file}")

        # Row pages and edit forms
        for row in data_rows:
            row_short_name = row.get('short_name') or row.get('id')
            if not row_short_name:
                continue
            output_file = generate_row_html(table_name, schema, row, data_dir, table_output_dir)
            print(f"Generated row page: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating HTML for table {table_name}: {e}")
        return False

def main():
    """Main function to generate the website."""
    parser = argparse.ArgumentParser(description="Generate Math Database static website.")
    parser.add_argument("data_dir", type=str, help="Path to the data directory.")
    parser.add_argument("--output_dir", type=str, default=None, help="Path to the output directory (default: <data_dir>/../docs)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (data_dir.parent / "docs")

    output_dir.mkdir(exist_ok=True)
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} not found")
        sys.exit(1)

    # Remove all files and folders in output_dir for a clean build
    for item in output_dir.iterdir():
        if item.is_dir():
            for subitem in item.rglob('*'):
                if subitem.is_file():
                    subitem.unlink()
            item.rmdir()
        else:
            item.unlink()

    print(f"Generating website from {data_dir} to {output_dir}")
    tables_info = load_utils.get_table_infos(data_dir)
    successful_tables = 0
    for table_name, info in tables_info.items():
        table_path = data_dir / table_name
        if table_path.is_dir():
            output_file = generate_table_html(table_name, table_path, data_dir, output_dir)
            if output_file:
                print(f"Generated HTML for {table_name}: {output_file}")
                successful_tables += 1
    if successful_tables == 0:
        print("No tables were successfully processed")
        sys.exit(1)
    output_file = generate_main_index(tables_info, data_dir, output_dir)
    print(f"Generated main index: {output_file}")
    output_file = generate_css(output_dir)
    print(f"Generated CSS: {output_file}")
    # Generate graphs/<short_name>.html for each graph in main.json
    main_json = load_utils.get_main_json(data_dir)
    graphs = main_json.get("graphs", [])
    import render_graph_utils
    graphs_dir = output_dir / "graphs"
    graphs_dir.mkdir(exist_ok=True)
    for graph in graphs:
        short_name = graph.get("short_name")
        if not short_name:
            continue
        graph_html = render_graph_utils.render_named_graph_html(data_dir, short_name)
        graph_file = graphs_dir / f"{short_name}.html"
        with open(graph_file, "w", encoding="utf-8") as gf:
            gf.write(graph_html)
        print(f"Generated graph: {graph_file}")
    print(f"\nWebsite generation complete!")
    print(f"Successfully processed {successful_tables} tables")
    print(f"Output directory: {output_dir}")
    print(f"Open {output_dir}/index.html in a browser to view the website")


if __name__ == "__main__":
    main()