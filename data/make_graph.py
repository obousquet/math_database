import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from load_utils import TableEntriesCache
from typing import Dict, Any, List

def generate(cache: TableEntriesCache) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate nodes and edges for the graph.
    Nodes: equations and mathematicians.
    Edges: author relationship from equations to mathematicians.
    Returns:
        {
            "nodes": [ {"id": str, "label": str, "ref": str, "type": str} ],
            "edges": [ {"source": str, "target": str, "ref": str, "label": str} ]
        }
    """
    nodes = []
    edges = []
    # Add mathematician nodes
    for m in cache.get("mathematicians"):
        nodes.append({
            "id": f'#mathematicians/{m["id"]}',
            "label": m.get("name", m["id"]),
            "ref": f'#mathematicians/{m["id"]}',
            "type": "mathematician",
            "shape": "ellipse",
            "color": "#4F81BD",
            "fillcolor": "#D9E1F2",
        })
    # Add equation nodes and author edges
    for eq in cache.get("equations"):
        latex = eq.get("equation", "")
        name = eq.get("name", eq["id"])
        nodes.append({
            "id": f'#equations/{eq["id"]}',
            "label": f'{name}\n${latex}$',
            "ref": f'#equations/{eq["id"]}',
            "type": "equation",
            "shape": "box",
            "color": "#C0504D",
            "fillcolor": "#F2DCDB",
        })
        author = eq.get("author", [])
        _, author_entry = cache.lookup(author)
        if author_entry:
            author_id = f'#mathematicians/{author_entry["id"]}'
            edges.append({
                "source": f'#equations/{eq["id"]}',
                "target": author_id,
                "ref": '',
                "label": "author",
                "style": "dashed",
                "color": "#C0504D",
                "arrowhead": "open",
            })
    return {"nodes": nodes, "edges": edges}
