import copy
import importlib.util
from pathlib import Path
import sys
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'publication_generator'))
from openalex_data import AUTHOR, ORCID, validate, match_work, citation_badge, normalize_doi, catalogue_snapshot
spec = importlib.util.spec_from_file_location('openalex_crawler', ROOT / 'openalex_crawler/main.py')
crawler = importlib.util.module_from_spec(spec); spec.loader.exec_module(crawler)

AUTHOR_DATA = {'id':AUTHOR, 'orcid':ORCID, 'works_count':2, 'cited_by_count':9, 'summary_stats':{'h_index':2}}
WORK = {'id':'https://openalex.org/W1', 'doi':'https://doi.org/10.1234/a', 'display_name':'Paper A', 'cited_by_count':8, 'publication_year':2025, 'authorships':[{'author':{'id':AUTHOR}}]}
PAYLOAD = {'meta':{'count':1}, 'results':[WORK]}

class OpenAlexTests(unittest.TestCase):
    def collect(self, author=AUTHOR_DATA, payload=PAYLOAD):
        with patch.object(crawler, 'get_json', side_effect=[author,payload]):
            return crawler.collect(None)
    def test_complete_snapshot_and_index_lag(self):
        d=self.collect(); self.assertEqual(d['works_count'],2); self.assertEqual(d['retrieved_works_count'],1)
        self.assertEqual(d['citedby'],9)
    def test_wrong_author_refused(self):
        with self.assertRaises(ValueError): self.collect(dict(AUTHOR_DATA, orcid='wrong'))
    def test_partial_response_refused(self):
        with self.assertRaises(ValueError): self.collect(payload={'meta':{'count':2},'results':[WORK]})
    def test_duplicate_ids_refused(self):
        with self.assertRaises(ValueError): self.collect(payload={'meta':{'count':2},'results':[WORK,WORK]})
    def test_wrong_work_author_refused(self):
        with self.assertRaises(ValueError): self.collect(payload={'meta':{'count':1},'results':[dict(WORK,authorships=[])]})
    def test_failed_fetch_preserves_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            old = os.getcwd()
            try:
                os.chdir(folder)
                output = Path('openalex_crawler/results/openalex_data.json')
                output.parent.mkdir(parents=True); output.write_text('old snapshot')
                with patch.object(crawler, 'collect', side_effect=ValueError('Wrong identity')):
                    with self.assertRaises(ValueError): crawler.main()
                self.assertEqual(output.read_text(), 'old snapshot')
            finally: os.chdir(old)
    def test_doi_normalization(self):
        self.assertEqual(normalize_doi(' https://doi.org/10.1234/AbC '),'10.1234/abc')
        self.assertEqual(normalize_doi(float('nan')),'')
    def test_strict_title_mismatch_not_accepted(self):
        d=self.collect(); self.assertIsNone(match_work(d,'10.1234/a','Paper B'))
        self.assertIn('N/A',citation_badge(d,'10.1234/a','Paper B'))
        self.assertIn('citations-8',citation_badge(d,'10.1234/a','Paper A'))
    def reviewed_fixture(self):
        return {'works': {'https://openalex.org/W4416097588': {
            'doi': '10.26599/cs.2025.9510006',
            'title': 'Projection of global daily CO 2 emissions in 2025',
            'num_citations': 3}}}
    def test_owner_reviewed_title_exception(self):
        d=self.reviewed_fixture()
        self.assertIsNotNone(match_work(d,'10.26599/CS.2025.9510006','Projection of global daily CO2 emission in 2025'))
    def test_reviewed_exception_does_not_allow_other_work_id(self):
        d=self.reviewed_fixture();d['works']['https://openalex.org/W999']=d['works'].pop('https://openalex.org/W4416097588')
        self.assertIsNone(match_work(d,'10.26599/cs.2025.9510006','Projection of global daily CO2 emission in 2025'))
    def test_reviewed_exception_does_not_allow_changed_source_title(self):
        d=self.reviewed_fixture();d['works']['https://openalex.org/W4416097588']['title']='Projection of global daily CO2 emissions in 2026'
        self.assertIsNone(match_work(d,'10.26599/cs.2025.9510006','Projection of global daily CO2 emission in 2025'))
    def test_reviewed_exception_does_not_allow_changed_catalogue_title(self):
        self.assertIsNone(match_work(self.reviewed_fixture(),'10.26599/cs.2025.9510006','Projection of global daily CO2 emission in 2026'))
    def test_reviewed_exception_still_rejects_ambiguous_doi(self):
        d=self.reviewed_fixture();d['works']['https://openalex.org/W999']=dict(d['works']['https://openalex.org/W4416097588'])
        self.assertIsNone(match_work(d,'10.26599/cs.2025.9510006','Projection of global daily CO2 emission in 2025'))
    def test_ambiguous_doi_not_accepted(self):
        d=self.collect();d['works']['https://openalex.org/W2']=dict(d['works']['https://openalex.org/W1'])
        self.assertIsNone(match_work(d,'10.1234/a','Paper A'))
    def test_alias_response_excluded(self):
        with patch('requests.Session') as factory:
            r=factory.return_value.__enter__.return_value.get.return_value
            r.status_code=200;r.json.return_value=PAYLOAD
            with self.assertRaises(ValueError): catalogue_snapshot(['10.1234/b'])
    def test_empty_catalogue_refused(self):
        with self.assertRaises(ValueError): catalogue_snapshot([])
    def test_zero_match_response_refused(self):
        with patch('requests.Session') as factory:
            r=factory.return_value.__enter__.return_value.get.return_value
            r.status_code=200;r.json.return_value={'meta':{'count':0},'results':[]}
            with self.assertRaises(ValueError): catalogue_snapshot(['10.1234/a'])
    def test_duplicate_catalogue_results_refused(self):
        with patch('requests.Session') as factory:
            r=factory.return_value.__enter__.return_value.get.return_value
            r.status_code=200;r.json.return_value={'meta':{'count':2},'results':[WORK,WORK]}
            with self.assertRaises(ValueError): catalogue_snapshot(['10.1234/a'])
    def test_boolean_count_rejected(self):
        d=self.collect();d['citedby']=True
        with self.assertRaises(ValueError): validate(d)
    def test_http_error_redacted(self):
        session=MagicMock();session.get.return_value.status_code=403
        with self.assertRaisesRegex(RuntimeError,'HTTP 403'): crawler.get_json(session,'/authors/test')
    def test_catalogue_bad_response_raises(self):
        with patch('requests.Session') as factory:
            r=factory.return_value.__enter__.return_value.get.return_value
            r.status_code=200;r.json.return_value={'meta':{'count':2},'results':[WORK]}
            with self.assertRaises(ValueError): catalogue_snapshot(['10.1234/a'])
if __name__=='__main__':unittest.main()
