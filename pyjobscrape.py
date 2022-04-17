import sys, getopt
# from urllib.request import Request, urlopen
import urllib.parse
from bs4 import BeautifulSoup as soup
import re
import pandas as pd
from datetime import datetime
# import webbrowser
import random
import ssl
import time
import requests     # TOR service required locally on port 9050
from stem import Signal
from stem.control import Controller
from settings import get_settings_dict
# from csv import to_csv

use_proxy_list = {
    'http': 'socks5://127.0.0.1:9050',
    'https': 'socks5://127.0.0.1:9050'
}


headers_list = [
    # Firefox 77 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    # Chrome 83 Mac
    {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    },
    # Chrome 83 Windows
    {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
]

def get_random_user_agent():
    return random.choice(headers_list)

def get_jobs_IDs(url):
    list_job_ids = []
    headers = {}
    proxies = {}
    if use_proxy:
        headers = get_random_user_agent()
        proxies = use_proxy_list

    response = requests.get(url, proxies=proxies, headers=headers)

    if response.status_code == 200:
        pagesoup = soup(response.text, features="html5lib", from_encoding='utf8')
        # Looking for data-jk inside a section id="vjs-container"
        a_list = pagesoup.find_all("a", attrs={"data-jk": True})
        if len(a_list) == 0:
            print(f"Num jobs: {len(a_list)}" )
            print(f"Response.text: *****\n\n{response.text}\n\n*****")
        for a in a_list:
            if a.has_attr('data-jk'):
                a_data_jk = a['data-jk']
                # print(f"a job key {a_data_jk}")
                list_job_ids.append(a_data_jk)
    else:
        print(f"Status code from {url}: {response.status_code}. Text: {response.text}")

    return list_job_ids

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_job(job_page, job_id):
    job_url = f'{job_page}{job_id}'
    job_dict = {"id": job_id, "source": env_dict["job_site"], "url": job_url, "job_title": "", "job_location": "", "company": "",
    "company_rating": None, "company_rating_max_potential": None, "company_rating_num_employee_votes": None,
    "job_type_full_time": False,	"job_type_part_time": False,	"job_type_temporary": False,	"num_candidates": 1,
    "pay_min_posted": None,	"pay_max_posted": None,	"pay_min_hourly": None,	"pay_max_hourly": None,	"pay_unit_time": "hourly",
    "description": ""}
    print(f'\tGetting {job_url}')
    headers = {}
    proxies = {}
    if use_proxy:
        headers = get_random_user_agent()
        proxies = use_proxy_list

    response = requests.get(job_url, proxies=proxies, headers=headers)

    if response.status_code == 200:
        # webpage = urlopen(req).read()
        pagesoup = soup(response.text, features="html5lib", from_encoding='utf8')

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
                print(f"No title found for {job_id}")

        job_location = pagesoup.find('span', attrs={"class": "indeed-apply-widget",
            "data-indeed-apply-joblocation":True})
        if job_location is not None:
            job_dict["job_location"] = job_location["data-indeed-apply-joblocation"]
        else:
            job_dict["job_location"] = None

        company_tag = pagesoup.find('meta', attrs={"property": "og:description", "content":True})
        if company_tag is not None:
            job_dict["company"] = company_tag['content']
        else:
            company_tag = pagesoup.find('div', attrs={"class": "jobsearch-CompanyReview--heading", "content":True})
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
        job_dict["num_candidates"] = 1
        multiple_candidates_span = pagesoup.find('span', attrs={"class": "jobsearch-HiringInsights-icon--multiplecandidates"})
        if multiple_candidates_span is not None:
            multiple_candidates_sib = multiple_candidates_span.nextSibling
            if multiple_candidates_sib is not None:
                num_multiple_candidates = next(multiple_candidates_sib.children, None).nextSibling
                if num_multiple_candidates is not None:
                    num_text_raw = num_multiple_candidates.text.strip()
                    num_text = ''.join(filter(str.isdigit, num_text_raw))
                    if num_text.isdigit():
                        job_dict["num_candidates"] = int(num_text)
                    else:
                        if num_text_raw.find("On-going") != -1:
                            job_dict["num_candidates"] = True   # This means "lots"
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

        # For pay, since it is posted in a number of different hourly, daily, weekly amounts,
        # we normalize it to hourly but also save the originally posted rate and unit of time
        # since that may indicate the frequency of pay, which may be useful later
        pay = pagesoup.find('div', text="Salary")
        pay_text_raw = None
        job_dict["pay_min_posted"] = None
        job_dict["pay_max_posted"] = None
        job_dict["pay_min_hourly"] = None
        job_dict["pay_max_hourly"] = None
        job_dict["pay_unit_time"] = "hour"
        pay_conversion_to_hours = 1

        if pay is not None:
            pay_text_raw = pay.nextSibling.text.strip()
            pay_per_unit_time_idx = pay_text_raw.find("hour")
            if pay_per_unit_time_idx != -1:
                job_dict["pay_unit_time"] = "hour"

        # TO DO - convert pay to hourly in these next 2 cases?
            elif pay_text_raw.find("day")  != -1:
                job_dict["pay_unit_time"] = "day"
                pay_conversion_to_hours = 8.0

            elif pay_text_raw.find("week")  != -1:
                job_dict["pay_unit_time"] = "week"
                pay_conversion_to_hours = 40.0

            pay_text_raw_strip_currency = pay_text_raw.replace('$','')
            pay_text_raw_words = pay_text_raw_strip_currency.split(" ")
            pay_range_list = [i for i in pay_text_raw_words if (is_number(i))]

            if len(pay_range_list) > 0:
                job_dict["pay_min_posted"] = float(pay_range_list[0])
                job_dict["pay_min_hourly"] = float(pay_range_list[0]) / pay_conversion_to_hours
                if len(pay_range_list) > 1:
                    job_dict["pay_max_posted"] = float(pay_range_list[1])
                    job_dict["pay_max_hourly"] = float(pay_range_list[1]) / pay_conversion_to_hours

        # print(f'Pay range: {job_dict["pay_min"]} - {job_dict["pay_max"]}')
        description_div = pagesoup.find(id="jobDescriptionText")
        if description_div is not None:
            job_dict["description"] = description_div.text.strip()
            # print(f'description: {job_dict["description"]}')
    else:
        print(f"Status code from {job_url}: {response.status_code}. Text: {response.text}")

    return job_dict

# get all the search results for a given job site
#       config_job_site_dict, job_title, job_location - configured or overrides from command line
#       list_jobs_dict - returned
#
def get_jobsite_SERPs( job_title, job_location, search_term_atleastone):
    list_jobs = []
    # pages = env_dict["max_results"] // env_dict["page_length"]
    more_pages = True
    page = 1

    while more_pages:
        list_job_ids = []
        serp_start_at = (page-1) * env_dict["page_length"]+1
        if serp_start_at > env_dict["max_results"]:
            more_pages = False
            continue

        url = env_dict["url"].format(   # Format the URL to include the job title and results length
            urllib.parse.quote(job_title, safe=""), # add Job title to url
            urllib.parse.quote(search_term_atleastone, safe=""), # add find at least one to url
            urllib.parse.quote(job_location, safe=""),  # add location to url
            serp_start_at,                              # Where to start in SERP
            env_dict["page_length"])                            # Add max results per page
        datetime_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'Looking for {job_title} at {env_dict["job_site"]} on {datetime_string} via {url}')

        while len(list_job_ids) == 0:
            list_job_ids = get_jobs_IDs(url)
            if len(list_job_ids) == 0:
                return list_jobs        # This is a failure state

        if env_dict["randomize_per_page_clicks"] is True:
            page_max_result_clicks_randomizer = round(random.randint( env_dict["page_length"] // 2, env_dict["page_length"]))
        else:
            page_max_result_clicks_randomizer = env_dict["page_length"]
        len_returned_list = len(list_job_ids)
        print(f'Tried to get {env_dict["page_length"]} job results from page {page} and retrieved {len_returned_list} jobs')

        if len_returned_list < page_max_result_clicks_randomizer:
            more_pages = False
            print(f'Last page of search results.')

        if len_returned_list > page_max_result_clicks_randomizer:
            print(f"Randomly trimming list of search results to open down to {page_max_result_clicks_randomizer}")
            del list_job_ids[page_max_result_clicks_randomizer:]

        for job_id in list_job_ids:
            job_dict = get_job(env_dict["job_page"], job_id)
            sleep_per_iteration_rand = env_dict["sleep_time_between_requests"] + round(random.random()*env_dict["random_sleep_variation"], 1)
            # print(f"Sleeping for {sleep_per_iteration_rand}...")
            time.sleep(sleep_per_iteration_rand)
            list_jobs.append(job_dict)

        list_job_ids.clear()    # We are reusing this in a loop, so make sure to clean it between iterations
        page = page + 1

    return list_jobs


def main(argv):

    # Parse command line and override config
    job_location = None
    job_title = None
    search_term_atleastone = None
    opts, args = getopt.getopt(argv,"s,l,j",["atleastone=", "location=", "job="])
    for opt, arg in opts:
        if opt in ("-l", "--location"):
            job_location = arg
            print(f"Location: {job_location}")
        elif opt in ("-j", "--job"):
            job_title = arg
        elif opt in ("-s", "--atleastone"):
            search_term_atleastone = arg
            print(f"Find at least one of: {search_term_atleastone}")

    if use_proxy:
        # Get my IP Address
        proxies = use_proxy_list
        my_ip = requests.get('https://ident.me', proxies=proxies).text
        print( f'Requests will originate from IP {my_ip}')
    else:
        print('Not using proxies')

    ssl._create_default_https_context = ssl._create_unverified_context
    print("\nScraping\n")

    list_jobs = []

    # take overridden location and title from command line
    if job_title is not None and job_location is not None:
        list_jobs = get_jobsite_SERPs(job_title, job_location, search_term_atleastone)
    else:
        # Optionally override config with command line parms
        if job_location is None and "job_titles" in env_dict:
            job_location_list = env_dict["job_locations"]
        if job_title is None and "job_titles" in env_dict:
            job_title_list = env_dict["job_titles"]
        if search_term_atleastone is None:
            search_term_atleastone = ""

        for job_title in job_title_list:
            print(f"job title {job_title}")
            for job_location in job_location_list:
                print(f"job loc {job_location}")
                list_jobs_per_title_location = get_jobsite_SERPs(job_title, job_location, search_term_atleastone)
                # print(f"partial list: {list_jobs_per_title_location}")
                list_jobs.extend(list_jobs_per_title_location)

    if len(list_jobs) > 0:
        pd_jobs = pd.DataFrame(list_jobs)
        # stats = pd_jobs.describe(include='all')
        # print (stats)
        print(pd_jobs)
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        csv_path = f'./{datetime_string}_{job_location}_{job_title}_{search_term_atleastone}_{env_dict["job_site"]}.csv'.replace(" ", "_")
        # to_csv(csv_path, list_jobs)
        pd_jobs.to_csv(csv_path)
        print(f'Done. Saved results to {csv_path}')
    else:
        print(f'No results.')

if __name__ == "__main__":
    env_dict = get_settings_dict()
    use_proxy = True

    # See if we want to use a proxy (this is set to 0 in Heroku)
    if "NO_PROXY" in env_dict:
        use_proxy = not bool(env_dict["NO_PROXY"])

    main(sys.argv[1:])
