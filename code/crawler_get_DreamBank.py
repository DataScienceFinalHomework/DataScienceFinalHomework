import requests

url = 'https://dreambank.net/search.cgi'

headers = {
    'User-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.7680.80'
}

response = requests.get(url, headers=headers)
html = response.text

with open("dreambank.html","w",encoding = "utf-8") as f:
    f.write(html)

from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

#应该是要找<select name="series" id="select:series" size="11" multiple>里的option value

series = []
for i in soup.find_all('select', {'name': 'series'})[0].find_all("option"):
    series.append(i.get("value"))

print(series)

import time

IDs = []

for i in series[0:2]:
    d = []
    url = "https://dreambank.net/search.cgi?series=" + i
    query = {'query': 'e'}
    response = requests.get(url, headers=headers, params=query)
    html = response.text
    time.sleep(1)
    
    soup = BeautifulSoup(html, "html.parser")
    
    #应该要找<select size="20" name="d" multiple>中<option value="1" selected>1</option>的数字
     
    for j in soup.find_all('select',{'name':"d"})[0].find_all("option"):
        d.append(j.get("value"))

    IDs.append({'name': i, 'd': d})

# 对于每个name，拿着id去访问https://dreambank.net/show.cgi?d=<d>,拿到html后解析出梦的内容

url = "https://dreambank.net/show.cgi"

for k in IDs:
    current_name = k["name"]
    current_d = k["d"]

    for l in current_d:
        query = {"series" : current_name, "d": l, "query": "e"}
        response = requests.get(url, headers=headers, params=query)
        html = response.text
        time.sleep(0.75)
        
        #抓取诸如<label for="checkbox:alta:7" style="cursor:pointer;">#7 (1985?)</label><br/><br style="margin-bottom:-0.7em;"/>后面的内容

        start_marker = '<br style="margin-bottom:-0.7em;"/>'
        end_marker = '<hr noshade'

        temp = html.split(start_marker)[1]
        dream_text = temp.split(end_marker)[0]
        clean_text = dream_text.strip()

        with open("dreams.txt", "a", encoding = "utf-8") as f:
            f.write(clean_text + "\n")