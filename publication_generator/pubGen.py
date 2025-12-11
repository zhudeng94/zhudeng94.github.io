import pandas as pd
import requests
import gspread
import os


# 从 Google Spreadsheet 读取数据
def read_google_sheet(sheet_name):
    credentials = {
      "type": "service_account",
      "project_id": "ceremonial-hold-366807",
      "private_key_id": os.environ['GS_PRIVATE_KEY_ID'],
      "private_key": os.environ['GS_PRIVATE_KEY'].replace('\\n', '\n'),
      "client_email": "296654983139-compute@developer.gserviceaccount.com",
      "client_id": "115750140284121630235",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/296654983139-compute%40developer.gserviceaccount.com",
      "universe_domain": "googleapis.com"
    }
    print(credentials)

    gc = gspread.service_account_from_dict(credentials)
    # 打开 Google 表格
    sheet = gc.open_by_url(sheet_name).sheet1
    # 获取所有数据并转换为 Pandas DataFrame
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    return df

df = read_google_sheet("https://docs.google.com/spreadsheets/d/1WK8TH28_nhs6fEpVGv2RKQt7Zm-p1OpHthG282B8WDc")
df.date = pd.to_datetime(df.date)
df.sort_values('date', ascending=False,  inplace=True)

js = requests.get('https://cdn.jsdelivr.net/gh/zhudeng94/zhudeng94.github.io@google-scholar-stats/gs_data.json', verify=False).json()

selected_pub = ""
all_pub = ""

y = 0
i = 1

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

    if pub['selected'] == 1:
        tmp = (f"{i}. {','.join(author.split(',')[:3])}, et al. <a href='http://doi.org/{doi}'>{title}</a>. ***{journal}***. {year}."
               f"<a href='https://scholar.google.com/citations?view_op=view_citation&citation_for_view={gsid}'><img src='https://img.shields.io/badge/Citations-{cite_num}-white?logo=googlescholar'></a> "
               f"<div class='altmetric-embed' data-badge-type='4' data-doi='{doi}'></div>"
               f"  \n")
        selected_pub += tmp
        i += 1

    if y!=year:
        y = year
        all_pub += f"\n### 🌳 {y}   \n"

    tmp = (f"- {author}. <a href='http://doi.org/{doi}'>{title}</a>. ***{journal}***. {year}.   \n   "
           f"<div> "
           f"<a href='https://scholar.google.com/citations?view_op=view_citation&citation_for_view={gsid}'><img src='https://img.shields.io/badge/Citations-{cite_num}-white?logo=googlescholar'></a> "
           f"<a href='https://www.altmetric.com/details.php?doi={doi}'><img src='https://img.shields.io/badge/🔥Altmetric-{score}-red'></a>"
           f"</div>   \n")
    all_pub += tmp


with open('_pages/includes/pub_selected.md', 'w') as f:
    f.write(selected_pub)

with open('_pages/includes/pub_list.md', 'w') as f:
    f.write(all_pub)
