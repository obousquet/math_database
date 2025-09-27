"""
Simple server for Math Database: supports form POST to save JSON files in server mode.
"""
import os
from flask import Flask, request, jsonify, Response, abort
from pathlib import Path

import render_utils
import load_utils

app = Flask(__name__)

# Set the data directory (relative to this script)
DATA_DIR = Path(os.environ.get("MATHDB_DATA_DIR", "data")).resolve()

@app.route('/api/save_entry/<table>', methods=['POST'])
def save_entry(table):
    """Save a JSON entry to the appropriate table directory and update cache."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    entry = request.get_json()
    # Determine filename: prefer short_name, fallback to id
    filename = entry.get('short_name') or entry.get('id')
    if not filename:
        return jsonify({"error": "Entry must have 'short_name' or 'id'"}), 400
    filename = f"{filename}.json"
    table_dir = DATA_DIR / table
    table_dir.mkdir(parents=True, exist_ok=True)
    file_path = table_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(entry, f, indent=2, ensure_ascii=False)
    # Update cache
    load_utils.get_table_entries_cache().update(table, DATA_DIR, entry)
    return jsonify({"success": True, "filename": filename})

@app.route('/api/delete_entry/<table>/<entry_id>', methods=['DELETE'])
def delete_entry(table, entry_id):
    """Delete a JSON entry file from the appropriate table directory and update cache."""
    table_dir = DATA_DIR / table
    # Try both short_name and id
    for fname in [f"{entry_id}.json"]:
        file_path = table_dir / fname
        if file_path.exists():
            try:
                file_path.unlink()
                # Update cache
                load_utils.get_table_entries_cache().remove(table, DATA_DIR, entry_id)
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
    data_rows, schema = load_utils.get_table_data(table, DATA_DIR)
    render_module = load_utils.load_render_module(table_path, table)
    make_title = getattr(render_module, 'make_title', None) if render_module else None
    html = render_utils.render_table_index_html(table, data_rows, schema, DATA_DIR, mode="server", make_title=make_title)
    return Response(html, mimetype='text/html')

@app.route('/<table>/add.html')
def serve_add_entry(table):
    schema = load_utils.get_table_schema(table, DATA_DIR)
    html = render_utils.render_add_entry_html(table, schema, DATA_DIR)
    return Response(html, mimetype='text/html')

@app.route('/<table>/<row>.html')
def serve_row_page(table, row):
    schema = load_utils.get_table_schema(table, DATA_DIR)
    entry = load_utils.lookup_table_entry_by_short_name(table, row, DATA_DIR)
    if not entry:
        entry = load_utils.lookup_table_entry_by_id(table, row, DATA_DIR)
    if not entry:
        abort(404)
    html = render_utils.render_row_html(table, schema, entry, DATA_DIR, mode="server")
    return Response(html, mimetype='text/html')

@app.route('/<table>/edit_<row>.html')
def serve_edit_entry(table, row):
    schema = load_utils.get_table_schema(table, DATA_DIR)
    entry = load_utils.lookup_table_entry_by_short_name(table, row, DATA_DIR)
    if not entry:
        entry = load_utils.lookup_table_entry_by_id(table, row, DATA_DIR)
    if not entry:
        abort(404)
    html = render_utils.render_edit_entry_html(table, schema, entry, DATA_DIR)
    return Response(html, mimetype='text/html')

@app.route('/styles.css')
def serve_css():
    css = render_utils.render_css()
    return Response(css, mimetype='text/css')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
