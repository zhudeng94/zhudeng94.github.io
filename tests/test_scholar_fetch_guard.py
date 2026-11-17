import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'google_scholar_crawler'))
from fetch_guard import inspect_response, scholar_fetch_guard, ScholarAccessStopped

def response(status=200, body='<html>profile</html>'):
    r = requests.Response(); r.status_code=status; r._content=body.encode(); r.headers['Content-Type']='text/html'; return r

class ScholarGuardTests(unittest.TestCase):
    def test_valid_profile(self): inspect_response(response())
    def test_denials_stop_without_swallowing_by_library_exception_handler(self):
        for status in (401,403,429):
            with self.subTest(status=status), self.assertRaises(ScholarAccessStopped): inspect_response(response(status))
        self.assertFalse(issubclass(ScholarAccessStopped, Exception))
    def test_challenges_stop_even_with_http_200(self):
        for body in ('<div id="gs_captcha_ccl">', 'Our systems have detected unusual traffic'):
            with self.assertRaises(ScholarAccessStopped): inspect_response(response(body=body))
    def test_no_sensitive_body_logging(self):
        log=io.StringIO()
        with contextlib.redirect_stdout(log): inspect_response(response(body='SECRET_CONTENT'))
        self.assertNotIn('SECRET_CONTENT', log.getvalue())
    def test_transient_http_error_remains_error(self):
        with self.assertRaises(requests.HTTPError): inspect_response(response(503))
    def test_wrapper_makes_exactly_one_request_and_is_restored(self):
        with patch.object(requests.Session,'request',return_value=response(403)) as original:
            with scholar_fetch_guard(), self.assertRaises(ScholarAccessStopped):
                requests.Session().get('https://scholar.google.com/citations?user=test')
            self.assertIs(requests.Session.request, original)
            self.assertEqual(original.call_count, 1)
    def test_transport_exception_logs_type_only(self):
        log=io.StringIO()
        with patch.object(requests.Session,'request',side_effect=requests.Timeout('SECRET_URL')), contextlib.redirect_stdout(log):
            with scholar_fetch_guard(), self.assertRaises(requests.Timeout):
                requests.Session().get('https://scholar.google.com/citations?user=test')
        self.assertIn('Timeout',log.getvalue());self.assertNotIn('SECRET_URL',log.getvalue())
    def test_other_hosts_unmodified(self):
        with patch.object(requests.Session,'request',return_value=response(403)) as original:
            with scholar_fetch_guard():
                r=requests.Session().get('https://example.org/')
            self.assertEqual(r.status_code,403);self.assertEqual(original.call_count,1)
if __name__=='__main__':unittest.main()
