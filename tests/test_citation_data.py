import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'publication_generator'))
from citation_data import load_citation_data, validate

DATA = {'publications': {'id': {'num_citations': 12}}}
class CitationDataTests(unittest.TestCase):
    def test_valid_local_file_without_network(self):
        with tempfile.TemporaryDirectory() as d, patch('citation_data.requests.Session') as session:
            p = Path(d) / 'data.json'; p.write_text(json.dumps(DATA))
            self.assertEqual(load_citation_data(p), DATA); session.assert_not_called()
    def test_invalid_data(self):
        for data in [None, {}, {'publications': {}}, {'publications': {'id': {'num_citations': -1}}}]:
            with self.subTest(data=data), self.assertRaises(ValueError): validate(data)
    def test_missing_local_file_does_not_fallback(self):
        with patch('citation_data.requests.Session') as session:
            with self.assertRaises(FileNotFoundError): load_citation_data('/nonexistent/citation.json')
            session.assert_not_called()
    def test_remote_valid(self):
        with patch('citation_data.requests.Session') as factory:
            response = factory.return_value.__enter__.return_value.get.return_value
            response.json.return_value = DATA
            self.assertEqual(load_citation_data(), DATA)
            response.raise_for_status.assert_called_once()
    def test_remote_invalid_json(self):
        with patch('citation_data.requests.Session') as factory:
            factory.return_value.__enter__.return_value.get.return_value.json.side_effect = ValueError('bad')
            with self.assertRaises(ValueError): load_citation_data()
    def test_http_error(self):
        with patch('citation_data.requests.Session') as factory:
            response = factory.return_value.__enter__.return_value.get.return_value
            response.raise_for_status.side_effect = RuntimeError('HTTP failure')
            with self.assertRaises(RuntimeError): load_citation_data()
            response.json.assert_not_called()
if __name__ == '__main__': unittest.main()
