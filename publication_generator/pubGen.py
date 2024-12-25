import pandas as pd
import requests

df = pd.read_excel('files/publications.xlsx', parse_dates=['date'])
df.sort_values('date', ascending=False,  inplace=True)

js = requests.get('https://cdn.jsdelivr.net/gh/zhudeng94/zhudeng94.github.io@google-scholar-stats/gs_data.json', verify=False).json()

selected_pub = ""
all_pub = ""

for index, pub in df.iterrows():
    author = pub['author'].replace('Zhu Deng', '**Zhu Deng**')
    title = pub['title']
    journal = pub['journal']
    year = pub['date'].year
    gsid = pub['gsid']
    if gsid in js['publications'].keys():
        cite_num = js['publications'][gsid]['num_citations']
    else:
        cite_num = 0
    doi = pub['doi']
    altmetric = ''
    # almetric = f'<div class="altmetric-embed" data-badge-type="4" data-doi="{doi}"></div>'
    citation = f'<img src="https://img.shields.io/badge/citations-{cite_num}-white">'

    tmp = f"- {author}. [{title}](http://doi.org/{doi}). ***{journal}***. {year}. {citation if cite_num>0 else ''} {altmetric}   \n"

    if pub['selected'] == 1:
        selected_pub += tmp

    all_pub += tmp


with open('_pages/includes/pub_selected.md', 'w') as f:
    f.write(selected_pub)

with open('_pages/includes/pub_list.md', 'w') as f:
    f.write(all_pub)
