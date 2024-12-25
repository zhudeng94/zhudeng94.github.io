import pandas as pd
import requests

df = pd.read_excel('files/publications.xlsx', parse_dates=['date'])
df.sort_values('date', ascending=False,  inplace=True)

js = requests.get('https://cdn.jsdelivr.net/gh/zhudeng94/zhudeng94.github.io@google-scholar-stats/gs_data.json', verify=False).json()

selected_pub = ""
all_pub = ""

y = 0

for index, pub in df.iterrows():
    author = pub['author'].replace('Zhu Deng', '**Zhu Deng**')
    title = pub['title']
    journal = pub['journal']
    year = pub['date'].year
    gsid = pub['gsid']
    doi = pub['doi']

    cite_num = 0
    score = 0

    if gsid in js['publications'].keys():
        cite_num = js['publications'][gsid]['num_citations']

    if doi != "":
        res = requests.get(f'https://api.altmetric.com/v1/doi/{doi}')
        if res.status_code == 200:
            altmetric_js = res.json()
            score = round(altmetric_js['score'])

    tmp = (f"- {author}. <u>{title}</u>.<a href='http://doi.org/{doi}'>🔗</a> ***{journal}***. {year}.   \n   "
           f"<div> "
           f"<a href='https://scholar.google.com/citations?view_op=view_citation&citation_for_view={gsid}'><img src='https://img.shields.io/badge/citation-{cite_num}-white?logo=googlescholar'></a> "
           f"<a href='https://www.altmetric.com/details.php?doi={doi}'><img src='https://img.shields.io/badge/🔥Altmetric-{score}-red'></a>"
           f"</div>   \n")

    if pub['selected'] == 1:
        selected_pub += tmp

    if y!=year:
        y = year
        all_pub += f"## {y}   \n"

    all_pub += tmp


with open('_pages/includes/pub_selected.md', 'w') as f:
    f.write(selected_pub)

with open('_pages/includes/pub_list.md', 'w') as f:
    f.write(all_pub)
