import sys, getopt
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
        "url": "https://www.indeed.com/jobs?as_and&as_phr=&as_ttl={}&as_any&as_not&as_ttl&as_cmp&jt=parttime&st&sr=directhire&salary&radius=25&l&fromage=any&l={}&start={}&limit={}&sort&psf=advsrch&from=advancedsearch&vjk=19ff24d735a88a04&filter=0",
        "page_length": 50, # Can be up to 50 for Indeed. Keep it small for testing
        "sleep_time_between_requests": 4, # seconds to sleep between SERP clicks
        "random_sleep_variation": 2, # add some variety to the sleep
        "job_title": "nursing aide",
        "job_location": "san diego",
        "job_page": "https://www.indeed.com/viewjob?jk=",
        "max_results": 250, # The maximum number of jobs retried across all pages (but this is reduced by randomization below)
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
    # print(f"Num jobs: {len(a_list)}" )
    for a in a_list:
        if a.has_attr('data-jk'):
            a_data_jk = a['data-jk']
            # print(f"a job key {a_data_jk}")
            list_job_ids.append(a_data_jk)

    return list_job_ids

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_job(job_page, job_id):
    job_url = f'{job_page}{job_id}'
    job_dict = {"id": job_id, "url": job_url}
    print(f'\tGetting {job_url}')
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

    return job_dict

# get all the search results for a given job site
#       config_job_site_dict, job_title, job_location - configured or overrides from command line
#       list_jobs_dict - returned
#
def get_jobsite_SERPs(config_job_site_dict, job_title, job_location):
    list_jobs_dict = [] # List of dictionaries of job search results, returned f
    pages = config_job_site_dict["max_results"] // config_job_site_dict["page_length"]
    more_pages = True
    page = 1

    while more_pages:
        list_job_ids = []
        serp_start_at = (page-1) * config_job_site_dict["page_length"]+1
        if serp_start_at > config_job_site_dict["max_results"]:
            more_pages = False
            continue

        url = config_job_site_dict["url"].format(   # Format the URL to include the job title and results length
            urllib.parse.quote(job_title, safe=""), # add Job title to url
            urllib.parse.quote(job_location, safe=""),  # add location to url
            serp_start_at,                              # Where to start in SERP
            config_job_site_dict["page_length"])                            # Add max results per page
        datetime_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'Looking for {config_job_site_dict["job_title"]} at {config_job_site_dict["job_site"]} on {datetime_string} via {url}')

        list_job_ids = get_jobs_IDs(url)

        if config_job_site_dict["randomize_per_page_clicks"] is True:
            page_max_result_clicks_randomizer = round(random.randint( config_job_site_dict["page_length"] // 2, config_job_site_dict["page_length"]))
        else:
            page_max_result_clicks_randomizer = config_job_site_dict["page_length"]
        len_returned_list = len(list_job_ids)
        print(f'Tried to get {config_job_site_dict["page_length"]} job results from page {page} and retrieved {len_returned_list} jobs')

        if len_returned_list < page_max_result_clicks_randomizer:
            more_pages = False
            print(f'Last page of search results.')

        if len_returned_list > page_max_result_clicks_randomizer:
            print(f"Randomly trimming list of search results to open down to {page_max_result_clicks_randomizer}")
            del list_job_ids[page_max_result_clicks_randomizer:]

        for job_id in list_job_ids:
            job_dict = get_job(config_job_site_dict["job_page"], job_id)
            sleep_per_iteration_rand = config_job_site_dict["sleep_time_between_requests"] + round(random.random()*config_job_site_dict["random_sleep_variation"], 1)
            # print(f"Sleeping for {sleep_per_iteration_rand}...")
            time.sleep(sleep_per_iteration_rand)
            list_jobs_dict.append(job_dict)

        list_job_ids.clear()    # We are reusing this in a loop, so make sure to clean it between iterations
        page = page + 1

    return list_jobs_dict

def main(argv):
    # Parse command line and override config
    job_location = None
    job_title = None
    opts, args = getopt.getopt(argv,"l,j",["location=", "job="])
    for opt, arg in opts:
        if opt in ("-l", "--location"):
            job_location = arg
            print(f"Location: {job_location}")
        elif opt in ("j", "--job"):
            job_title = arg

    ssl._create_default_https_context = ssl._create_unverified_context
    print("\nScraping\n")

    list_jobs_dict = []

    # For each configured job site, get as many pages of results as is configured
    for idx, config_job_site_dict in enumerate(list_dict_config_job_sites):
        # Optionally override config with command line parms
        if job_location is None:
            job_location = config_job_site_dict["job_location"]
        if job_title is None:
            job_title = config_job_site_dict["job_title"]

        list_jobs_dict = get_jobsite_SERPs(config_job_site_dict, job_title, job_location)

        pd_jobs = pd.DataFrame(list_jobs_dict)
        # stats = pd_jobs.describe(include='all')
        # print (stats)
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        csv_path = f'./{datetime_string}_{job_location}_{job_title}_{config_job_site_dict["job_site"]}.csv'.replace(" ", "_")
        pd_jobs.to_csv(csv_path)
        print(f'Done. Saved results to {csv_path}')

if __name__ == "__main__":
    main(sys.argv[1:])
