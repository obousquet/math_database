"""
Common rendering utilities for HTML generation.
"""
import functools

import json

from pathlib import Path
import load_utils
import re
import markdown

def render_list_section(items, title):
    """Render a list of items as an HTML section with title."""
    if not items:
        return ''

    items_html = f"<ul class='fields-list'>"
    for item in items:
        items_html += f"<li>{item}</li>"
    items_html += "</ul>"
    
    return f"""
    <div class="fields">
        <strong>{title}:</strong>
        {items_html}
    </div>
    """

def render_latex_field(label, equation):
    result = ''
    if not equation:
        return result
    if label:
        result += f"<strong>{label}:</strong>"
    result += f"""
    <div class="table-display">
        <div class="latex-equation" data-latex="{equation}">
            {equation}
        </div>
    </div>
    """
    return result

def render_text_field(label, text, data_dir):
    result = ''
    if not text:
        return result
    # Replace hashtags with links
    def hashtag_replacer(match):
        hashtag = match.group(0)
        return maybe_linked(hashtag, data_dir)
    hashtag_pattern = r'#\w+(?:/\w+)?'
    linked_text = re.sub(hashtag_pattern, hashtag_replacer, text)
    # Render Markdown
    html_text = markdown.markdown(linked_text, extensions=['extra', 'sane_lists'])
    if label:
        result += f"<strong>{label}:</strong>"
    result += f"<div class=\"text-field\">{html_text}</div>"
    return result

def render_string_field(label, text, table_name, data_dir):
    result = ''
    if not text:
        return result
    if label:
        result += f"<p><strong>{label}: </strong>"
    else:
        result += '<p>'
    result += f'{maybe_linked(text, data_dir=data_dir)}</p>'
    return result

def get_mathjax_head():
    return """
        <script src=\"https://polyfill.io/v3/polyfill.min.js?features=es6\"></script>
        <script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>
        <script>
            window.MathJax = {
                tex: {
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }
            };</script>"""

def get_mathjax_scripts():
    return """
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

def render_base_page_template(title, table_name, content, data_dir, extra_head="", extra_scripts="", use_mathjax=False):
    """Render the base HTML page template with common structure."""
    # Generate navigation links
    nav_links = ['<a href="../index.html">Home</a>']
    main_json = load_utils.get_main_json(data_dir)
    homepage = main_json.get("homepage")
    if homepage:
        nav_links.append(f'<a href="{homepage}" target="_blank">About</a>')
    all_tables = load_utils.get_table_infos(data_dir)
    for table, info in sorted(all_tables.items(), key=lambda v: v[1]['name']):
        nav_links.append(f'<a href="../{table}/index.html">{info["name"]}</a>')
    nav_html = "\n                ".join(nav_links)

    # Try to get site-wide title from main.json
    site_title = None
    main_json = load_utils.get_main_json(data_dir)
    site_title = main_json.get("title")

    # Use get_table_schema for table title/description
    table_title = None
    schema = None
    if table_name:
        schema = load_utils.get_table_schema(table_name, data_dir)
        if schema:
            table_title = schema.get("description") or schema.get("table_name")

    # Compose the <title> tag
    if table_title and site_title:
        page_title = f"{table_title} - {site_title}"
    elif table_title:
        page_title = table_title
    elif site_title:
        page_title = site_title
    else:
        page_title = title

    # Add MathJax if requested
    if use_mathjax:
        extra_head = get_mathjax_head() + (extra_head or "")
        extra_scripts = get_mathjax_scripts() + (extra_scripts or "")

    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>{page_title}</title>
        <link rel=\"stylesheet\" href=\"../styles.css\">
        {extra_head}
    </head>
    <body>
        <header>
            <h1>{page_title}</h1>
            <nav>
                {nav_html}
            </nav>
        </header>
        <main class=\"table-container\">
            {content}
        </main>
        {extra_scripts}
    </body>
    </html>
    """

def get_delete_js(table_name):
    return f"""
    <script>
    function deleteEntry(entryId) {{
        if (!confirm('Are you sure you want to delete entry ' + entryId + '? This cannot be undone.')) return;
        fetch('/api/delete_entry/{table_name}/' + entryId, {{ method: 'DELETE' }})
            .then(resp => resp.json())
            .then(data => {{
                if (data.success) {{
                    alert('Entry deleted.');
                    window.location.href = 'index.html';
                }} else {{
                    alert('Error deleting entry: ' + (data.error || 'Unknown error'));
                }}
            }})
            .catch(err => alert('Error deleting entry: ' + err));
    }}
    </script>
    """
    
