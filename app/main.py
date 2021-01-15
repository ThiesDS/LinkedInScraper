import os
import json
import sys
import time
import xlsxwriter

from Scraper import HashtagScraper

# Loading of input data (LinkedIn hashtag Urls)
hashtags = []
for hashtag in open('../input/input_hashtags.txt', "r"):
    hashtags.append(hashtag)

# Warning if hashtags are not provided
if len(hashtags) == 0:
    print("Please provide an input.")
    sys.exit(0)

# Launch HashtagScraper
s = HashtagScraper(
    linkedin_username=os.getenv('LINKEDIN_EMAIL'),
    linkedin_password=os.getenv('LINKEDIN_PASSWORD'),
    hashtags=hashtags,
    headless='HEADLESS',
    output_format=os.getenv('OUTPUT_FORMAT')
)

s.start()