# Math Database

A Python application that generates static HTML websites from structured mathematical data, perfect for hosting on GitHub Pages.

Requires Python 3.10 or later.

## Features

- **Data-driven**: Organizes data in a structured directory format with schemas
- **Customizable rendering**: Each table has its own Python render module for flexible HTML generation
- **Cross-referencing**: Easily link between tables using hashtags like `#<table>/<short_name>`, `#<table>/<id>`, or simply `#<short_name>`/`#<id>` if unique. Reference fields in schemas are auto-populated with links to related entries.
- **Graph generation**: Add a `make_graph.py` file to create interactive graph visualizations from your data
- **Bibliography support**: Add a `.bib` file and link it in `main.json` to generate a bibliography page; reference entries via `\cite{key}` or `#bib/key`
- **GitHub Pages ready**: Generates static HTML suitable for GitHub Pages hosting
- **Mathematical notation**: Supports LaTeX rendering with MathJax
- **Responsive design**: Mobile-friendly CSS with modern styling

## Directory Structure

```
data/
├── [table_name]/
│   ├── schema.json          # Table schema definition
│   ├── render_[table_name].py  # Custom HTML rendering logic
│   ├── 001_record1.json     # Individual data records
│   ├── 002_record2.json
│   └── ...
└── [another_table]/
    ├── schema.json
    ├── render_[another_table].py
    └── ...
```

## Usage

1. **Add your data**: Create subdirectories in `data/` for each table
2. **Define schema**: Add `schema.json` files describing your data structure
3. **Create render modules**: Add `render_[table_name].py` files for HTML generation
4. **Add data records**: Create JSON files for individual records
5. **Cross-reference entries**: Use hashtags like `#<table>/<short_name>`, `#<table>/<id>`, or simply `#<short_name>`/`#<id>` in any field to link to other entries. If you define a field with type `reference` in your schema, it will be auto-populated with links to related entries.
6. **Add graphs (optional)**: Create a `make_graph.py` file in your data directory and reference it in `main.json` to generate interactive graph pages
7. **Add a bibliography (optional)**: Add a `.bib` file and reference it in `main.json` under the `bibliography` key; a bibliography page will be generated automatically
8. **Reference bibliography entries**: Use `\cite{key}` in LaTeX fields or `#bib/key` in text fields to link to bibliography entries
9. **Generate static website**: Run the generator with the following command:

  ```bash
  python generate_website.py --data_dir DATA_DIR [--output_dir OUTPUT_DIR] [--deploy true]
  ```

  - `--data_dir DATA_DIR` (required): Path to your data directory (e.g. `data/`)
  - `--output_dir OUTPUT_DIR` (optional): Path to the output directory (default: `../docs` relative to your data directory)
  - `--deploy true` (optional): Use the `deploy_url` in `main.json` as the base URL for generated links. Use this when publishing to a GitHub Pages project site.

  Example:
  ```bash
  python generate_website.py --data_dir data/ --output_dir docs/ --deploy true
  ```

The generated website will be placed in the output directory, ready for GitHub Pages. The output directory is cleared before generation, so ensure `--output_dir` points only to generated site files.

## Graph readability

Graph pages offer optional **Focus on selection** (linear ancestors and
descendants plus directly attached overlays), **Clear focus**, and **Fit graph**.
Turn focus off to open parameter cards. Witness labels appear on edge hover or
at readable zoom levels; the selector can instead show all labels or hide them.
The underlying edge colors, dashes and separation-strength widths are unchanged.

A graph hook may return `layout: {"optimize_horizontal": True}` to enable a
bounded browser-side crossing/span cleanup using all displayed edges. It never
changes node ranks or vertical positions and keeps affine clusters together.
It scores straight edge chords as a proxy for the gently curved final paths;
this is a heuristic, not a guarantee of a globally minimum-crossing drawing.
Node `equivalent_refs` lists can accompany compact equality labels: the renderer
shows the full list of linked parameters in the popup. An edge's optional
`hierarchy: false` excludes it from transitive focus traversal, not from display
or horizontal optimization (use this for nonlinear or variant-only overlays).

An optional integer node field `horizontal_group` assigns left-to-right regions
when every node supplies it. The optimizer reserves disjoint horizontal bands
and optimizes within each one, preserving ranks and affine blocks. The hook must
assign all members of a block to the same group. Layout scores then compare
against the initial region-constrained placement; honoring regions takes priority
over the unconstrained crossing score. Combinatorial Parameters uses full base
affine reachability after equality collapse for E-only, both, Size-only, and
neither-known regions; these labels do not assert incomparability.

Browser regression checks:

