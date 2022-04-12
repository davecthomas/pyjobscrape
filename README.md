# pyjobscrape scrapes jobs from job sites
## Environment
`brew install python`
Read https://sylvaindurand.org/use-tor-with-python/
`brew install tor`
`brew services restart tor`
`python3.10 -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
## Use
Caffeine is a python package that prevents your system from sleeping when running long-running scripts.
Run with `caffeinate -i python3.10 pyjobscrape.py`
## Quit
`Ctrl-c`