def render_row_page_template(
        title, table_name, row, data_dir, use_mathjax=False, mode="static"):
    """Render a standalone HTML page for a single equation row."""
    content = f'<div class="back-link-light"><a href="index.html">&larr; Back to {table_name.title()} Table</a></div>'
    content += render_card(
        table_name, schema=load_utils.get_table_schema(table_name, data_dir), entry=row, data_dir=data_dir, mode=mode) 
    return render_base_page_template(
        title=title,
        table_name=table_name,
        content=content,
        data_dir=data_dir,
        extra_scripts=get_delete_js(table_name) if mode == "server" else "",
        use_mathjax=True
    )

def render_table_content(rows_html, schema):
    """Render the main table content with description."""
    description = schema.get('description', '') if schema else ''
    
    return f"""
            <div class="table-description">
                <p>{description}</p>
            </div>
            <div class="table-grid">
                {rows_html}
            </div>
    """

def match(reference, entry, table=None):
    if not isinstance(reference, str) or not reference.startswith('#'):
        return False
    key = reference[1:]
    if '/' in key:
        table_ref, short_name_or_id = key.split('/', 1)
        if table and table != table_ref:
            return False
    else:
        short_name_or_id = key
    if short_name_or_id.isdigit():
        return entry.get('id') == int(short_name_or_id)
    return entry.get('short_name') == short_name_or_id

def maybe_linked(value, data_dir):
    """
    If value starts with #, link to an entry:
    - #short_name: search all tables for short_name
    - #table/short_name: search specific table for short_name
    Otherwise, return value as is.
    """
    if not isinstance(value, str) or not value.startswith('#'):
        return value
    key = value[1:]
    if '/' in key:
        table, short_name = key.split('/', 1)
        entry = load_utils.lookup_table_entry_by_short_name(table, short_name, data_dir)
        if entry:
            name = entry.get('name', short_name)
            return f'<a href="../{table}/{short_name}.html">{name}</a>'
        return '?' + value
    # Search all tables for short_name
    tables_info = load_utils.get_table_infos(data_dir)
    for table in tables_info:
        entry = load_utils.lookup_table_entry_by_short_name(table, key, data_dir)
        if entry:
            name = entry.get('name', key)
            return f'<a href="../{table}/{key}.html">{name}</a>'
    return '?' + value

def get_enum_display_name(table, column, value, data_dir):
    """Get the display name for an enum value in a specific table and column."""
    enum_values = load_utils.get_enum_values(table, column, data_dir)
    for val, display in enum_values:
        if val == value:
            return display
    return value

def get_next_id(table_name, data_dir):
    """Return the next available id (as a string) for a table, assuming numeric ids."""
    entries = load_utils.get_table_entries(table_name, data_dir)
    max_id = 0
    for entry in entries:
        try:
            val = int(entry.get('id', 0))
            if val > max_id:
                max_id = val
        except Exception:
            continue
    return str(max_id + 1)

