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
    def run_generator(self, data, doi="", catalogue=None, lookup_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / '_pages/includes').mkdir(parents=True)
            outputs = [root / '_pages/includes' / name for name in ('pub_list.md', 'pub_selected.md')]
            for path in outputs: path.write_text('existing output')
            stats = root / 'stats.json'; stats.write_text(json.dumps(data))
            client = MagicMock()
            client.open_by_url.return_value.sheet1.get_all_records.return_value = [
                dict(author='Zhu Deng, Example Author', title='Example paper', journal='Test Journal', date='2026-01-01', gsid='paper:1', doi=doi, selected=1)]
            original = os.getcwd(); log = io.StringIO(); error = None
            try:
                os.chdir(root)
                with patch.dict(os.environ, {'GS_PRIVATE_KEY_ID':'SECRET-ID', 'GS_PRIVATE_KEY':'SECRET-KEY', 'OPENALEX_DATA_PATH':str(stats)}), patch('gspread.service_account_from_dict', return_value=client), patch('openalex_data.catalogue_snapshot', return_value=catalogue or {'works':{}}, side_effect=lookup_error), patch('requests.get') as altmetric, contextlib.redirect_stdout(log):
                    altmetric.return_value.status_code = 404
                    try: runpy.run_path(str(ROOT / 'publication_generator/pubGen.py'))
                    except (ValueError, RuntimeError) as exc: error = exc
            finally: os.chdir(original)
            self.assertNotIn('SECRET', log.getvalue())
            return [p.read_text() for p in outputs], error
    def valid_data(self):
        return {'schema_version':1, 'source':'OpenAlex', 'author_id':'https://openalex.org/A5088725316', 'orcid':'https://orcid.org/0000-0002-6409-9578', 'updated':'2026-11-18', 'works_count':1, 'retrieved_works_count':1, 'citedby':37, 'hindex':1, 'works':{'https://openalex.org/W1':{'doi':'10.1234/a','title':'Example paper','num_citations':37}}}
    def test_exact_match_renders_count(self):
        outputs,error=self.run_generator(self.valid_data(), '10.1234/a', self.valid_data())
        self.assertIsNone(error)
        for output in outputs: self.assertIn('OpenAlex%20citations-37',output)
    def test_title_mismatch_renders_na(self):
        fixture=self.valid_data(); fixture['works']['https://openalex.org/W1']['title']='Different paper'
        outputs,error=self.run_generator(self.valid_data(), '10.1234/a', fixture)
        self.assertIsInstance(error,ValueError)
        self.assertEqual(outputs,['existing output','existing output'])
    def test_api_failure_preserves_both_outputs(self):
        outputs,error=self.run_generator(self.valid_data(), '10.1234/a', lookup_error=RuntimeError('API failure'))
        self.assertIsInstance(error,RuntimeError)
        self.assertEqual(outputs,['existing output','existing output'])
    def test_invalid_stats_preserve_both_existing_outputs(self):
        outputs, error = self.run_generator({'publications': {}})
        self.assertIsInstance(error, ValueError)
        self.assertEqual(outputs, ['existing output', 'existing output'])
if __name__ == '__main__': unittest.main()
