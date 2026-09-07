"""Browser regressions: uv run --with playwright python test_graph_readability.py.

Set GRAPH_SITE_DIR to a generated Combinatorial Parameters docs directory to
also exercise real SVG geometry and the popup/zoom interactions offline.
"""
import json
import os
from pathlib import Path
import unittest
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


class ReadabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = sync_playwright().start()
        cls.browser = cls.driver.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.driver.stop()

    def test_optimizer_and_reachability(self):
        page = self.browser.new_page()
        page.add_script_tag(path=str(Path(__file__).parent / 'js/graph-readability.js'))
        result = page.evaluate("""() => {
            const nodes=[
                {id:'a',x:0,y:0,rank:0,width:40}, {id:'b',x:600,y:0,rank:0,width:40},
                {id:'c',x:600,y:100,rank:1,width:40}, {id:'d',x:0,y:100,rank:1,width:40},
                {id:'e',x:900,y:100,rank:1,width:40}];
            const edges=[{source:'a',target:'c'},{source:'b',target:'d'}];
            const before=structuredClone(nodes);
            const metrics=GraphReadability.optimize(nodes,edges,[{nodes:['c','e']}]);
            const up=[...GraphReadability.reachable('c',edges,true)];
            const down=[...GraphReadability.reachable('a',edges)];
            return {nodes,before,metrics,up,down};
        }""")
        self.assertLess(result['metrics']['after']['score'], result['metrics']['before']['score'])
        self.assertEqual(result['metrics']['after']['crossings'], 0)
        for old, new in zip(result['before'], result['nodes']):
            self.assertEqual((old['y'], old['rank']), (new['y'], new['rank']))
        row = sorted((n for n in result['nodes'] if n['rank'] == 1), key=lambda n: n['x'])
        self.assertEqual(abs([n['id'] for n in row].index('c') - [n['id'] for n in row].index('e')), 1)
        for a, b in zip(row, row[1:]):
            self.assertGreater(b['x'] - a['x'], (a['width'] + b['width'])/2)
        self.assertCountEqual(result['up'], ['c', 'a'])
        self.assertCountEqual(result['down'], ['a', 'c'])
        self.assertEqual(page.evaluate("() => [...GraphReadability.reachable('a', [{source:'b', target:'a', reverseArrow:true}])].sort()"), ['a', 'b'])
        page.close()

    @unittest.skipUnless(os.environ.get('GRAPH_SITE_DIR'), 'set GRAPH_SITE_DIR for generated-site checks')
    def test_generated_site(self):
        root = Path(os.environ['GRAPH_SITE_DIR']).resolve()
        page = self.browser.new_page(viewport={'width': 1800, 'height': 1200})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def local(route):
            suffix = urlparse(route.request.url).path.split('/Combinatorial-Parameters/', 1)[1]
            path = root / suffix
            if path.is_file():
                route.fulfill(path=str(path))
            else:
                route.abort()

        page.route('https://obousquet.github.io/Combinatorial-Parameters/**', local)
        page.goto('https://obousquet.github.io/Combinatorial-Parameters/graphs/hasse.html', wait_until='networkidle')
        page.wait_for_selector('svg[data-readability-ready]', timeout=90000)
        metrics = json.loads(page.locator('#graph svg').get_attribute('data-layout-metrics'))
        print('Layout metrics:', metrics)
        self.assertLessEqual(metrics['after']['score'], metrics['before']['score'])
        geometry = page.evaluate("""() => {
            const nodes=[...document.querySelectorAll('#graph g.node')].map(n=>({
                id:n.querySelector('title').textContent, box:n.getBoundingClientRect(),
                dy:n.transform.baseVal.consolidate()?.matrix.f||0}));
            let overlaps=0;
            nodes.forEach((a,i)=>nodes.slice(i+1).forEach(b=> {
                if(a.box.left<b.box.right && b.box.left<a.box.right && a.box.top<b.box.bottom && b.box.top<a.box.bottom) overlaps++;
            }));
            return {overlaps, shiftedY:nodes.filter(n=>n.dy!==0).length};
        }""")
        self.assertEqual(geometry, {'overlaps': 0, 'shiftedY': 0})
        regions = page.evaluate("""() => {
            const groups=new Map();
            document.querySelectorAll('#graph g.node[data-horizontal-group]').forEach(n=> {
                const k=Number(n.dataset.horizontalGroup), b=n.getBoundingClientRect();
                if(!groups.has(k)) groups.set(k,[]);
                groups.get(k).push([b.left,b.right]);
            });
            return [...groups].sort((a,b)=>a[0]-b[0]).map(([k,boxes])=>({
                group:k,left:Math.min(...boxes.map(b=>b[0])),right:Math.max(...boxes.map(b=>b[1]))}));
        }""")
        self.assertEqual([r['group'] for r in regions], [0,1,2,3])
        for a,b in zip(regions,regions[1:]):
            self.assertLess(a['right'],b['left'])
        visible = """() => [...document.querySelectorAll('.edge-witness-label')].filter(e=>getComputedStyle(e).visibility==='visible').length"""
        self.assertEqual(page.evaluate(visible), 0)
        page.select_option('#graph-witness-mode', 'always')
        count = page.locator('.edge-witness-label').count()
        self.assertGreater(count, 0)
        self.assertEqual(page.evaluate(visible), count)
        page.select_option('#graph-witness-mode', 'never')
        self.assertEqual(page.evaluate(visible), 0)
        page.select_option('#graph-witness-mode', 'auto')
        # Hover a real edge stroke, not the hidden label or a synthetic event.
        point = page.evaluate("""() => {
            const path=document.querySelector('#graph g.edge[id] path:not(.edge-hit-area)');
            const p=path.getPointAtLength(path.getTotalLength()*0.3);
            return new DOMPoint(p.x,p.y).matrixTransform(path.getScreenCTM()).toJSON();
        }""")
        page.mouse.move(point['x'], point['y'])
        self.assertGreater(page.evaluate(visible), 0)
        page.mouse.move(1, 1)
        # Drive the public d3 zoom API; the mutation observer must update labels.
        page.evaluate("""() => {
            const g=d3.select('#graph').graphviz();
            g.zoomSelection().call(g.zoomBehavior().scaleBy, 5);
        }""")
        page.wait_for_function("() => document.querySelector('#graph svg').classList.contains('witness-labels-visible')")
        self.assertEqual(page.evaluate(visible), count)
        page.click('#graph-fit')
        page.check('#graph-focus-mode')
        target = page.locator('#graph g.node').filter(has=page.locator('title', has_text='#parameters/5')).first
        target.click(force=True)
        self.assertGreater(page.locator('#graph .graph-dimmed').count(), 0)
        self.assertEqual(page.locator('#graph .graph-selected').count(), 1)
        self.assertFalse(page.locator('#node-modal').is_visible())
        page.click('#graph-clear-focus')
        self.assertEqual(page.locator('#graph .graph-dimmed').count(), 0)
        page.uncheck('#graph-focus-mode')
        compact = page.locator('#graph g.node').filter(has_text='equivalents').first
        compact.click(force=True)
        self.assertTrue(page.locator('#node-modal').is_visible())
        self.assertGreater(page.locator('.graph-equivalents a').count(), 1)
        page.wait_for_selector('#node-modal-content mjx-container')
        self.assertEqual(page.locator('#node-modal-content mjx-merror').count(), 0)
        page.locator('#node-modal button').click()
        page.select_option('#graph-witness-mode', 'always')
        page.locator('.edge-witness-label').first.click(force=True)
        self.assertTrue(page.locator('#node-modal').is_visible())
        self.assertEqual(page.locator('.graph-equivalents').count(), 0)
        page.wait_for_selector('#node-modal-content mjx-container')
        self.assertEqual(page.locator('#node-modal-content mjx-merror').count(), 0)
        page.locator('#node-modal button').click()
        page.select_option('#graph-witness-mode', 'auto')
        page.screenshot(path='/tmp/readability-after.png', full_page=True)
        self.assertEqual(errors, [])
        page.close()


if __name__ == '__main__':
    unittest.main()
