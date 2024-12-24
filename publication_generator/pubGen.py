import pandas as pd

df = pd.read_excel('files/publications.xlsx', parse_dates=['date'])
df.sort_values('date', ascending=False,  inplace=True)

selected_pub = ""
other_pub = ""

for index, pub in df.iterrows():
    author = pub['author'].replace('Zhu Deng', '**Zhu Deng**')
    title = pub['title']
    journal = pub['journal']
    year = pub['date'].year
    gsid = pub['gsid']
    doi = pub['doi']
    almetric = f"<div class='altmetric-embed' data-badge-type='4' data-doi='{doi}'></div>"

    tmp = f"- {author}. [{title}](http://doi.org/{doi}). ***{journal}***. {year}. [<span class='show_paper_citations' data='{gsid}'></span>] {almetric}  \n"

    if pub['selected'] == 1:
        selected_pub += tmp
    else:
        other_pub += tmp



md = f"""
## 🌟 SELECTED PUBLICATIONS  
{selected_pub}
## 📄 Other Publications  
{other_pub}
"""

print(md)
with open('_pages/includes/pub_list.md', 'w') as f:
    f.write(md)
