import os
import json
import sys
import time
import xlsxwriter

from Scraper import HashtagScraper

# Loading of input data (LinkedIn hashtag Urls)
hashtag_urls = []
for entry in open('../input/hashtags/urls.txt', "r"):
    hashtag_urls.append(entry.strip())

print(hashtag_urls)

# Warning if hashtags are not provided
if len(hashtag_urls) == 0:
    print("Please provide an input.")
    sys.exit(0)

# Launch HashtagScraper
s = HashtagScraper(
    linkedin_username=os.getenv('LINKEDIN_EMAIL'),
    linkedin_password=os.getenv('LINKEDIN_PASSWORD'),
    hashtag_urls=hashtag_urls,
    headless='HEADLESS'
)

s.start()