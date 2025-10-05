import json
import load_utils
from typing import List, Dict, Any
import render_utils
import re
import html

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
    legend: List[Dict[str, Any]],
    graph_name: str = "Graph",
    data_dir: str = None,
    base_url: str = "/",
    mode: str = "static",
) -> str:
    """
    Args:
        nodes: List of node dicts with keys "id", "label", "ref", etc.
        edges: List of edge dicts with keys "source", "target", "ref", "label", etc.
        legend: List of legend items, each a dict with keys "type" (which can be "node" or "edge") and the  style attributes for that type (e.g. color, shape, fillcolor).
        graph_name: Title of the graph page.
        data_dir: Path to data directory for loading entries.
        base_url: Base URL for links.
        mode: "static" or "server" for rendering mode.
    """
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
    
    # Add invisible edge label nodes for clickability
    for edge_idx, edge in enumerate(edges):
        edge_label_node = f"__edge__{edge_idx}"
        edge_label = edge.get("label", "•")  # Use bullet point if no label
        # Create a small clickable node for the edge label
        dot_lines.append(f'"{edge_label_node}" [shape=box, style=filled, fillcolor="#f0f0f0", fontsize=10, width=0.3, height=0.3, label="{edge_label}"];')
    
    # Now add edges with invisible labels (the label is on the node instead)
    for edge_idx, edge in enumerate(edges):
        edge_label_node = f"__edge__{edge_idx}"
        attrs = []
        attrs.append('label=""')  # No label on edge itself
        if "color" in edge:
            attrs.append(f'color="{edge["color"]}"')
        else:
            attrs.append('color="#888888"')
        if "arrowhead" in edge:
            attrs.append(f'arrowhead={edge["arrowhead"]}')
        if "style" in edge:
            attrs.append(f'style={edge["style"]}')
        attrs.append('arrowsize=0.7')
        
        # Split the edge into two parts: source -> label_node -> target
        dot_lines.append(f'"{edge["source"]}" -> "{edge_label_node}" [{", ".join(attrs)}, dir=none];')
        dot_lines.append(f'"{edge_label_node}" -> "{edge["target"]}" [{", ".join(attrs)}];')
    
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
                mode=mode
            )
        else:
            card_html = f'<div class="table-card"><h3>{node.get("label", node["id"])} (no details)</h3></div>'
        node_cards[node["id"]] = card_html.replace('"', '\"').replace("'", "\'")

    # Prepare edge cards
    edge_cards = {}
    for edge_idx, edge in enumerate(edges):
        ref = edge.get("ref")
        label_ref = edge.get("label_ref")
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
                    mode=mode
                )
                edge_cards['__edge__' + str(edge_idx)] = card_html.replace('"', '\"').replace("'", "\'")
        if label_ref:
            table, entry = cache.lookup(label_ref)
            if entry:
                card_html = render_utils.render_card(
                    table_name=table,
                    schema=cache.get_table_schema(table),
                    entry=entry,
                    data_dir=data_dir,
                    mode=mode
                )
                edge_cards['__label__' + str(edge_idx)] = card_html.replace('"', '\"').replace("'", "\'")
    
    # Build legend as individual DOT graphs for each item (will be embedded in HTML table)
    legend_items_data = []
    
    if legend:
        for i, item in enumerate(legend):
            item_type = item.get('type', 'node')
            text = item.get('text', item.get('label', 'Unnamed'))
            
            # Create a minimal DOT graph for this item
            dot_lines = ['digraph "" {']
            dot_lines.append('graph [bgcolor=transparent, margin=0];')
            dot_lines.append('node [label="\\N", penwidth=1.8];')
            dot_lines.append('edge [arrowhead=vee];')
            
            if item_type == 'node':
                # Create a sample node
                attrs = []
                label = item.get('label', '')
                attrs.append(f'label="{label}"')
                
                if "color" in item:
                    attrs.append(f'color="{item["color"]}"')
                if "fillcolor" in item:
                    attrs.append(f'fillcolor="{item["fillcolor"]}"')
                    attrs.append('style=filled')
                if "shape" in item:
                    attrs.append(f'shape={item["shape"]}')
                if "style" in item:
                    attrs.append(f'style={item["style"]}')
                
                dot_lines.append(f'"item" [{", ".join(attrs)}];')
                
            elif item_type == 'edge':
                # Create a horizontal edge with smaller dots and shorter arrow
                dot_lines.append('"src" [shape=point, width=0.08, height=0.08];')
                dot_lines.append('"dst" [shape=point, width=0.08, height=0.08];')
                
                edge_attrs = []
                if "color" in item:
                    edge_attrs.append(f'color="{item["color"]}"')
                else:
                    edge_attrs.append('color="#888888"')
                if "arrowhead" in item:
                    edge_attrs.append(f'arrowhead={item["arrowhead"]}')
                if "style" in item:
                    edge_attrs.append(f'style={item["style"]}')
                edge_attrs.append('penwidth=1.5')
                edge_attrs.append('minlen=3')
                
                dot_lines.append(f'"src" -> "dst" [{", ".join(edge_attrs)}];')
                dot_lines.append('{rank=same; "src"; "dst";}')
            
            dot_lines.append('}')
            legend_item_dot_src = " ".join(dot_lines)
            
            legend_items_data.append({
                'index': i,
                'type': item_type,
                'text': text,
                'dot_src': legend_item_dot_src
            })
    
    # HTML template
    head = """
    <link rel="stylesheet" href="styles/graph.css" />
    """
    html_str = f"""
    <div id='graph-container-main' class='graph-container-main'>
        <button id='legend-button' onclick='document.getElementById("legend-modal").style.display="block"' style='position:absolute; top:10px; left:10px; z-index:100; padding:0.5em 1em; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:1em;'>📊 Legend</button>
        <div id='graph'></div>
        <div id='node-modal' class='node-modal'>
            <div id='node-modal-content' class='node-modal-content'></div>
            <button onclick='document.getElementById("node-modal").style.display="none"' style='margin:1em auto;display:block;'>Close</button>
        </div>
        <div id='legend-modal' class='node-modal' style='display:none;'>
            <div class='node-modal-content' style='max-width: 800px; min-width: 600px;'>
                <h3 style='margin-bottom:1em;'>Legend</h3>
                <table id='legend-table' style='width:100%; border-collapse: collapse;'>
                </table>
            </div>
            <button onclick='document.getElementById("legend-modal").style.display="none"' style='margin:1em auto;display:block;'>Close</button>
        </div>
    </div>
    """
    scripts = f"""
    <script src="js/jquery.min.js" type="text/javascript"></script>
    <script src="js/d3.min.js"></script>
    <script src="js/hpcc.min.js"></script>
    <script src="js/d3-graphviz.js"></script>
    <script>
    const nodeCards = {json.dumps(node_cards)};
    const edgeCards = {json.dumps(edge_cards)};
    const legendItems = {json.dumps(legend_items_data)};
    document.addEventListener('DOMContentLoaded', function() {{
        console.log('Initializing graph visualization');
        const graphContainer = d3.select('#graph-container-main');
        let width = graphContainer.node().clientWidth;
        let height = graphContainer.node().clientHeight;
        if (height < 600) height = 600;
        const graph = d3.select('#graph');
        console.log('Rendering main graph with dimensions:', width, 'x', height);
        graph.graphviz({{useWorker: false}})
            .width(width)
            .height(height)
            .fit(true)
            .renderDot(`{dot_src}`)
            .on('end', function() {{
                console.log('Main graph rendering complete');
                d3.selectAll('.node').on('click', function(event) {{
                    var node_id = d3.select(this).select('title').text();
                    if (!node_id) {{
                        node_id = d3.select(this).select('text').text();
                    }}
                    
                    // Check if this is an edge label node
                    if (node_id.startsWith('__edge__')) {{
                        var edge_idx = parseInt(node_id.replace('__edge__', ''));
                        // Get the edge card by index
                        var edge_card = edgeCards[node_id];
                        var edge_label_key = '__label__' + edge_idx;
                        // If there's a label card, show it instead
                        if (edgeCards[edge_label_key]) {{
                            edge_card = edgeCards[edge_label_key];
                        }}
                        var modal = document.getElementById('node-modal');
                        var content = document.getElementById('node-modal-content');
                        content.innerHTML = edge_card || '<div class="table-card"><h3>Edge ' + edge_idx + '</h3></div>';
                        modal.style.display = 'block';
                        if (window.MathJax) MathJax.typesetPromise([content]);
                    }} else {{
                        // Regular node
                        var modal = document.getElementById('node-modal');
                        var content = document.getElementById('node-modal-content');
                        content.innerHTML = nodeCards[node_id] || '<div class="table-card"><h3>' + node_id + '</h3></div>';
                        modal.style.display = 'block';
                        if (window.MathJax) MathJax.typesetPromise([content]);
                    }}
                }});
            }});
        
        // Render legend table when legend button is clicked
        let legendRendered = false;
        document.getElementById('legend-button').addEventListener('click', function() {{
            if (!legendRendered) {{
                const legendTable = document.getElementById('legend-table');
                
                // Create table rows for each legend item
                legendItems.forEach(function(item, idx) {{
                    const row = document.createElement('tr');
                    row.style.borderBottom = '1px solid #eee';
                    
                    // SVG cell
                    const svgCell = document.createElement('td');
                    svgCell.style.padding = '5px';
                    svgCell.style.width = '100px';
                    svgCell.style.verticalAlign = 'middle';
                    const svgDiv = document.createElement('div');
                    svgDiv.id = 'legend-item-' + idx;
                    svgDiv.style.width = '100%';
                    svgDiv.style.height = '40px';
                    svgCell.appendChild(svgDiv);
                    
                    // Text cell
                    const textCell = document.createElement('td');
                    textCell.style.padding = '5px';
                    textCell.style.verticalAlign = 'middle';
                    textCell.style.fontSize = '0.9em';
                    textCell.textContent = item.text;
                    
                    row.appendChild(svgCell);
                    row.appendChild(textCell);
                    legendTable.appendChild(row);
                    
                    // Render the individual graph for this item (without worker to avoid conflicts)
                    d3.select('#legend-item-' + idx)
                        .graphviz({{useWorker: false}})
                        .width(100)
                        .height(40)
                        .fit(true)
                        .renderDot(item.dot_src);
                }});
                
                legendRendered = true;
            }}
        }});
        
        // Close modals when clicking outside
        document.addEventListener('mousedown', function(e) {{
            var nodeModal = document.getElementById('node-modal');
            var legendModal = document.getElementById('legend-modal');
            
            if (nodeModal.style.display === 'block' && !nodeModal.contains(e.target)) {{
                nodeModal.style.display = 'none';
            }}
            
            if (legendModal.style.display === 'block' && !legendModal.contains(e.target)) {{
                legendModal.style.display = 'none';
            }}
        }});
    }});
    </script>
    """
    return render_utils.render_base_page_template(
        title=graph_name,
        table_name=None,
        content=html_str,
        data_dir=data_dir,
        extra_scripts=scripts,
        extra_head=head,
        use_mathjax=True,
        base_url=base_url
    )

def render_named_graph_html(data_dir: str, short_name: str, base_url: str = "/", mode: str = "static") -> str:
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
    legend = graph_data.get("legend", [])
    graph_name = graph_info.get("name", short_name)
    return render_graph_html(nodes, edges, legend=legend, graph_name=graph_name, data_dir=data_dir, base_url=base_url, mode=mode)