```bash
uv run --with playwright python test_graph_readability.py
GRAPH_SITE_DIR=../Combinatorial-Parameters/docs uv run --with playwright python test_graph_readability.py
```

Chromium must be installed for Playwright. The second command also checks the
generated graph, fixed vertical positions, overlap-free nodes, equality cards,
focus/reset controls and witness-label zoom behavior against local site assets.

## Editing Data Locally

To edit the database and preview changes locally, use the server:

```bash
python server.py
```

This will start a local server that allows you to add, edit, and delete entries directly in the database via the web interface. All changes are made to your local data directory.

After making local modifications, you can commit and push your changes, then make a pull request (PR) to update the static website on GitHub Pages.

## Example Data Structure

### Schema (schema.json)

Optional columns may set `hide_when_empty: true` to omit their card field when
the value is absent, null, or an empty string (zero and false remain visible).
Relationship statements support `incomparability_strength` values `affine`
and `functional`; the scope is displayed in parameter relationship lists.
Missing legacy scope remains simply "incomparable" and is not inferred.

```json
{
  "table_name": "equations",
  "description": "Mathematical equations and their properties",
  "columns": [
    {
      "name": "id",
      "type": "string",
      "description": "Unique identifier",
      "required": true
    },
    {
      "name": "name",
      "type": "string",
      "description": "Equation name",
      "required": true
    }
  ]
}
```

### Data Record (001_example.json)
```json
{
  "id": "001",
  "name": "Pythagorean Theorem",
  "equation": "a^2 + b^2 = c^2",
  "category": "geometry"
}
```

### Render Module (render_equations.py)
```python
def render_row(data):
    """Render a single row to HTML."""
    return f"<div class='equation'><h3>{data['name']}</h3></div>"

def render_table_page(rows, schema):
    """Render complete page HTML."""
    content = "".join(render_row(row) for row in rows)
    return f"<html><body>{content}</body></html>"
```

## Getting Started

1. Clone this repository
2. Set up your data following the structure above
3. Run the generator:
   ```bash
   python generate_website.py --data_dir data/ --output_dir docs/
   ```
4. Open `docs/index.html` in your browser to preview
5. Deploy to GitHub Pages:
   - Go to your repository Settings → Pages
   - Under "Source", select "Deploy from a branch"
   - Select the "main" branch and "/docs" folder
   - Click "Save"
   - Your site will be available at `https://yourusername.github.io/repository-name`

## Visualizing in VS Code

To preview the generated website directly in VS Code:

### Option 1: Simple Browser (for quick preview)
```bash
# Open the HTML file directly in VS Code's Simple Browser
# Note: CSS may not load properly with this method
code docs/index.html
```

### Option 2: Local HTTP Server (recommended)
```bash
# Navigate to the docs directory
cd docs

# Start a local HTTP server
python3 -m http.server 8000

# Then open http://localhost:8000 in VS Code's Simple Browser
# This ensures CSS and other assets load correctly
```

The local HTTP server method is recommended as it properly serves all static assets (CSS, images, etc.) and provides the most accurate preview of how your site will appear when deployed.

## Included Examples

This repository includes example data for:
- **Equations**: Famous mathematical equations with LaTeX notation
- **Mathematicians**: Biographical information about notable mathematicians

## GitHub Pages Setup

1. Go to your repository settings
2. Navigate to "Pages" section
3. Set source to "Deploy from a branch"
4. Select "main" branch and "/docs" folder
5. Your site will be available at `https://yourusername.github.io/your-repo-name`

For a project site, add a `deploy_url` to `data/main.json` and generate with deploy mode so links include the repository path:

```json
{
  "deploy_url": "https://yourusername.github.io/your-repo-name/"
}
```

```bash
python generate_website.py --data_dir data/ --output_dir docs/ --deploy true
```

## Customization

- Modify `styles.css` to change the appearance
- Edit render modules to customize HTML output
- Add new tables by creating new subdirectories in `data/`
- Add a `make_graph.py` file to create custom graph visualizations
- Add a `.bib` file and reference it in `main.json` to enable bibliography features
- Use hashtags like `#<table>/<short_name>`, `#<table>/<id>`, or simply `#<short_name>`/`#<id>` for cross-referencing entries
- Define fields of type `reference` in your schema to auto-populate links to related entries
- Use `\cite{key}` or `#bib/key` in your data to create links to bibliography entries
- Extend the main generator script for additional functionality

## Workflow Summary

- Use `generate_website.py --data_dir DATA_DIR --output_dir DOCS_DIR --deploy true` to generate static HTML pages for a GitHub Pages project site (no editing capability).
- Use `server.py` to run a local server for editing and previewing the database interactively.
- After editing locally, commit and push your changes, then make a PR to update the static site on GitHub Pages.
