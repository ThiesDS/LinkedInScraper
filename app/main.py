import os
import json
import sys
import time
import xlsxwriter

from Scraper import HashtagScraper, ProfileScraper

if os.getenv('SCRAPER') == 'hashtags':
    # Loading of input data
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
        scroll_depth=os.getenv('SCROLL_DEPTH'),
        output_format=os.getenv('OUTPUT_FORMAT')
    )

    s.start()

elif os.getenv('SCRAPER') == 'profiles':
    # Loading of input data
    profiles = []
    for profile in open('../input/input_profiles.txt', "r"):
        profiles.append(profile)

    # Warning if profiles are not provided
    if len(profiles) == 0:
        print("Please provide an input.")
        sys.exit(0)

    # Launch Scraper
    s = ProfileScraper(
        linkedin_username=os.getenv('LINKEDIN_EMAIL'),
        linkedin_password=os.getenv('LINKEDIN_PASSWORD'),
        profiles=profiles,
        headless='HEADLESS',
        output_format=os.getenv('OUTPUT_FORMAT')
    )

    s.start()