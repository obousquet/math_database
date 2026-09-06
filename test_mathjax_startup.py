"""Guard single-pass startup and configuration-before-loader ordering."""

import unittest

from render_utils import get_mathjax_head, get_mathjax_scripts


class MathJaxStartupTests(unittest.TestCase):
    def test_configuration_precedes_async_loader(self):
        head = get_mathjax_head()
        self.assertLess(head.index('window.MathJax ='), head.index('id="MathJax-script"'))

    def test_fields_are_prepared_before_one_default_typeset(self):
        head = get_mathjax_head()
        self.assertIn(".latex-equation[data-latex]", head)
        self.assertIn("eq.textContent =", head)
        self.assertLess(head.index('eq.textContent ='), head.index('defaultPageReady()'))
        self.assertEqual(head.count('defaultPageReady()'), 1)
        self.assertIn('return MathJax.startup.defaultPageReady();', head)

    def test_no_second_document_wide_pass(self):
        self.assertEqual(get_mathjax_scripts(), '')
        self.assertNotIn('typesetPromise()', get_mathjax_head())


if __name__ == '__main__':
    unittest.main()
