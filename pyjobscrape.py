import sys, getopt
import pandas as pd
from datetime import datetime
import ssl
import requests     # TOR service required locally on port 9050
from job_scrape import job_scrape
from settings import settings
from proxy import use_proxy_list

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

    ssl._create_default_https_context = ssl._create_unverified_context
    print("\nScraping\n")
    my_ip = requests.get('https://ident.me', proxies=use_proxy_list).text
    print(f'IP Before starting: {my_ip}')
    js = job_scrape()

    list_jobs = []
    s = settings()
    env_dict = s.get_settings()
    # take overridden location and title from command line
    if job_title is not None and job_location is not None:
        list_jobs = js.get_jobsite_SERPs(job_title, job_location, search_term_atleastone)
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
                list_jobs_per_title_location = js.get_jobsite_SERPs(job_title, job_location, search_term_atleastone)
                # print(f"partial list: {list_jobs_per_title_location}")
                list_jobs.extend(list_jobs_per_title_location)

    if len(list_jobs) > 0:
        pd_jobs = pd.DataFrame(list_jobs)
        # stats = pd_jobs.describe(include='all')
        # print (stats)
        print(pd_jobs)
        datetime_string = datetime.now().strftime("%Y-%m-%d")
        csv_path = f'./{datetime_string}_{job_location}_{job_title}_{search_term_atleastone}_{env_dict["job_site"]}.csv'.replace(" ", "_")
        # to_csv(csv_path, list_jobs)
        pd_jobs.to_csv(csv_path)
        print(f'Done. Saved results to {csv_path}')
    else:
        print(f'No results.')

if __name__ == "__main__":
    main(sys.argv[1:])
