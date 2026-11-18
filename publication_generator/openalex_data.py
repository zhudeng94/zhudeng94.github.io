"""Strict OpenAlex snapshot contract; no fallback to Scholar or inferred zeros."""
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote

AUTHOR = 'https://openalex.org/A5088725316'
ORCID = 'https://orcid.org/0000-0002-6409-9578'

def normalize_doi(value):
    if not isinstance(value, str):
        return ''
    value = unquote(value.strip()).lower()
    value = re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value)
    return value if re.fullmatch(r'10\.\d{4,9}/\S+', value) else ''

def count(value):
    if type(value) is not int or value < 0:
        raise ValueError('Invalid OpenAlex count')
    return value

def validate(data):
    if (not isinstance(data, dict) or data.get('source') != 'OpenAlex'
        or data.get('schema_version') != 1 or data.get('author_id') != AUTHOR
        or data.get('orcid') != ORCID or not data.get('updated')):
        raise ValueError('Wrong OpenAlex snapshot identity or schema')
    for key in ('citedby', 'hindex', 'works_count', 'retrieved_works_count'):
        count(data.get(key))
    works = data.get('works')
    if not isinstance(works, dict) or not works or len(works) != data['retrieved_works_count']:
        raise ValueError('Incomplete OpenAlex work list')
    for ident, work in works.items():
        if not re.fullmatch(r'https://openalex.org/W\d+', ident):
            raise ValueError('Invalid work ID')
        count(work.get('num_citations'))
        if work.get('doi') and normalize_doi(work['doi']) != work['doi']:
            raise ValueError('Unnormalized DOI')
    return data

def load_data(path):
    if not path:
        raise ValueError('OPENALEX_DATA_PATH is required; refusing a Scholar fallback')
    return validate(json.loads(Path(path).read_text(encoding='utf-8')))

def normalize_title(value):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', str(value)).casefold())

def match_work(data, doi, title=None):
    doi = normalize_doi(doi)
    matches = [dict(w, id=i) for i, w in data['works'].items() if doi and w['doi'] == doi]
    # Ambiguous identifiers are not arbitrarily resolved or summed.
    if len(matches) != 1:
        return None
    if title is not None and (not normalize_title(title) or normalize_title(title) != normalize_title(matches[0].get('title', ''))):
        return None
    return matches[0]

def citation_badge(data, doi, title):
    work = match_work(data, doi, title)
    if work is None:
        return '<span title="No unique exact DOI and title match in OpenAlex">OpenAlex citations: N/A</span> '
    return (f"<a href='{work['id']}'><img alt='OpenAlex citations: {work['num_citations']}' "
            f"src='https://img.shields.io/badge/OpenAlex%20citations-{work['num_citations']}-white'></a> ")


def catalogue_snapshot(dois):
    """Match curated DOI records directly, independently of OpenAlex author clustering."""
    import requests
    import os
    wanted = sorted({normalize_doi(d) for d in dois} - {''})
    if not wanted:
        raise ValueError('Empty DOI catalogue; retaining previous output')
    result = {'works': {}}
    with requests.Session() as session:
        if os.environ.get('OPENALEX_API_KEY'):
            session.headers['Authorization'] = 'Bearer ' + os.environ['OPENALEX_API_KEY']
        for start in range(0, len(wanted), 50):
            batch = wanted[start:start + 50]
            try:
                response = session.get('https://api.openalex.org/works',
                    params={'filter': 'doi:' + '|'.join(batch), 'per_page': 100}, timeout=(10, 30))
                if response.status_code != 200:
                    raise RuntimeError(f'OpenAlex catalogue HTTP {response.status_code}; retaining previous output')
                payload = response.json()
            except (requests.RequestException, ValueError):
                raise RuntimeError('OpenAlex catalogue request failed; retaining previous output') from None
            rows = payload.get('results')
            if not isinstance(rows, list) or payload.get('meta', {}).get('count') != len(rows):
                raise ValueError('Incomplete OpenAlex DOI lookup')
            seen_ids = set()
            for work in rows:
                if work.get('id') in seen_ids:
                    raise ValueError('Repeated OpenAlex work ID in one response')
                seen_ids.add(work.get('id'))
                doi = normalize_doi(work.get('doi'))
                if doi not in batch:
                    continue  # Redirect/alias is not an exact DOI match.
                ident = work.get('id', '')
                if not re.fullmatch(r'https://openalex.org/W\d+', ident):
                    raise ValueError('Invalid OpenAlex work ID')
                paper = {'doi': doi, 'title': work.get('display_name', ''), 'num_citations': count(work.get('cited_by_count'))}
                if ident in result['works']:
                    raise ValueError('Conflicting OpenAlex work identities')
                result['works'][ident] = paper
    matched = sum(match_work(result, doi) is not None for doi in wanted)
    if not matched:
        raise ValueError('No exact OpenAlex DOI matches; retaining previous output')
    print(f'OpenAlex exact DOI coverage: {matched}/{len(wanted)} unique catalogue DOIs; unmatched/ambiguous shown as N/A')
    return result
