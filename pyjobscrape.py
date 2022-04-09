from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup

from datetime import datetime
import webbrowser
import random
import ssl


def get_jobs_IDs(url):
    list_job_ids = []
    req = Request(url,headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    pagesoup = soup(webpage, "html.parser")
    # Looking for data-jk inside a section id="vjs-container"
    a_list = pagesoup.find_all("a", attrs={"data-jk": True})
    print(f"Num jobs: {len(a_list)}" )
    for a in a_list:
        if a.has_attr('data-jk'):
            a_data_jk = a['data-jk']
            # print(f"a job key {a_data_jk}")
            list_job_ids.append(a_data_jk)

    return list_job_ids

def get_job(job_page, job_id):
    job_url = f'{job_page}{job_id}'
    job_dict = {"id": job_id, "url": job_url}
    print(f'job_url: {job_url}')
    req = Request(job_url, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    pagesoup = soup(webpage, "html.parser")
    job_dict["h1"] = pagesoup.find('h1').text
    print(job_dict)

    # list_urls = []
    # for a in a_s:
    #     if a.has_attr('href'):
    #         a_href = a['href']
    #         if a_href is not None and len(a_href)>0:
    #             # print("Checking for products here: {}".format(a_href))
    #             req_product = Request(a_href,headers={'User-Agent': 'Mozilla/5.0'})
    #             webpage_product = urlopen(req_product).read()
    #             pagesoup_product = soup(webpage_product, "html.parser")
    #             d = pagesoup_product.find("button", title="Notify Me")
    #             if d is None:
    #                 list_urls.append(a_href)
    return job_dict

list_dict_config_job_sites = [
    # {
    #     "url": "https://www.roguefitness.com/weightlifting-bars-plates/barbells/mens-20kg-barbells?baruse[0]=multipurpose&is_salable[0]=0",
    #     "name": "test"
    # },
    {
        "job_site": "Indeed.com",
        "url": "https://www.indeed.com/jobs?as_and&as_phr=nursing%20aide&as_any&as_not&as_ttl&as_cmp&jt=parttime&st&sr=directhire&salary&radius=25&l&fromage=any&limit={}&sort&psf=advsrch&from=advancedsearch&vjk=19ff24d735a88a04",
        "list_length": 5, # Can be up to 50 for Indeed. Keep it small for testing
        "sleep_time_between_requests": 2, # seconds to sleep to prevent site from knowing you're a scraper
        "random_sleep_variation": 1, # add on to sleep to look more human
        "job_title": "nursing aide",
        "job_page": "https://www.indeed.com/viewjob?jk="
    }
]


import time
ssl._create_default_https_context = ssl._create_unverified_context
print("\nScraping\n")
list_job_dict = []

for idx, config_job_site_dict in enumerate(list_dict_config_job_sites):
    url = config_job_site_dict["url"].format(config_job_site_dict["list_length"])
    print(f"getting {url}")
    print(f'Looking for {config_job_site_dict["job_title"]} at {config_job_site_dict["job_site"]} on {datetime.now().strftime("%A %B %d %H:%M:%S")}')
    list_job_ids = get_jobs_IDs(url)
    print(f'Opening up {len(list_job_ids)} job pages on {config_job_site_dict["job_site"]}')
    for job_id in list_job_ids:
        job_dict = get_job(config_job_site_dict["job_page"], job_id)
        sleep_per_iteration_rand = config_job_site_dict["sleep_time_between_requests"] + round(random.random()*config_job_site_dict["random_sleep_variation"], 1)
        print(f"Sleeping for {sleep_per_iteration_rand}...")
        time.sleep(sleep_per_iteration_rand)
        list_job_dict.append(job_dict)
