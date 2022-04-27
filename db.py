import os
import psycopg2
from settings import settings

class pg:
    def __init__(self):
        s = settings()
        self.env_dict = s.get_settings()
        self.conn = self.get_conn()

    def get_conn(self):
        conn = None
        if "DATABASE_URL" in self.env_dict:
            db_url = os.environ['DATABASE_URL']
            conn = psycopg2.connect(db_url, sslmode='prefer')
        return conn

    def query(self, sql):
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def insert(self, sql):
        self.conn.cursor.execute(sql)
        return self.conn.cursor.fetchone()[0]

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn is not None:
            self.conn.close()


