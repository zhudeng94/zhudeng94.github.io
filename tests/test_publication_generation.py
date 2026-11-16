"""Exercise the actual generator with isolated, deterministic service fixtures."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'publication_generator'))
class PublicationGenerationTests(unittest.TestCase):
    def run_generator(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / '_pages/includes').mkdir(parents=True)
            outputs = [root / '_pages/includes' / name for name in ('pub_list.md', 'pub_selected.md')]
            for path in outputs: path.write_text('existing output')
            stats = root / 'stats.json'; stats.write_text(json.dumps(data))
            client = MagicMock()
            client.open_by_url.return_value.sheet1.get_all_records.return_value = [
                dict(author='Zhu Deng, Example Author', title='Example paper', journal='Test Journal', date='2026-01-01', gsid='paper:1', doi='', selected=1)]
            original = os.getcwd(); log = io.StringIO(); error = None
            try:
                os.chdir(root)
                with patch.dict(os.environ, {'GS_PRIVATE_KEY_ID':'SECRET-ID', 'GS_PRIVATE_KEY':'SECRET-KEY', 'SCHOLAR_DATA_PATH':str(stats)}), patch('gspread.service_account_from_dict', return_value=client), contextlib.redirect_stdout(log):
                    try: runpy.run_path(str(ROOT / 'publication_generator/pubGen.py'))
                    except ValueError as exc: error = exc
            finally: os.chdir(original)
            self.assertNotIn('SECRET', log.getvalue())
            return [p.read_text() for p in outputs], error
    def test_success_preserves_citation_count_and_renders_both_lists(self):
        outputs, error = self.run_generator({'publications': {'paper:1': {'num_citations': 37}}})
        self.assertIsNone(error)
        for text in outputs:
            self.assertIn('Example paper', text); self.assertIn('Citations-37-', text)
    def test_invalid_stats_preserve_both_existing_outputs(self):
        outputs, error = self.run_generator({'publications': {}})
        self.assertIsInstance(error, ValueError)
        self.assertEqual(outputs, ['existing output', 'existing output'])
if __name__ == '__main__': unittest.main()
