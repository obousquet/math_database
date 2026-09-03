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
    clusters: List[Dict[str, Any]] | None = None,
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
    # Graph hooks conventionally assign rank 0 to the greatest parameters.
    # Spell out the direction instead of relying on Graphviz's default, since
    # a graph with only same-rank blocks otherwise has no constraint ordering
    # those blocks with respect to one another.
    # Graphviz supplies node placement and ranks only.  The browser replaces
    # these straight placeholder edges with direct Bézier curves after layout;
    # this avoids Graphviz's obstacle-avoiding routes altogether.
    dot_lines = ['strict digraph "" {graph [bgcolor=transparent, rankdir=TB, newrank=true, remincross=true, splines=line];']
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
        if "peripheries" in node:
            attrs.append(f'peripheries={int(node["peripheries"])}')
        if "style" in node:
            attrs.append(f'style={node["style"]}')
        dot_lines.append(f'"{node["id"]}" [{", ".join(attrs)}];')

    # Graph hooks may identify a set of nodes that merits a visual enclosure
    # (for example, parameters mutually bounded by affine-linear functions).
    # Clusters are optional and deliberately contain only real nodes: this
    # avoids the invisible-anchor routing artefacts that the graph renderer
    # otherwise has to work around.
    for cluster_index, cluster in enumerate(clusters or []):
        node_ids = cluster.get("nodes", [])
        if len(node_ids) < 2:
            continue
        attrs = {
            "label": cluster.get("label", ""),
            "color": cluster.get("color", "#6C5CE7"),
            "fontcolor": cluster.get("fontcolor", "#4B3F72"),
            "style": cluster.get("style", "rounded,dashed"),
            "penwidth": cluster.get("penwidth", 1.25),
            "margin": cluster.get("margin", 10),
        }
        rendered_attrs = ", ".join(
            f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"
            for key, value in attrs.items()
        )
        dot_lines.append(
            f'subgraph cluster_{cluster_index} {{graph [{rendered_attrs}]; rank=same; '
            + "; ".join(f'"{node_id}"' for node_id in node_ids)
            + ";}"
        )

    # A repository graph hook may assign ranks to its nodes.  Grouping each
    # rank in a DOT ``rank=same`` block lets a condensed preorder render from
    # its sources at the top while retaining every original node.
    rank_groups = {}
    for node in nodes:
        if "rank" in node:
            rank_groups.setdefault(node["rank"], []).append(node["id"])
    ordered_ranks = sorted(rank_groups)
    rank_representatives = []
    for rank_value in ordered_ranks:
        node_ids = rank_groups[rank_value]
        # A same-rank subgraph is enough to align the nodes.  Do not add a
        # synthetic invisible point: Graphviz treats even a zero-size,
        # invisible node as an obstacle when routing visible edges, which
        # causes otherwise direct arrows to detour around rank anchors.
        dot_lines.append('{rank=same; ' + '; '.join(f'"{node_id}"' for node_id in node_ids) + ';}')
        # One real member can carry the ordering constraint for the rank.
        # Unlike a synthetic anchor it has no extra footprint for edges to
        # avoid; it is already a visible node in this graph.
        rank_representatives.append(node_ids[0])
    for upper, lower in zip(rank_representatives, rank_representatives[1:]):
        # This only establishes the sequence of rank blocks.  Giving this
        # arbitrary representative chain a large weight pins columns together
        # and defeats dot's crossing minimizer, so retain only the smallest
        # useful rank weight.
        dot_lines.append(f'"{upper}" -> "{lower}" [style=invis, weight=1, minlen=1];')
    
    for edge_idx, edge in enumerate(edges):
        attrs = []
        # An SVG id lets the browser replace Graphviz's placeholder with a
        # direct curve and attach an exact-midpoint witness label afterwards.
        attrs.append(f'id="graph-edge-{edge_idx}"')
        attrs.append('label=""')
        if "color" in edge:
            attrs.append(f'color="{edge["color"]}"')
        else:
            attrs.append('color="#888888"')
        if "arrowhead" in edge:
            attrs.append(f'arrowhead={edge["arrowhead"]}')
        if "style" in edge:
            attrs.append(f'style={edge["style"]}')
        if "penwidth" in edge:
            attrs.append(f'penwidth={float(edge["penwidth"]):g}')
        # Overlay edges must not perturb the Hasse-backbone layout.  Dot uses
        # only the reduced homogeneous relations to choose a compact ordering;
        # the browser draws all other direct facts afterwards.
        if edge.get("constraint") is False:
            attrs.append('constraint=false')
        attrs.append('arrowsize=0.7')
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
        if entry and table == "parameters":
            # Graph popups should stay readable at a glance.  Parameter pages
            # retain the complete record, while this concise database-owned
            # summary is intentionally the only prose shown in the graph.
            summary = (
                entry.get("graph_summary")
                or entry.get("description")
                or entry.get("definition")
            )
            title = html.escape(entry.get("name", node.get("label", node["id"])))
            symbol = render_utils.render_latex_field("Symbol", entry.get("symbol", ""))
            summary_html = render_utils.render_text_field(
                "Summary",
                summary or "No concise summary has been recorded yet. Open the parameter page for the full catalogue entry.",
                data_dir,
            )
            # Pages declare a site-wide <base> URL, so popup links must be
            # relative to that base rather than to graphs/hasse.html.
            relationships_html = render_utils.render_parameter_relationships(entry, cache)
            row_link = f'{table}/{entry["short_name"]}.html' if entry.get("short_name") else None
            title_html = f'<h3><a href="{row_link}" class="table-title-link">{title}</a></h3>' if row_link else f"<h3>{title}</h3>"
            card_html = f'<div class="table-card">{title_html}{symbol}{summary_html}{relationships_html}</div>'
        elif entry:
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
                if "peripheries" in item:
                    attrs.append(f'peripheries={int(item["peripheries"])}')
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
                edge_attrs.append(f'penwidth={float(item.get("penwidth", 1.5)):g}')
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
    const edgeGeometry = {json.dumps([{
        "source": edge["source"],
        "target": edge["target"],
        "label": edge.get("label"),
        "labelColor": edge.get("label_color", "#555555"),
        "penwidth": edge.get("penwidth", 1),
    } for edge in edges])};
    const legendItems = {json.dumps(legend_items_data)};
    function normalizeLatex(latex) {{
        // The catalogue has historically accepted both bare TeX and TeX
        // already wrapped in a math delimiter.  This renderer owns the
        // display delimiter, so remove exactly one outer pair first.
        latex = (latex || '').trim();
        const delimiters = [['$$', '$$'], ['\\\\[', '\\\\]'], ['\\\\(', '\\\\)'], ['$', '$']];
        for (const [opening, closing] of delimiters) {{
            if (latex.startsWith(opening) && latex.endsWith(closing)
                && latex.length > opening.length + closing.length) {{
                return latex.slice(opening.length, -closing.length).trim();
            }}
        }}
        return latex;
    }}
    function typesetModalContent(content) {{
        // Cards inserted into the modal are not present when the page-level
        // MathJax initializer runs.  In particular, generic class cards use
        // .latex-equation/data-latex wrappers, whose contents need delimiters
        // before MathJax can recognise them as mathematics.
        content.querySelectorAll('.latex-equation').forEach(function(equation) {{
            const latex = normalizeLatex(equation.getAttribute('data-latex'));
            if (latex) equation.textContent = '$$' + latex + '$$';
        }});
        if (window.MathJax && typeof MathJax.typesetPromise === 'function') {{
            MathJax.typesetClear([content]);
            MathJax.typesetPromise([content]);
        }}
    }}
    function showEdgeCard(edgeIdx) {{
        var edgeCard = edgeCards['__label__' + edgeIdx] || edgeCards['__edge__' + edgeIdx];
        if (!edgeCard) return;
        var modal = document.getElementById('node-modal');
        var content = document.getElementById('node-modal-content');
        content.innerHTML = edgeCard;
        modal.style.display = 'block';
        typesetModalContent(content);
    }}
    function clipToBox(box, origin, direction) {{
        const dx = direction.x - origin.x;
        const dy = direction.y - origin.y;
        const halfWidth = Math.max(1, box.width / 2);
        const halfHeight = Math.max(1, box.height / 2);
        const scale = 1 / Math.max(Math.abs(dx) / halfWidth, Math.abs(dy) / halfHeight, 1e-6);
        return {{x: origin.x + dx * scale, y: origin.y + dy * scale}};
    }}
    function quadraticPoint(start, control, end, t) {{
        const u = 1 - t;
        return {{
            x: u * u * start.x + 2 * u * t * control.x + t * t * end.x,
            y: u * u * start.y + 2 * u * t * control.y + t * t * end.y,
        }};
    }}
    function curveHitsNode(start, control, end, box) {{
        // Sampling is sufficient here: nodes are substantially larger than
        // the curve stroke and labels, and a small padding keeps paths from
        // visually grazing their boundary.
        const padding = 7;
        for (let step = 1; step < 40; step += 1) {{
            const point = quadraticPoint(start, control, end, step / 40);
            if (point.x >= box.x - padding && point.x <= box.x + box.width + padding
                && point.y >= box.y - padding && point.y <= box.y + box.height + padding) {{
                return true;
            }}
        }}
        return false;
    }}
    function labelHitsNode(start, control, end, label, box) {{
        if (!label) return false;
        const midpoint = quadraticPoint(start, control, end, 0.5);
        const halfWidth = Math.max(36, label.length * 6.1 + 12) / 2 + 4;
        const halfHeight = 13;
        return midpoint.x + halfWidth >= box.x && midpoint.x - halfWidth <= box.x + box.width
            && midpoint.y + halfHeight >= box.y && midpoint.y - halfHeight <= box.y + box.height;
    }}
    function chooseCurve(source, target, otherNodes, index, label) {{
        const dx = target.center.x - source.center.x, dy = target.center.y - source.center.y;
        const distance = Math.hypot(dx, dy) || 1;
        const middle = {{x: (source.center.x + target.center.x) / 2,
                        y: (source.center.y + target.center.y) / 2}};
        // Prefer gentle, alternating curves.  Keep the bend bounded: an
        // overlay that escapes far beyond the placed graph is harder to read
        // than one that briefly passes behind an intervening node.
        const signs = index % 2 ? [1, -1] : [-1, 1];
        const maxBend = Math.min(160, Math.max(36, distance * 0.18));
        const bends = Array.from(new Set(
            [0, 12, 24, 40, 60, 84, 112, maxBend].filter(function(bend) {{ return bend <= maxBend; }})
        ));
        let best = null;
        for (const bend of bends) {{
            for (const sign of signs) {{
                const control = {{x: middle.x - dy / distance * bend * sign,
                                 y: middle.y + dx / distance * bend * sign}};
                const start = clipToBox(source.box, source.center, control);
                const end = clipToBox(target.box, target.center, control);
                const collisions = otherNodes.reduce(function(total, node) {{
                    return total + Number(curveHitsNode(start, control, end, node.box)
                        || labelHitsNode(start, control, end, label, node.box));
                }}, 0);
                if (!best || collisions < best.collisions) {{
                    best = {{start, control, end, collisions}};
                }}
                if (collisions === 0) {{
                    return {{start, control, end}};
                }}
            }}
        }}
        return best;
    }}
    function drawDirectCurves() {{
        const svg = document.querySelector('#graph svg');
        if (!svg) return;
        const namespace = 'http://www.w3.org/2000/svg';
        let defs = svg.querySelector('defs');
        if (!defs) {{ defs = document.createElementNS(namespace, 'defs'); svg.insertBefore(defs, svg.firstChild); }}
        let marker = defs.querySelector('#direct-edge-arrow');
        if (!marker) {{
            marker = document.createElementNS(namespace, 'marker');
            marker.setAttribute('id', 'direct-edge-arrow');
            marker.setAttribute('viewBox', '0 -5 10 10');
            marker.setAttribute('refX', '9'); marker.setAttribute('refY', '0');
            marker.setAttribute('markerWidth', '6'); marker.setAttribute('markerHeight', '6');
            marker.setAttribute('orient', 'auto');
            const arrow = document.createElementNS(namespace, 'path');
            arrow.setAttribute('d', 'M0,-5L10,0L0,5Z'); arrow.setAttribute('fill', 'context-stroke');
            marker.appendChild(arrow); defs.appendChild(marker);
        }}
        const nodes = new Map();
        svg.querySelectorAll('g.node').forEach(function(node) {{
            const title = node.querySelector('title');
            if (!title) return;
            const box = node.getBBox();
            nodes.set(title.textContent, {{box: box, center: {{x: box.x + box.width / 2, y: box.y + box.height / 2}}}});
        }});
        edgeGeometry.forEach(function(edge, index) {{
            const edgeGroup = svg.querySelector('#graph-edge-' + index);
            const source = nodes.get(edge.source), target = nodes.get(edge.target);
            if (!edgeGroup || !source || !target) return;
            edgeGroup.querySelectorAll('.edge-witness-label').forEach(function(label) {{ label.remove(); }});
            const others = Array.from(nodes.entries())
                .filter(function(entry) {{ return entry[0] !== edge.source && entry[0] !== edge.target; }})
                .map(function(entry) {{ return entry[1]; }});
            const {{start, control, end}} = chooseCurve(source, target, others, index, edge.label);
            const path = edgeGroup.querySelector('path');
            if (!path) return;
            path.setAttribute('d', `M${{start.x}},${{start.y}} Q${{control.x}},${{control.y}} ${{end.x}},${{end.y}}`);
            path.setAttribute('stroke-width', edge.penwidth);
            path.setAttribute('marker-end', 'url(#direct-edge-arrow)');
            edgeGroup.querySelectorAll('polygon').forEach(function(polygon) {{ polygon.style.display = 'none'; }});
            if (!edge.label) return;
            const midpoint = {{x: (start.x + 2 * control.x + end.x) / 4, y: (start.y + 2 * control.y + end.y) / 4}};
            const group = document.createElementNS(namespace, 'g');
            group.setAttribute('class', 'edge-witness-label'); group.style.cursor = 'pointer';
            const width = Math.max(36, edge.label.length * 6.1 + 12), height = 18;
            const rect = document.createElementNS(namespace, 'rect');
            rect.setAttribute('x', midpoint.x - width / 2); rect.setAttribute('y', midpoint.y - height / 2);
            rect.setAttribute('width', width); rect.setAttribute('height', height); rect.setAttribute('rx', '3');
            rect.setAttribute('fill', '#ffffff'); rect.setAttribute('fill-opacity', '0.88');
            rect.setAttribute('stroke', edge.labelColor); rect.setAttribute('stroke-width', '0.7'); group.appendChild(rect);
            const text = document.createElementNS(namespace, 'text');
            text.setAttribute('x', midpoint.x); text.setAttribute('y', midpoint.y + 3.5);
            text.setAttribute('text-anchor', 'middle'); text.setAttribute('font-size', '10'); text.setAttribute('fill', edge.labelColor);
            text.textContent = edge.label; group.appendChild(text);
            group.addEventListener('click', function(event) {{ event.stopPropagation(); showEdgeCard(index); }});
            // Keep the label in the same transformed SVG group as the path.
            // Appending it at the root SVG level put it in a different
            // coordinate system after d3-graphviz's fit transform, which is
            // why labels could appear detached from their arrows.
            edgeGroup.appendChild(group);
        }});
    }}
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
                drawDirectCurves();
                d3.selectAll('.node').on('click', function(event) {{
                    var node_id = d3.select(this).select('title').text();
                    if (!node_id) {{
                        node_id = d3.select(this).select('text').text();
                    }}
                    
                    var modal = document.getElementById('node-modal');
                    var content = document.getElementById('node-modal-content');
                    content.innerHTML = nodeCards[node_id] || '<div class="table-card"><h3>' + node_id + '</h3></div>';
                    modal.style.display = 'block';
                    typesetModalContent(content);
                }});
                // Native DOT edge labels are part of the edge SVG group.  A
                // click anywhere on that group (especially its witness
                // label) opens the witness card when one is available.
                d3.selectAll('.edge').on('click', function(event) {{
                    var edgeId = this.id || '';
                    var match = edgeId.match(/^graph-edge-(\\d+)$/);
                    if (!match) return;
                    var edgeIdx = parseInt(match[1]);
                    showEdgeCard(edgeIdx);
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
    clusters = graph_data.get("clusters", [])
    graph_name = graph_info.get("name", short_name)
    return render_graph_html(nodes, edges, legend=legend, clusters=clusters, graph_name=graph_name, data_dir=data_dir, base_url=base_url, mode=mode)
