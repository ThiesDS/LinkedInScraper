import json
import sys
import time
import xlsxwriter
from configparser import ConfigParser

from HashtagScraper import HashtagScraper

# Loading of configurations
from utils import ComplexEncoder

config = ConfigParser()
config.read('config.ini')

# Setting the execution mode
headless_option = 'HEADLESS'

# Loading of input data (LinkedIn hashtag Urls)
hashtag_urls = []
for entry in open('../input/hashtags/urls.txt'), "r"):
    hashtag_urls.append(entry.strip())

#if len(hashtag_urls) == 0:
#    print("Please provide an input.")
#    sys.exit(0)

# Launch Scraper
s = HashtagScraper(
    linkedin_username=config.get('linkedin', 'username'),
    linkedin_password=config.get('linkedin', 'password'),
    hashtag_urls=hashtag_urls,
    headless=headless_option
)

s.start()