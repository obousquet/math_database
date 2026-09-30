import unittest
from unittest.mock import patch

import render_graph_utils


class _EmptyCache:
    def lookup(self, reference):
        return None, None


class GraphDotTests(unittest.TestCase):
    @patch.object(render_graph_utils.render_utils, "render_base_page_template")
    @patch.object(render_graph_utils.load_utils, "get_table_entries_cache")
    def test_parallel_edges_and_composite_node_styles(self, get_cache, render_page):
        get_cache.return_value = _EmptyCache()
        render_page.side_effect = lambda **kwargs: kwargs["extra_scripts"]
        html = render_graph_utils.render_graph_html(
            nodes=[{
                "id": "a", "label": "A", "shape": "box",
                "fillcolor": "#ffffff", "style": "filled,dashed",
            }, {"id": "b", "label": "B"}],
            edges=[
                {"source": "a", "target": "b", "label": "first"},
                {"source": "a", "target": "b", "label": "second"},
            ],
            legend=[],
            data_dir="unused",
        )

        self.assertIn('digraph ""', html)
        self.assertNotIn('strict digraph', html)
        self.assertEqual(html.count('id="graph-edge-'), 2)
        self.assertIn('style="filled,dashed"', html)


if __name__ == "__main__":
    unittest.main()
