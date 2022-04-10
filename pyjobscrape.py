from urllib.request import Request, urlopen
import urllib.parse
from bs4 import BeautifulSoup as soup
import re
import pandas as pd
from datetime import datetime
import webbrowser
import random
import ssl
import time

list_dict_config_job_sites = [
    {
        "job_site": "Indeed.com",
        "url": "https://www.indeed.com/jobs?as_and&as_phr={}&as_any&as_not&as_ttl&as_cmp&jt=parttime&st&sr=directhire&salary&radius=25&l&fromage=any$l={}&start={}&limit={}&sort&psf=advsrch&from=advancedsearch&vjk=19ff24d735a88a04",
        "page_length": 25, # Can be up to 50 for Indeed. Keep it small for testing
        "sleep_time_between_requests": 4, # seconds to sleep between SERP clicks
        "random_sleep_variation": 2, # add some variety to the sleep
        "job_title": "nursing aide",
        "job_location": "san diego",
        "job_page": "https://www.indeed.com/viewjob?jk=",
        "max_results": 50, # The maximum number of jobs retried across all pages (but this is reduced by randomization below)
        "randomize_per_page_clicks": True # Only select a percentage of page results if True
    }
]

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

    title = pagesoup.find('h1')
    if title is not None:
        job_dict["job_title"] = title.text.strip()
    else:
        title = pagesoup.find('span', attrs={"class": "indeed-apply-widget",
            "data-indeed-apply-jobtitle":True})
        if title is not None:
            job_dict["job_title"] = title["data-indeed-apply-jobtitle"]
        else:
            job_dict["job_title"] = None        # This is probably an error in our parsing

    job_location = pagesoup.find('span', attrs={"class": "indeed-apply-widget",
        "data-indeed-apply-joblocation":True})
    if job_location is not None:
        job_dict["job_location"] = job_location["data-indeed-apply-joblocation"]
    else:
        job_dict["job_location"] = None

    company_tag = pagesoup.find('meta', attrs={"property": "og:description", "content":True})
    if company_tag is not None:
        job_dict["company"] = company_tag['content']

    job_type_element = pagesoup.find("div", string="Full-time")
    if job_type_element is not None:
        job_dict["job_type_full_time"] = True
    else:
        job_dict["job_type_full_time"] = False
    job_type_element = pagesoup.find("div", string="Part-time")
    if job_type_element is not None:
        job_dict["job_type_part_time"] = True
    else:
        job_dict["job_type_part_time"] = False
    job_type_element = pagesoup.find("div", string="Temporary")
    if job_type_element is not None:
        job_dict["job_type_temporary"] = True
    else:
        job_dict["job_type_temporary"] = False

    # jobsearch-HiringInsights-icon--multiplecandidates
    multiple_candidates_span = pagesoup.find('span', attrs={"class": "jobsearch-HiringInsights-icon--multiplecandidates"})
    if multiple_candidates_span is not None:
        multiple_candidates_sib = multiple_candidates_span.nextSibling
        if multiple_candidates_sib is not None:
            num_multiple_candidates = next(multiple_candidates_sib.children, None).nextSibling
            if num_multiple_candidates is not None:
                num_text_raw = num_multiple_candidates.text.strip()
                print(f"num_text_raw: {num_text_raw}")
                num_text = ''.join(filter(str.isdigit, num_text_raw))
                print(f"num_text: {num_text}")
                if num_text.isdigit():
                    job_dict["num_candidates"] = int(num_text)
                else:
                    if num_text_raw.find("On-going") != -1:
                        job_dict["num_candidates"] = True   # This means "lots"
                    else:
                        job_dict["num_candidates"] = 1
                    print( f"Num candidates text: {num_text_raw}")
                print(f'Num stored: {job_dict["num_candidates"]}')

    else:
        job_dict["num_candidates"] = 1

    company_rating_element = pagesoup.find('div', attrs={"class": "icl-Ratings-starsCountWrapper"})
    if company_rating_element is not None and company_rating_element.has_attr("aria-label"):
        company_rating_fulltext = company_rating_element["aria-label"]
        list_rating_info = re.findall(r"[-+]?(?:\d*\.\d+|\d+)",company_rating_fulltext)
        if len(list_rating_info) == 3:
            job_dict["company_rating"] = list_rating_info[0]
            job_dict["company_rating_max_potential"] = list_rating_info[1]
            job_dict["company_rating_num_employee_votes"] = list_rating_info[2]

    pay = pagesoup.find('div', text="Salary")
    if pay is not None:
        job_dict["pay"] = pay.nextSibling.text.strip()
    else:
        job_dict["pay"] = None

    description_div = pagesoup.find(id="jobDescriptionText")
    if description_div is not None:
        job_dict["description"] = description_div.text.strip()
        # print(f'description: {job_dict["description"]}')

    return job_dict

ssl._create_default_https_context = ssl._create_unverified_context
print("\nScraping\n")

list_jobs_dict = []

for idx, config_job_site_dict in enumerate(list_dict_config_job_sites):
    pages = config_job_site_dict["max_results"] // config_job_site_dict["page_length"]

    for page in list(range(pages)):
        print(f"Pulling page {page+1} of {pages} pages...")

        url = config_job_site_dict["url"].format(   # Format the URL to include the job title and results length
            urllib.parse.quote(config_job_site_dict["job_title"], safe=""), # add Job title to url
            urllib.parse.quote(config_job_site_dict["job_location"], safe=""),  # add location to url
            page-1*config_job_site_dict["page_length"],                     # Where to start in SERP
            config_job_site_dict["page_length"])                            # Add max results per page
        print(f"Getting {url}")
        datetime_string = datetime.now().strftime("%A %B %d %H:%M:%S")
        print(f'Looking for {config_job_site_dict["job_title"]} at {config_job_site_dict["job_site"]} on {datetime_string}')
        list_job_ids = get_jobs_IDs(url)
        if config_job_site_dict["randomize_per_page_clicks"] is True:
            page_max_clicks = round(random.random() * config_job_site_dict["page_length"])
        else:
            page_max_clicks = config_job_site_dict["page_length"]

        print(f"Getting {page_max_clicks} jobs from page {page+1}")

        for job in list(range(page_max_clicks)):
            job_id = list_job_ids[job]
            job_dict = get_job(config_job_site_dict["job_page"], job_id)
            sleep_per_iteration_rand = config_job_site_dict["sleep_time_between_requests"] + round(random.random()*config_job_site_dict["random_sleep_variation"], 1)
            # print(f"Sleeping for {sleep_per_iteration_rand}...")
            time.sleep(sleep_per_iteration_rand)
            list_jobs_dict.append(job_dict)

    pd_jobs = pd.DataFrame(list_jobs_dict)
    csv_path = f'./{datetime_string}_{config_job_site_dict["job_location"]}_{config_job_site_dict["job_title"]}_{config_job_site_dict["job_site"]}.csv'.replace(" ", "_")
    print(f'Saving to {csv_path}')
    pd_jobs.to_csv(csv_path)
