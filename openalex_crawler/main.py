"""Fetch the ORCID-verified OpenAlex author and complete work list."""
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'publication_generator'))
from openalex_data import AUTHOR, ORCID, normalize_doi, validate

BASE = 'https://api.openalex.org'

def get_json(session, path, params=None):
    try:
        response = session.get(BASE + path, params=params, timeout=(10, 30))
        if response.status_code != 200:
            raise RuntimeError(f'OpenAlex HTTP {response.status_code}; existing snapshot retained')
        return response.json()
    except requests.RequestException:
        # Do not log request URLs, headers, API keys or response bodies.
        raise RuntimeError('OpenAlex transport failure; existing snapshot retained') from None
    except ValueError:
        raise RuntimeError('Invalid OpenAlex JSON; existing snapshot retained') from None

def collect(session):
    author = get_json(session, '/authors/orcid:0000-0002-6409-9578')
    if author.get('id') != AUTHOR or author.get('orcid') != ORCID:
        raise ValueError('OpenAlex author identity changed; manual review required')
    works = {}
    expected = author.get('works_count')
    if type(expected) is not int or not 0 < expected <= 10000:
        raise ValueError('Unexpected OpenAlex work count')
    page = 1
    total = None
    while True:
        payload = get_json(session, '/works', {'filter': 'author.id:A5088725316', 'per_page': 100, 'page': page, 'sort': 'cited_by_count:desc'})
        observed = payload.get('meta', {}).get('count')
        if type(observed) is not int or not 0 < observed <= 10000:
            raise ValueError('Invalid OpenAlex result count')
        if total is not None and observed != total:
            raise ValueError('Result count changed during retrieval')
        total = observed
        for w in payload['results']:
            ident = w['id']
            if ident in works or not any(a.get('author', {}).get('id') == AUTHOR for a in w.get('authorships', [])):
                raise ValueError('Duplicate or wrong-author work in OpenAlex response')
            works[ident] = {'doi': normalize_doi(w.get('doi')), 'title': w.get('display_name', ''),
                            'num_citations': w['cited_by_count'], 'year': w.get('publication_year')}
        if page * 100 >= total:
            break
        page += 1
    if len(works) != total:
        raise ValueError('Incomplete OpenAlex response')
    return validate({'schema_version': 1, 'source': 'OpenAlex', 'author_id': AUTHOR, 'orcid': ORCID,
                     'updated': datetime.now(timezone.utc).isoformat(), 'works_count': expected, 'retrieved_works_count': total,
                     'citedby': author['cited_by_count'], 'hindex': author['summary_stats']['h_index'], 'works': works})

def main():
    with requests.Session() as session:
        session.headers['User-Agent'] = 'zhudeng94-academic-homepage/1.0 (OpenAlex citation updater)'
        if os.environ.get('OPENALEX_API_KEY'):
            session.headers['Authorization'] = 'Bearer ' + os.environ['OPENALEX_API_KEY']
        data = collect(session)
    output = Path('openalex_crawler/results/openalex_data.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(output)
    print(f"Validated {data['retrieved_works_count']} retrieved OpenAlex works; author profile reports {data['works_count']}; source timestamp {data['updated']}")

if __name__ == '__main__':
    main()
