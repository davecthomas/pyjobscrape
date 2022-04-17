import os
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv
import json

default_settings = {
    "NO_PROXY": False,
    "DATABASE_URL": "",
    "source": "Indeed",
    "job_site":  "Indeed.com",
    "url": "https://www.indeed.com/jobs?as_and&as_phr=&as_ttl={}&as_any={}&as_not&as_ttl&as_cmp&jt=parttime&st&sr=directhire&salary&radius=25&l&fromage=any&l={}&start={}&limit={}&sort&psf=advsrch&from=advancedsearch&filter=0",
    "sleep_time_between_requests":  5,
    "random_sleep_variation": 3,
    "job_page": "https://www.indeed.com/viewjob?jk=",
    "randomize_per_page_clicks": True,
    "job_titles": ["caretaker"],
    "job_locations": ["san diego county"],
    "max_results": 25,
    "page_length": 10
}

def load_environment():
    load_dotenv(find_dotenv())
    return os.environ

def get_settings_dict():
    env_dict = load_environment()
    dict_settings = default_settings
    for i, (k, v) in enumerate(env_dict.items()):
        match k:
            case "job_titles" | "job_locations":
                dict_settings[k] = json.loads(env_dict[k])
            case "sleep_time_between_requests":
                dict_settings[k] = int(env_dict[k])
            case "random_sleep_variation":
                dict_settings[k] = int(env_dict[k])
            case "randomize_per_page_clicks":
                dict_settings[k] = bool(env_dict[k])
            case "max_results":
                dict_settings[k] = int(env_dict[k])
            case "page_length":
                dict_settings[k] = int(env_dict[k])
            case _:
               dict_settings[k] = env_dict[k]

    return dict_settings