def render_card(table_name, schema, entry, data_dir, mode="static", make_title=None):
    """Render a card view for an entry, based on its schema."""
    if not schema or not entry:
        return "<div class='table-card'>No data available</div>"
    card_content = ""
    if make_title:
        title = make_title(entry)
    else:
        title = entry.get('name', 'No Name')

    row_link = f"{entry['short_name']}.html" if entry.get('short_name') else None
    edit_link = ""
    trashcan = ""
    if mode != "static":
        edit_target = f"edit_{entry.get('short_name') or entry.get('id')}.html"
        # Icons container for proper layout
        icons_html = f'''<span style="position:absolute; top:8px; right:8px; display:flex; gap:8px; z-index:2;">
            <a href="{edit_target}" class="edit-entry-link" title="Edit Entry" style="font-size:1.2em; text-decoration:none;">✎</a>
            <span class="delete-entry-btn" style="cursor:pointer; font-size:1.2em;" title="Delete Entry" onclick="deleteEntry({entry.get('id')})">🗑️</span>
        </span>'''
    else:
        icons_html = ""
    if row_link:
        title_html = f'<h3><a href="{row_link}" class="table-title-link">{title}</a></h3>'
    else:
        title_html = f'<h3>{title}</h3>'

    for col in schema.get('columns', []):
        col_name = col.get('name')
        col_label = col.get('label', col_name)
        col_value = entry.get(col_name, '')
        if not col.get('rendered', True):
            continue
        col_type = col.get('type', 'string')
        match col_type:
            case 'string':
                field = render_string_field(col_label, col_value, table_name, data_dir)
            case 'integer':
                field = f'<p><strong>{col_label}:</strong> {str(col_value) if col_value is not None else ""}</p>'
            case 'boolean':
                if col_value is True:
                    display = "Yes"
                elif col_value is False:
                    display = "No"
                else:
                    display = "Unspecified"
                field = f'<p><strong>{col_label}:</strong> {display}</p>'
            case 'text':
                field = render_text_field(col_label, col_value, data_dir)
            case 'latex':
                field = render_latex_field(col_label, col_value)
            case 'enum':
                field = f'<p><strong>{col_label}:</strong> {get_enum_display_name(table_name, col_name, col_value, data_dir)}</p>'
            case 'array':
                field = f'<p><strong>{col_label}:</strong>'
                if isinstance(col_value, list):
                    items_html = "<ul class='fields-list'>"
                    for item in col_value:
                        items_html += f"<li>{maybe_linked(item, data_dir=data_dir)}</li>"
                    items_html += "</ul>"
                    field += items_html + '</p>'
            case 'reference':
                # Reference fields: auto-populate from another table/column
                ref_table = col.get('table')
                ref_column = col.get('column')
                if ref_table and ref_column:
                    # Find all entries in ref_table where ref_column == entry['short_name'] or entry['id']
                    ref_entries = []
                    for ref_entry in load_utils.get_table_entries(ref_table, data_dir):
                        if match(ref_entry.get(ref_column), entry, table=table_name):
                            ref_entries.append(ref_entry)
                    if ref_entries:
                        # Display as a list of links or names
                        items_html = "<ul class='fields-list'>"
                        for ref_entry in ref_entries:
                            display = ref_entry.get('name', ref_entry.get('short_name', str(ref_entry.get('id', ''))))
                            link = f"../{ref_table}/{ref_entry.get('short_name', ref_entry.get('id'))}.html"
                            items_html += f"<li><a href='{link}'>{display}</a></li>"
                        items_html += "</ul>"
                        field = f'<p><strong>{col_label}:</strong>{items_html}</p>'
                    else:
                        field = f'<p><strong>{col_label}:</strong> <em>None</em></p>'
                else:
                    field = f'<p><strong>{col_label}:</strong> <em>Invalid reference config</em></p>'
        card_content += field + '\n'
    html = f"""
    <div class="table-card" id="math-{entry['id']}" style="position:relative;">
        {icons_html}
        {title_html}
        <div class="table-details">
        {card_content}
        </div>
    </div>
    """
    return html

