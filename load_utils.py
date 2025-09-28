import json
from pathlib import Path
import functools
import importlib.util

from matplotlib import table

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
        if table_path.is_dir() and (table_path / "schema.json").exists():
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

@functools.cache
def get_graph_info(short_name, data_dir):
    # Load main.json
    main_json = get_main_json(data_dir)
    graphs = main_json.get("graphs", [])
    graph_info = next((g for g in graphs if g.get("short_name") == short_name), None)
    if not graph_info:
        return f"<div class='error'>Graph '{short_name}' not found.</div>"
    module_path = Path(data_dir).parent / graph_info["module"]
    function_name = graph_info["function"]
    # Dynamically import module and get function
    spec = importlib.util.spec_from_file_location("graph_mod", module_path)
    graph_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(graph_mod)
    generate_func = getattr(graph_mod, function_name)
    return generate_func, graph_info

# Explicit cache for table entries
class TableEntriesCache:
    def __init__(self, data_dir=None):
        self._cache = {}  # key: (table, data_dir), value: list of entries
        self.data_dir = data_dir

    def get(self, table):
        key = str(table)
        if key not in self._cache:
            self._cache[key] = self._load_entries(table)
        return self._cache[key]

    def _load_entries(self, table):
        table_dir = Path(self.data_dir) / table
        entries = []
        for file in table_dir.glob("*.json"):
            if file.name == "schema.json":
                continue
            entry = load_json_file(file)
            if entry:
                entries.append(entry)
        return entries

    def remove(self, table, entry_id: int | str):
        key = str(table)
        entries = self.get(table)
        new_entries = [e for e in entries if e.get('id') != entry_id and e.get('short_name') != entry_id]
        self._cache[key] = new_entries

    def update(self, table, entry):
        key = str(table)
        entries = self.get(table)
        entry_id = entry.get('id') or entry.get('short_name')
        updated = False
        for i, e in enumerate(entries):
            if e.get('id') == entry_id or e.get('short_name') == entry_id:
                entries[i] = entry
                updated = True
                break
        if not updated:
            entries.append(entry)
        self._cache[key] = entries

    def lookup(self, ref: str):
        """Lookup an entry by #id or #short_name or #table/id or #table/short_name."""
        if not ref.startswith('#'):
            return None, None
        ref = ref[1:]
        if '/' in ref:
            table, id_part = ref.split('/', 1)
            entries = self.get(table)
            for entry in entries:
                if id_part.isdigit():
                    if entry.get('id') == int(id_part):
                        return table, entry
                if entry.get('short_name') == id_part:
                    return table, entry
            return None, None
        for table, entries in self._cache.items():
            for entry in entries:
                if ref.isdigit():
                    if entry.get('id') == int(ref):
                        return table, entry
                if entry.get('short_name') == ref:
                    return table, entry
        return None, None

    def get_url(self, ref: str):
        """Return a markdown link if ref is found, else just the ref text."""
        table, entry = self.lookup(ref)
        if entry:
            key = entry.get('short_name', entry.get('id'))
            return f'/{table}/{key}.html', entry
        return None, None


@functools.cache  # We use this to ensure a singleton instance
def get_table_entries_cache(data_dir=None):
    # Singleton cache instance
    table_entries_cache = TableEntriesCache(data_dir)
    return table_entries_cache

def get_table_entries(table, data_dir):
    """Get all entries for a table, using explicit cache."""
    return get_table_entries_cache(data_dir).get(table)

def get_table_dict_by_short_name(table, data_dir):
    """Return a dict mapping short_name to entry for a table."""
    entries = get_table_entries(table, data_dir)
    return {entry.get("short_name"): entry for entry in entries if "short_name" in entry}

def get_table_dict_by_id(table, data_dir):
    """Return a dict mapping id to entry for a table."""
    entries = get_table_entries(table, data_dir)
    return {entry.get("id"): entry for entry in entries if "id" in entry}

@functools.lru_cache(maxsize=1000)
def get_table_schema(table_name, data_dir):
    """Read and cache the schema.json file for a table."""
    schema_path = Path(data_dir) / table_name / "schema.json"
    return load_json_file(schema_path) or {}

@functools.lru_cache(maxsize=1000)
def get_enum_values(table_name, column_name, data_dir):
    """Get the enum values for a specific column in a table's schema."""
    schema = get_table_schema(table_name, data_dir)
    if not schema:
        return []
    for col in schema.get('columns', []):
        if col['name'] == column_name and col.get('type') == 'enum':
            return [(opt['value'], opt.get('display_name', opt['value'])) for opt in col.get('enum', [])]
    return []

def get_table_data(table_name, data_dir):
    """Load all data files for a table."""
    return get_table_entries(table_name, data_dir), get_table_schema(table_name, data_dir)

def lookup_table_entry_by_short_name(table, short_name, data_dir):
    """Lookup a table entry by its short_name. Returns the entry dict or None."""
    d = get_table_dict_by_short_name(table, data_dir)
    return d.get(short_name)


def lookup_table_entry_by_id(table, id_value: int, data_dir: str):
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