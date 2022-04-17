import os
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv

def load_environment():
    load_dotenv(find_dotenv())
    return os.environ