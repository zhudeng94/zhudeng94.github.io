"""Load validated citation data without turning a failed fetch into zero counts."""
import json
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://raw.githubusercontent.com/zhudeng94/zhudeng94.github.io/google-scholar-stats/gs_data.json"

def validate(data):
    if not isinstance(data, dict) or not isinstance(data.get("publications"), dict):
        raise ValueError("Citation data must contain a publications mapping")
    if not data["publications"]:
        raise ValueError("Refusing empty citation data")
    for paper in data["publications"].values():
        if not isinstance(paper, dict) or not isinstance(paper.get("num_citations"), int) or paper["num_citations"] < 0:
            raise ValueError("Citation data contains an invalid citation count")
    return data

def load_citation_data(path=None):
    # CI checks out the stats branch directly, avoiding CDN caching/failures.
    # An invalid/missing explicit file is an error, not permission to overwrite counts.
    if path:
        return validate(json.loads(Path(path).read_text(encoding="utf-8")))
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))))
        response = session.get(URL, timeout=(10, 30))
        response.raise_for_status()
        try:
            return validate(response.json())
        except (ValueError, TypeError) as exc:
            raise ValueError("Citation response is not valid citation JSON; existing output must be retained") from exc
