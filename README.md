# pyjobscrape 
scrapes jobs from job sites
## Environment
`brew install python`

`brew install tor`

`brew services restart tor`


## Prep DB
```
brew install postgres
brew services start postgres
/usr/local/opt/postgres/bin/createuser -s postgres
psql pyjobscrape -U postgres -h localhost
CREATE ROLE pyjobscrape;
ALTER ROLE pyjobscrape WITH LOGIN PASSWORD '<your password>' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE pyjobscrape OWNER pyjobscrape;
REVOKE ALL ON DATABASE pyjobscrape FROM PUBLIC;
GRANT CONNECT ON DATABASE pyjobscrape TO pyjobscrape;
GRANT ALL ON DATABASE pyjobscrape TO pyjobscrape;
\c pyjobscrape
\i pg_schema.sql
COPY jobs from pg_data.sql delimiter '\t'
\q
```
Make sure you got it right
```
psql postgres://pyjobscrape:p@localhost:5432/pyjobscrape
select * from jobs;
```
## Prep python
```
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## .env file
For local, create .env. For Heroku, add config vars in Settings. 
```
DATABASE_URL = <url>
NO_PROXY = TRUE | FALSE
job_titles = ["title1", "title2", ...]
job_locations = ["loc1", "loc2", ...]
```
## Use
`python3.10 pyjobscrape.py`
### Optional parameters
--job

--location

--anyoneof
## Quit
`Ctrl-c`
