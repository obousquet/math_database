import json
from pathlib import Path
import functools
import importlib.util

def load_json_file(filepath):
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {e}")
        return None


@functools.cache
def get_table_infos(data_dir):
    """Get information about all tables in the data directory."""
    tables_info = {}
    for table_path in data_dir.iterdir():
        if table_path.is_dir():
            table_name = table_path.name
            data_rows, schema = get_table_data(table_name, data_dir)
            if schema:
                description = schema.get('description', f'{table_name.title()} data')
            else:
                description = f'{table_name.title()} data'
            schema = get_table_schema(table_name, data_dir)
            if schema:
                name = schema.get('title', table_name.title())
            else:
                name = table_name.title()
            tables_info[table_name] = {
                'description': description,
                'count': len(data_rows),
                'name': name
            }
    return tables_info


@functools.cache
def get_main_json(data_dir):
    """Get the main.json content."""
    main_json_path = Path(data_dir) / "main.json"
    return load_json_file(main_json_path) or {}

@functools.lru_cache(maxsize=1000)
def get_table_entries(table, data_dir):
    """Read and cache all entries (not schema) for a table as a list."""
    table_dir = Path(data_dir) / table
    entries = []
    for file in table_dir.glob("*.json"):
        if file.name == "schema.json":
            continue
        entry = load_json_file(file)
        if entry:
            entries.append(entry)
    return entries

@functools.lru_cache(maxsize=1000)
def get_table_dict_by_short_name(table, data_dir):
    """Return a dict mapping short_name to entry for a table."""
    entries = get_table_entries(table, data_dir)
    return {entry.get("short_name"): entry for entry in entries if "short_name" in entry}

@functools.lru_cache(maxsize=1000)
def get_table_dict_by_id(table, data_dir):
    """Return a dict mapping id to entry for a table."""
    entries = get_table_entries(table, data_dir)
    return {entry.get("id"): entry for entry in entries if "id" in entry}

@functools.lru_cache(maxsize=1000)
def get_table_schema(table_name, data_dir):
    """Read and cache the schema.json file for a table."""
    schema_path = Path(data_dir) / table_name / "schema.json"
    return load_json_file(schema_path) or {}

def get_table_data(table_name, data_dir):
    """Load all data files for a table."""
    return get_table_entries(table_name, data_dir), get_table_schema(table_name, data_dir)

def lookup_table_entry_by_short_name(table, short_name, data_dir):
    """Lookup a table entry by its short_name. Returns the entry dict or None."""
    d = get_table_dict_by_short_name(table, data_dir)
    return d.get(short_name)


def lookup_table_entry_by_id(table, id_value, data_dir):
    """Lookup a table entry by its id. Returns the entry dict or None."""
    d = get_table_dict_by_id(table, data_dir)
    return d.get(id_value)


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