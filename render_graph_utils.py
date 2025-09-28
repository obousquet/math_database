import importlib.util
import json
from pathlib import Path
import load_utils
import pygraphviz as pgv
from typing import List, Dict, Any
import render_utils
import re

# Node: {"id": str, "label": str, "ref": str}
# Edge: {"source": str, "target": str, "ref": str, "label": str}

def replace_latex(label):
    # Find all instances of $...$ and replace with \(\displaystyle{...}\)
    label = re.sub(r'\$(.*?)\$', r'\\(\\displaystyle{\1}\\)', label)
    label = label.replace('\\', '\\\\')
    return label

def render_graph_html(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    page_url_lookup: Dict[str, str],
    graph_name: str = "Graph",
    data_dir: str = None
) -> str:
    """
    Renders a graph using pygraphviz and returns HTML for embedding in a webpage.
    Nodes and edges are clickable and link to their corresponding table row pages.
    The graph is zoomable using panzoom.js.
    Args:
        nodes: List of nodes, each with 'id', 'label', and 'ref' (database reference).
        edges: List of edges, each with 'source', 'target', and 'ref' (may contain 'label').
        page_url_lookup: Dict mapping database references to their corresponding page URLs.
        graph_name: Title for the graph.
    Returns:
        HTML string to embed the graph in a webpage.
    """
    # Create the graph
    G = pgv.AGraph(strict=False, directed=True)
    for node in nodes:
        raw_label = node.get("label", node["id"])
        node_kwargs = {
            "label": replace_latex(raw_label),
            "URL": page_url_lookup.get(node["ref"], "#"),
            "tooltip": raw_label
        }
        for key in node.keys():
            if key in ["shape", "color", "fillcolor"]:
                node_kwargs[key] = node[key]
        if "fillcolor" in node:
            node_kwargs["style"] = node_kwargs.get("style", "") + ",filled"
        G.add_node(node["id"], **node_kwargs)
    for edge in edges:
        url = page_url_lookup.get(edge.get("ref"), "#") if edge.get("ref") else "#"
        raw_label = edge.get("label", "")
        label = replace_latex(raw_label)
        edge_kwargs = {
            "label": label,
            "URL": url,
            "tooltip": raw_label
        }
        for key in edge.keys():
            if key in ["arrowhead", "style", "color"]:
                edge_kwargs[key] = edge[key]
        G.add_edge(
            edge["source"],
            edge["target"],
            **edge_kwargs
        )
    # Render to SVG
    svg_data = G.draw(format="svg", prog="dot")
    # pygraphviz returns bytes, decode to string
    svg_str = svg_data.decode("utf-8") if isinstance(svg_data, bytes) else svg_data
    # Remove width/height from SVG for better scaling
    svg_str = re.sub(r'width="[^"]+"', 'width="100%"', svg_str)
    svg_str = re.sub(r'height="[^"]+"', 'height="100%"', svg_str)

    html = f"""
    <div style='width:100%;height:600px;border:1px solid #ccc;overflow:hidden;'>
        <div id='graph-container' style='width:100%;height:100%;'>
            {svg_str}
        </div>
    </div>
    """
    scripts = """
    <script src='https://unpkg.com/@panzoom/panzoom@9.4.0/dist/panzoom.min.js'></script>
    <script src='https://polyfill.io/v3/polyfill.min.js?features=es6'></script>
    <script id='MathJax-script' async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const container = document.getElementById('graph-container');
            const svg = container.querySelector('svg');
            // Replace SVG <text> with foreignObject for MathJax
            if (svg) {
                const texts = svg.querySelectorAll('text');
                let foundLatex = false;
                texts.forEach(function(t) {
                    if (t.textContent && t.textContent.match(/\\(.*\\)/)) {
                        foundLatex = true;
                        const x = t.getAttribute('x');
                        const y = t.getAttribute('y');
                        const fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
                        fo.setAttribute('x', x-100);
                        fo.setAttribute('y', y-12);
                        fo.setAttribute('width', '200');
                        fo.setAttribute('height', '100');
                        const div = document.createElement('div');
                        div.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml');
                        div.className = 'mathjax-latex';
                        div.style.fontSize = '14px';
                        div.style.textAlign = 'center';
                        div.innerHTML = t.textContent;
                        fo.appendChild(div);
                        t.parentNode.replaceChild(fo, t);
                    }
                });
                // Target all mathjax-latex divs for typesetting
                const latexDivs = svg.querySelectorAll('div.mathjax-latex');
                MathJax.typesetPromise(Array.from(latexDivs));
            }
            if (svg) {
                svg.style.width = '100%';
                svg.style.height = '100%';
                Panzoom(svg, {
                    maxScale: 5,
                    minScale: 0.2,
                    contain: 'outside',
                });
            }
        }});
    </script>
    """
    return render_utils.render_base_page_template(
            title=graph_name,
            table_name=None,
            content=html,
            data_dir=data_dir,
            extra_scripts=scripts,
            use_mathjax=False
    )

def render_named_graph_html(data_dir: str, short_name: str) -> str:
    """
    Renders a graph by short_name, loading the correct module and function from main.json.
    """
    cache = load_utils.get_table_entries_cache(data_dir)
    generate_func, graph_info = load_utils.get_graph_info(short_name, data_dir)
    if not generate_func:
        return f"<div class='error'>Graph '{short_name}' not found.</div>"
    graph_data = generate_func(cache)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    # Build page_url_lookup for all refs
    page_url_lookup = {}
    for node in nodes:
        ref = node.get("ref")
        if ref:
            url, _ = cache.get_url(ref)
            if url:
                page_url_lookup[ref] = url
    for edge in edges:
        ref = edge.get("ref")
        if ref and ref not in page_url_lookup:
            url, _ = cache.get_url(ref)
            if url:
                page_url_lookup[ref] = url
    graph_name = graph_info.get("name", short_name)
    return render_graph_html(nodes, edges, page_url_lookup, graph_name=graph_name, data_dir=data_dir)


