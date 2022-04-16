CREATE SEQUENCE job_id_seq
    START WITH 7
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS jobs(
  id int DEFAULT nextval('job_id_seq'::regclass) NOT NULL,
  job_id varchar(255),
  source varchar(255),
  url text,
  job_title varchar(255),
  job_location varchar(255),
  company varchar(255),
  company_rating real,
  company_rating_max_potential integer,
  company_rating_employee_votes integer,
  job_type_full_time boolean,
  job_type_part_time boolean,
  job_type_temporary boolean,
  num_candidates integer,
  pay_min_posted money,
  pay_max_posted money,
  pay_min_hourly money,
  pay_max_hourly money,
  pay_unit_time varchar(32),
  description text,
  PRIMARY KEY( id )
);