def render_entry_form(table_name, schema, entry=None, default_entry=None):
    """
    Render a static HTML form for adding or editing an entry.
    - schema: table schema dict
    - entry: dict with existing values (for edit), or None
    - is_edit: True for edit form, False for add form
    - default_entry: dict with default values (for add form)
    """
    columns = schema.get('columns', [])
    form_fields = ""
    for col in columns:
        name = col['name']
        label = col.get('label', name)
        col_type = col.get('type', 'string')
        if col_type == 'reference':
            continue
        required = col.get('required', False)
        desc = col.get('description', '')
        if entry is not None:
            value = entry.get(name, '')
        elif default_entry is not None:
            value = default_entry.get(name, '')
        else:
            value = ''
        required_attr = 'required' if required else ''
        label = f"<label for='{name}'><strong>{label}</strong> ({col_type})</label>"
        helptext = f"<small>{desc}</small>"
        if col_type == 'array':
            # Render as a table of strings with add/remove/edit controls
            items = value if isinstance(value, list) else ([] if not value else [value])
            table_rows = ""
            import html
            for idx, item in enumerate(items):
                escaped_item = html.escape(str(item), quote=True)
                table_rows += f"""
                <tr>
                    <td><input type='text' value='{escaped_item}' data-array-index='{idx}' style='width:100%'></td>
                    <td>
                        <button type='button' onclick='removeArrayItem_{name}({idx})'>Remove</button>
                    </td>
                </tr>
                """
            input_html = f"""
            <table id='array-table-{name}' class='array-table'>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            <button type='button' onclick='addArrayItem_{name}()'>Add Item</button>
            <input type='hidden' id='{name}' name='{name}' value='{json.dumps(items)}'>
            <script>
            function updateArrayField_{name}() {{
                const table = document.getElementById('array-table-{name}');
                const items = [];
                for (const row of table.querySelectorAll('tbody tr')) {{
                    const input = row.querySelector('input[type="text"]');
                    if (input && input.value.trim()) items.push(input.value.trim());
                }}
                document.getElementById('{name}').value = JSON.stringify(items);
            }}
            function addArrayItem_{name}() {{
                const table = document.getElementById('array-table-{name}').querySelector('tbody');
                const idx = table.children.length;
                const row = document.createElement('tr');
                row.innerHTML = `<td><input type='text' value='' data-array-index='${{idx}}' style='width:100%'></td><td><button type='button' onclick='removeArrayItem_{name}(${{idx}})'>Remove</button></td>`;
                table.appendChild(row);
                row.querySelector('input').addEventListener('input', updateArrayField_{name});
                updateArrayField_{name}();
            }}
            function removeArrayItem_{name}(idx) {{
                const table = document.getElementById('array-table-{name}').querySelector('tbody');
                const rows = Array.from(table.children);
                if (rows[idx]) table.removeChild(rows[idx]);
                updateArrayField_{name}();
            }}
            // Attach listeners to existing inputs
            document.addEventListener('DOMContentLoaded', function() {{
                const table = document.getElementById('array-table-{name}').querySelector('tbody');
                for (const input of table.querySelectorAll('input[type="text"]')) {{
                    input.addEventListener('input', updateArrayField_{name});
                }}
                updateArrayField_{name}();
            }});
            </script>
            """
        elif col_type == 'boolean':
            # Render as a select dropdown for three states
            options = [
                ("", "Unspecified"),
                ("true", "Yes"),
                ("false", "No")
            ]
            selected = ""
            if value is True:
                selected = "true"
            elif value is False:
                selected = "false"
            input_html = f"<select id='{name}' name='{name}'>"
            for opt_val, opt_label in options:
                sel = "selected" if selected == opt_val else ""
                input_html += f"<option value='{opt_val}' {sel}>{opt_label}</option>"
            input_html += "</select>"
        elif col_type == 'integer':
            input_html = f"<input type='number' id='{name}' name='{name}' value='{value}' {required_attr}>"
        elif col_type == 'enum':
            options = col.get('enum', [])
            input_html = f"<select id='{name}' name='{name}' {required_attr}>"
            for opt in options:
                opt_value = opt['value']
                opt_display = opt.get('display_name', opt_value)
                selected = 'selected' if str(value) == str(opt_value) else ''
                input_html += f"<option value='{opt_value}' {selected}>{opt_display}</option>"
            input_html += "</select>"
        elif col_type == 'string':
            input_html = f"<input type='text' id='{name}' name='{name}' value='{value}' {required_attr}>"
        elif col_type == 'text':
            input_html = f"<textarea id='{name}' name='{name}' rows='4' cols='50' {required_attr}>{value}</textarea>"
        elif col_type == 'latex':
            input_html = f"<input type='text' id='{name}' name='{name}' value='{value}' {required_attr}>"
        elif col_type == 'reference':
            pass
        else:
            raise ValueError(f"Unsupported column type: {col_type}")
        form_fields += f"<div class='form-field'>{label}<br>{input_html}<br>{helptext}</div>"
    # JS for POST and download
    js = f'''
    <script>
    function formToJSON(form) {{
        const data = {{}};  // Initialize as an empty object
        for (const el of form.elements) {{
            if (!el.name) continue;
            if (el.type === 'number') {{
                data[el.name] = el.value ? Number(el.value) : null;
            }} else if (el.tagName === 'SELECT' && (el.options.length === 3) && (el.options[0].text === 'Unspecified')) {{
                // Boolean select
                if (el.value === "true") {{
                    data[el.name] = true;
                }} else if (el.value === "false") {{
                    data[el.name] = false;
                }} else {{
                    data[el.name] = null;
                }}
            }} else if (el.type === 'hidden' && el.value && el.name && el.value.startsWith('[')) {{
                // Parse JSON array for array fields
                try {{
                    data[el.name] = JSON.parse(el.value);
                }} catch (err) {{
                    data[el.name] = [];
                }}
            }} else {{
                data[el.name] = el.value;
            }}
        }}
        return data;
    }}
    async function postJSON(e) {{
        e.preventDefault();
        const form = document.getElementById('entry-form');
        const data = formToJSON(form);
        const resp = await fetch('/api/save_entry/{table_name}', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(data)
        }});
        if (resp.ok) {{
            alert('Entry saved successfully!');
            window.location.href = '/{table_name}/index.html';
        }} else {{
            let err;
            try {{ err = await resp.json(); }} catch (e) {{ err = {{}}; }}
            alert('Error saving entry: ' + (err.error || resp.status));
        }}
    }}
    </script>
    '''
    form_html = f'''
    <form id="entry-form" onsubmit="postJSON(event)">
        {form_fields}
        <button type="submit">Save Entry</button>
        <button type="button" onclick="window.history.back();" style="margin-left:1em;">Cancel</button>
    </form>
    {js}
    '''
    return form_html



