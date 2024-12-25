import pandas as pd
import requests


# INFO_COLUMNS = ["doi", "title", "author_names", "journal", "date", "id", "times_cited",]
INFO_COLUMNS = ["times_cited",]
PUBLICATION_LIST = 'publications.csv'


def update_publication_info():
    tmp = update_pub_list(pd.read_csv(PUBLICATION_LIST))
    tmp.to_csv(PUBLICATION_LIST, index=False)


def update_pub_list(pub):
    df = pd.json_normalize(pub['doi'].drop_duplicates().apply(get_pub_meta))
    df.sort_values(by='date', ascending=False, inplace=True)
    return df.dropna(how='all')


def get_pub_meta(doi):
    result = {}

    res = requests.get(f'https://api.altmetric.com/v1/doi/{doi}')
    if res.status_code == 200:
        altmetric_js = res.json()
        result['score'] = round(altmetric_js['score'], 2)
    
    print(f'[FINISHED] {doi}')
    return result


if __name__ == '__main__':
    update_publication_info()
