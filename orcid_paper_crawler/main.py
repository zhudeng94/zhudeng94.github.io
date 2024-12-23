# https://orcid.org/0000-0002-6409-9578/worksExtendedPage.json?offset=0&sort=date&sortAsc=false&pageSize=50

import requests

url = 'https://orcid.org/0000-0002-6409-9578/worksExtendedPage.json?offset=0&sort=date&sortAsc=false&pageSize=5000'

js = requests.get(url).json()
