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
    data_dir: str = None,
    base_url: str = "./" 
) -> str:
    # Build DOT source for graphviz.js
    dot_lines = ['strict digraph "" {graph [bgcolor=transparent];']
    dot_lines.append('node [label="\\N", penwidth=1.8];')
    dot_lines.append('edge [arrowhead=vee];')
    for node in nodes:
        attrs = []
        label = node.get("label", node["id"])
        attrs.append(f'label="{label}"')
        if "color" in node:
            attrs.append(f'color="{node["color"]}"')
        if "fillcolor" in node:
            attrs.append(f'fillcolor="{node["fillcolor"]}"')
            attrs.append('style=filled')
        if "shape" in node:
            attrs.append(f'shape={node["shape"]}')
        if "style" in node:
            attrs.append(f'style={node["style"]}')
        dot_lines.append(f'"{node["id"]}" [{", ".join(attrs)}];')
    for edge in edges:
        attrs = []
        if "label" in edge:
            label = edge["label"].replace('"', '\"')
            attrs.append(f'label="{label}"')
        if "color" in edge:
            attrs.append(f'color="{edge["color"]}"')
        if "arrowhead" in edge:
            attrs.append(f'arrowhead={edge["arrowhead"]}')
        if "style" in edge:
            attrs.append(f'style={edge["style"]}')
        dot_lines.append(f'"{edge["source"]}" -> "{edge["target"]}" [{", ".join(attrs)}];')
    dot_lines.append('}')
    dot_src = " ".join(dot_lines)

    # Prepare node cards (simplified)
    node_cards = {}
    cache = load_utils.get_table_entries_cache(data_dir)
    for node in nodes:
        ref = node.get("ref")
        entry = None
        table = None
        if ref:
            table, entry = cache.lookup(ref)
        if entry:
            card_html = render_utils.render_card(
                table_name=table,
                schema=cache.get_table_schema(table),
                entry=entry,
                data_dir=data_dir,
                mode="static"
            )
        else:
            card_html = f'<div class="table-card"><h3>{node.get("label", node["id"])} (no details)</h3></div>'
        node_cards[node["id"]] = card_html.replace('"', '\"').replace("'", "\'")

    # HTML template
    head = """
    <link rel="stylesheet" href="/styles/graph.css" />
    """
    html = f"""
    <div id='graph-container-main' class='graph-container-main'>
        <div id='graph'></div>
        <div id='node-modal' class='node-modal'>
            <div id='node-modal-content' class='node-modal-content'></div>
            <button onclick='document.getElementById("node-modal").style.display="none"' style='margin:1em auto;display:block;'>Close</button>
        </div>
    </div>
    """
    scripts = f"""
    <script src="/js/jquery.min.js" type="text/javascript"></script>
    <script src="/js/d3.min.js"></script>
    <script src="/js/hpcc.min.js"></script>
    <script src="/js/d3-graphviz.js"></script>
    <script>
    const nodeCards = {json.dumps(node_cards)};
    document.addEventListener('DOMContentLoaded', function() {{
        const graphContainer = d3.select('#graph-container-main');
        let width = graphContainer.node().clientWidth;
        let height = graphContainer.node().clientHeight;
        if (height < 600) height = 600;
        const graph = d3.select('#graph');
        graph.graphviz({{useWorker: true}})
            .width(width)
            .height(height)
            .fit(true)
            .renderDot(`{dot_src}`)
            .on('end', function() {{
                d3.selectAll('.node').on('click', function() {{
                    var node_id = d3.select(this).attr('id');
                    var node_id = d3.select(this).select('title').text();
                    if (!node_id) {{
                        node_id = d3.select(this).select('text').text();
                    }}
                    var modal = document.getElementById('node-modal');
                    var content = document.getElementById('node-modal-content');
                    content.innerHTML = nodeCards[node_id] || '<div class="table-card"><h3>' + node_id + '</h3></div>';
                    modal.style.display = 'block';
                    if (window.MathJax) MathJax.typesetPromise([content]);
                }});
            }});
        // Close modal when clicking outside
        document.addEventListener('mousedown', function(e) {{
            var modal = document.getElementById('node-modal');
            if (modal.style.display === 'block' && !modal.contains(e.target)) {{
                modal.style.display = 'none';
            }}
        }});
    }});
    </script>
    """
    return render_utils.render_base_page_template(
        title=graph_name,
        table_name=None,
        content=html,
        data_dir=data_dir,
        extra_scripts=scripts,
        extra_head=head,
        use_mathjax=False,
        base_url=base_url
    )

def render_named_graph_html(data_dir: str, short_name: str, base_url: str) -> str:
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
    return render_graph_html(nodes, edges, page_url_lookup, graph_name=graph_name, data_dir=data_dir, base_url=base_url)