def render_table_index_html(table_name, data_rows, schema, data_dir, mode, make_title=None):
    """Render the complete table page."""
    add_link = ('<div class="add-entry-link"><a href="add.html">+ Add New Entry</a></div>'
                if mode != "static" else '')
    rows_html = ""
    table_name = schema.get('table_name')
    for row in data_rows:
        rows_html += render_card(
            table_name=table_name, schema=schema, entry=row, data_dir=data_dir,  mode=mode, make_title=make_title)
    content = add_link + render_table_content(rows_html, schema)
    return render_base_page_template(
        title=schema.get('description', '') if schema else '',
        table_name=table_name,
        content=content,
        data_dir=data_dir,
        extra_scripts=get_delete_js(table_name) if mode == "server" else "",
        use_mathjax=True
    )


def render_add_entry_html(table_name, schema, data_dir):
    next_id = get_next_id(table_name, data_dir)
    default_entry = {"id": next_id}
    add_form_html = render_entry_form(table_name, schema, entry=None, default_entry=default_entry)
    title = schema.get('title', table_name.title())
    return render_base_page_template(
        title=f"Add New {title}",
        table_name=table_name,
        content=f'<h2>Add New {title}</h2>' + add_form_html,
        data_dir=data_dir,
        use_mathjax=(table_name == 'equations')
    )


def render_row_html(table_name, schema, row, data_dir, mode):
    title = schema.get('title', table_name.title())
    return render_row_page_template(
        title=title,
        table_name=table_name,
        row=row,
        data_dir=data_dir,
        mode=mode,
        use_mathjax=True
    )

def render_edit_entry_html(table_name, schema, row, data_dir):
    row_short_name = row.get('short_name') or row.get('id')
    edit_form_html = render_entry_form(table_name, schema, entry=row)
    return render_base_page_template(
        title=f"Edit {row.get('name', row_short_name)}",
        table_name=table_name,
        content=f'<h2>Edit {row.get("name", row_short_name)}</h2>' + edit_form_html,
        data_dir=data_dir,
        use_mathjax=True
    )

def render_main_index_html(tables_info, data_dir):
    main_info = load_utils.get_main_json(data_dir)
    tables_html = ""
    for table_name, info in tables_info.items():
        description = info.get('description', f'{table_name.title()} data')
        count = info.get('count', 0)
        tables_html += f"""
        <div class=\"table-card\">
            <h3><a href=\"{table_name}/index.html\">{table_name.title()}</a></h3>
            <p>{description}</p>
            <p class=\"record-count\">{count} records</p>
        </div>
        """
    # Navigation bar with About link
    nav_links = ['<a href="index.html">Home</a>']
    homepage = main_info.get("homepage")
    if homepage:
        nav_links.append(f'<a href="{homepage}" target="_blank">About</a>')
    nav_html = "\n                ".join(nav_links)
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>{main_info['title']}</title>
        <link rel=\"stylesheet\" href=\"styles.css\">
    </head>
    <body>
        <header>
            <h1>{main_info['header']}</h1>
            <p>{main_info['subtitle']}</p>
            <nav>
                {nav_html}
            </nav>
        </header>
        <main class=\"main-container\">
            <div class=\"intro\">
                <p>{main_info['description']}</p>
            </div>
            <div class=\"tables-grid\">
                {tables_html}
            </div>
        </main>
        <footer>
            <p>{main_info['footer']}</p>
        </footer>
    </body>
    </html>
    """

@functools.cache
def render_css():
    script_dir = Path(__file__).parent
    css_template = script_dir / "styles.css"
    if not css_template.exists():
        return "/* CSS template not found */"
    with open(css_template, 'r', encoding='utf-8') as src:
        return src.read()