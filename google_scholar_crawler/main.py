from scholarly import scholarly
import jsonpickle
import json
from datetime import datetime
import os
import pandas as pd
import gspread

# author: dict = scholarly.search_author_id(os.environ['GOOGLE_SCHOLAR_ID'])
author: dict = scholarly.search_author_id('bzZYiBgAAAAJ')
scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
name = author['name']
author['updated'] = str(datetime.now())
author['publications'] = {v['author_pub_id']:v for v in author['publications']}

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
author['total_paper_number'] = len(df)

print(json.dumps(author, indent=2))
os.makedirs('results', exist_ok=True)
with open(f'results/gs_data.json', 'w') as outfile:
    json.dump(author, outfile, ensure_ascii=False)


shieldio_data = {
  "schemaVersion": 1,
  "label": "citations",
  "message": f"{author['citedby']}",
}
with open(f'results/gs_data_shieldsio.json', 'w') as outfile:
    json.dump(shieldio_data, outfile, ensure_ascii=False)

shieldio_data = {
  "schemaVersion": 1,
  "label": "papers",
  "message": f"{len(author['publications'])}",
}
with open(f'results/gs_data_papers.json', 'w') as outfile:
    json.dump(shieldio_data, outfile, ensure_ascii=False)

