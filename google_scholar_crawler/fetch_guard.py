"""Bound Scholar requests and report safe diagnostics without bypassing challenges."""
from contextlib import contextmanager
from urllib.parse import urlsplit
from unittest.mock import patch
import requests

class ScholarAccessStopped(SystemExit):
    """Stop before scholarly retries access denials or opens a CAPTCHA solver."""

def inspect_response(response):
    status = response.status_code
    content_type = response.headers.get('Content-Type', '').split(';')[0]
    print(f'Scholar HTTP {status}; content-type={content_type}; bytes={len(response.content)}', flush=True)
    html = response.text.lower()
    challenge = any(marker in html for marker in (
        'gs_captcha_ccl', 'id="recaptcha"', 'captcha-form', 'rc-doscaptcha-body',
        'our systems have detected unusual traffic', 'verify you are human'))
    if challenge:
        raise ScholarAccessStopped('Scholar returned a verification challenge. Stopping without solving or bypassing it; existing data is unchanged.')
    if status in (401, 403, 429):
        raise ScholarAccessStopped(f'Scholar returned HTTP {status}. Stopping without changing sessions or proxies; existing data is unchanged. This status alone does not establish the cause.')
    response.raise_for_status()

@contextmanager
def scholar_fetch_guard():
    original = requests.Session.request
    def guarded(session, method, url, *args, **kwargs):
        if urlsplit(url).hostname != 'scholar.google.com':
            return original(session, method, url, *args, **kwargs)
        # Do not output headers, cookies, query strings, response bodies or exception messages.
        try:
            response = original(session, method, url, *args, **kwargs)
        except requests.RequestException as exc:
            print(f'Scholar transport exception: {type(exc).__name__}', flush=True)
            raise
        inspect_response(response)
        return response
    with patch.object(requests.Session, 'request', guarded):
        yield
