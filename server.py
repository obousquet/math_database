"""
Simple server for Math Database: supports form POST to save JSON files in server mode.
"""

import os
import sys
import argparse
from flask import Flask, request, jsonify, Response, abort
from pathlib import Path

import render_utils
import load_utils

app = Flask(__name__)

def make_filename(entry):
    """Generate a filename for a JSON entry based on its id and short_name."""
    id = entry.get("id")
    id = f"{id:03}"
    if entry.get("short_name", ""):
        filename = f'{id}_{entry.get("short_name")}.json'
    else:
        filename = f'{id}.json'
    return filename


# Serve dynamic graph pages for each graph by short_name
@app.route('/graphs/<short_name>.html')
def serve_named_graph(short_name):
    import render_graph_utils
    html = render_graph_utils.render_named_graph_html(DATA_DIR, short_name, base_url="/", mode="server")
    return Response(html, mimetype='text/html')

@app.route('/api/save_entry/<table>', methods=['POST'])
def save_entry(table):
    """Save a JSON entry to the appropriate table directory and update cache."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    entry = request.get_json()
    filename = make_filename(entry)
    table_dir = DATA_DIR / table
    table_dir.mkdir(parents=True, exist_ok=True)
    file_path = table_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(entry, f, indent=2, ensure_ascii=False)
    # Update cache
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    cache.update(table, entry)
    return jsonify({"success": True, "filename": filename})

@app.route('/api/delete_entry/<table>/<entry_id>', methods=['DELETE'])
def delete_entry(table, entry_id):
    """Delete a JSON entry file from the appropriate table directory and update cache."""
    table_dir = DATA_DIR / table
    # Lookup entry to find the exact filename
    entry_id = int(entry_id)
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    entry = cache.lookup_by_id(table, entry_id)
    if not entry:
        return jsonify({"error": f"Entry {entry_id} not found"}), 404
    fname = make_filename(entry)
    file_path = table_dir / fname
    if file_path.exists():
        try:
            file_path.unlink()
            # Update cache
            cache.remove(table, entry_id)
            return jsonify({"success": True, "deleted": fname})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Entry not found"}), 404


# Dynamic HTML routes

# Handle both / and /index.html for main index
@app.route('/')
@app.route('/index.html')
def serve_index():
    tables_info = load_utils.get_table_infos(DATA_DIR)
    html = render_utils.render_main_index_html(tables_info, DATA_DIR)
    return Response(html, mimetype='text/html')

@app.route('/<table>/index.html')
def serve_table_index(table):
    table_path = DATA_DIR / table
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    data_rows, schema = cache.get_table_data(table)
    render_module = load_utils.load_render_module(table_path, table)
    make_title = getattr(render_module, 'make_title', None) if render_module else None
    html = render_utils.render_table_index_html(table, data_rows, schema, DATA_DIR, mode="server", make_title=make_title)
    return Response(html, mimetype='text/html')

@app.route('/<table>/add.html')
def serve_add_entry(table):
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    schema = cache.get_table_schema(table)
    html = render_utils.render_add_entry_html(table, schema, DATA_DIR)
    return Response(html, mimetype='text/html')

@app.route('/<table>/<row>.html')
def serve_row_page(table, row):
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    schema = cache.get_table_schema(table)
    entry = cache.lookup_table_entry_by_short_name(table, row)
    if not entry:
        entry = cache.lookup_table_entry_by_id(table, row)
    if not entry:
        abort(404)
    html = render_utils.render_row_html(table, schema, entry, DATA_DIR, mode="server")
    return Response(html, mimetype='text/html')

@app.route('/<table>/edit_<row>.html')
def serve_edit_entry(table, row):
    cache = load_utils.get_table_entries_cache(DATA_DIR)
    schema = cache.get_table_schema(table)
    entry = cache.lookup_table_entry_by_short_name(table, row)
    if not entry:
        entry = cache.lookup_table_entry_by_id(table, row)
    if not entry:
        abort(404)
    html = render_utils.render_edit_entry_html(table, schema, entry, DATA_DIR)
    return Response(html, mimetype='text/html')

@app.route('/styles.css')
def serve_css():
    css = render_utils.render_local_file("styles.css")
    return Response(css, mimetype='text/css')

@app.route('/js/<path:filename>')
def serve_js(filename):
    if filename.endswith('.wasm'):
        # Read as binary
        wasm_path = Path(__file__).parent / 'js' / filename
        if not wasm_path.exists():
            return Response('Not found', status=404)
        with open(wasm_path, 'rb') as f:
            data = f.read()
        return Response(data, mimetype='application/wasm')
    else:
        js = render_utils.render_local_file(f"js/{filename}")
        if filename.endswith('.js'):
            mimetype = 'application/javascript'
        else:
            mimetype = 'text/plain'
        return Response(js, mimetype=mimetype)

@app.route('/styles/<path:filename>')
def serve_styles(filename):
    styles = render_utils.render_local_file(f"styles/{filename}")
    return Response(styles, mimetype='text/css')

@app.route('/bibliography.html')
def serve_bibliography():
    main_json = load_utils.get_main_json(DATA_DIR)
    bibinfo = main_json.get("bibliography")
    if not bibinfo:
        return Response("No bibliography configured.", mimetype='text/html')
    bib_html = render_utils.render_bibliography_html(DATA_DIR, bibinfo["bibfile"], bibinfo.get("title", "Bibliography"), base_url="/")
    return Response(bib_html, mimetype='text/html')

if __name__ == "__main__":

    # Parse command-line arguments for data directory
    parser = argparse.ArgumentParser(description="Math Database Server")
    parser.add_argument('--data_dir', type=str, default=None, help='Path to data directory')
    args, _ = parser.parse_known_args()

    # Set the data directory (priority: CLI > env > default)
    if args.data_dir:
        DATA_DIR = Path(args.data_dir).resolve()
    else:
        DATA_DIR = Path(os.environ.get("MATHDB_DATA_DIR", "data")).resolve()

    app.run(host="0.0.0.0", port=8080, debug=True)
