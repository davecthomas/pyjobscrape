import os
from dotenv import load_dotenv, find_dotenv
import json


class settings:

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

    def __init__(self):
        self.env_dict = self.get_settings_dict()

    def get_settings(self):
        return self.env_dict

    def load_environment(self):
        load_dotenv(find_dotenv())
        return os.environ

    def get_settings_dict(self):
        env_dict = self.load_environment()
        dict_settings = self.default_settings
        for i, (k, v) in enumerate(env_dict.items()):
            match k:
                case "NO_PROXY" | "randomize_per_page_clicks":
                    dict_settings[k] = v.lower() in ('true', '1', 't')
                case "job_titles" | "job_locations":
                    dict_settings[k] = json.loads(v)
                case "sleep_time_between_requests":
                    dict_settings[k] = int(v)
                case "random_sleep_variation":
                    dict_settings[k] = int(v)
                case "max_results":
                    dict_settings[k] = int(v)
                case "page_length":
                    dict_settings[k] = int(v)
                case _:
                   dict_settings[k] = v

        return dict_settings