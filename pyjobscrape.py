from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup

from datetime import datetime
import webbrowser
import random
import ssl


def get_jobs_urls(url):
    list_jobs = []
    req = Request(url,headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    pagesoup = soup(webpage, "html.parser")
    # Looking for data-jk inside a section id="vjs-container"
    a_list = pagesoup.find_all("a", attrs={"data-jk": True})
    print(f"Num jobs: {len(a_list)}" )
    for a in a_list:
        if a.has_attr('data-jk'):
            a_data_jk = a['data-jk']
            print(f"a job key {a_data_jk}")
            list_jobs.append(a_data_jk)

    return list_jobs

def get_job(pagesoup):
    a_s = pagesoup.find_all('a', {'class': 'product-image'})
    list_urls = []
    for a in a_s:
        if a.has_attr('href'):
            a_href = a['href']
            if a_href is not None and len(a_href)>0:
                # print("Checking for products here: {}".format(a_href))
                req_product = Request(a_href,headers={'User-Agent': 'Mozilla/5.0'})
                webpage_product = urlopen(req_product).read()
                pagesoup_product = soup(webpage_product, "html.parser")
                d = pagesoup_product.find("button", title="Notify Me")
                if d is None:
                    list_urls.append(a_href)
    return list_urls

list_dict_job_sites = [
    # {
    #     "url": "https://www.roguefitness.com/weightlifting-bars-plates/barbells/mens-20kg-barbells?baruse[0]=multipurpose&is_salable[0]=0",
    #     "name": "test"
    # },
    {
        "job_site": "Indeed.com",
        "url": "https://www.indeed.com/jobs?as_and&as_phr=nursing%20aide&as_any&as_not&as_ttl&as_cmp&jt=parttime&st&sr=directhire&salary&radius=25&l&fromage=any&limit=50&sort&psf=advsrch&from=advancedsearch&vjk=19ff24d735a88a04",
        "name": "nursing aide jobs"
    }
]
len_list = len(list_dict_job_sites)


import time
ssl._create_default_https_context = ssl._create_unverified_context
print("\nScraping\n")

for idx, jobs_dict in enumerate(list_dict_job_sites):
    print("Looking for {} at {} on {}".format(jobs_dict["name"], jobs_dict["job_site"], datetime.now().strftime("%A %B %d %H:%M:%S")), flush=True)
    list_jobs = get_jobs_urls(jobs_dict["url"])
