import json
import re
import time
import pandas as pd


class AuthenticationException(Exception):
    """"""
    pass


class ScrapingException(Exception):
    """"""
    pass


class HumanCheckException(Exception):
    """Human Check from Linkedin"""
    pass


class CannotProceedScrapingException(Exception):
    """Human Check from Linkedin during an headless mode execution"""
    pass

class Post:
    def __init__(self, id: str, username: str, userdescription: str, published: str, text: str):
        self.id = id
        self.username = username
        self.userdescription = userdescription
        self.published = published
        self.text = text

    def as_json(self):
        return dict(id=self.id,
                    username=self.username,
                    userdescription=self.userdescription,
                    published=self.published,
                    text=self.text
                )

class HashtagScrapingResult:
    def __init__(self, hashtag: str, scraping_date: str, hashtag_posts: {str}):
        self.hashtag = hashtag
        self.scraping_date = scraping_date
        self.hashtag_posts = hashtag_posts

    def as_json(self):
        d = {}
        d[self.hashtag] = {
            'scraping_date':self.scraping_date, 
            'hashtag_posts':self.hashtag_posts
        }
        return d

    def as_dataframe(self):
        # Initialize df
        df = pd.DataFrame(columns=['hashtag','scraping_date', 'id','username','userdescription','published','text'])

        # Loop over all hastag urls
        for key in self.hashtag_posts.keys():
            df = df.append({**{'hashtag':self.hashtag},
                            **{'scraping_date':self.scraping_date},
                            **self.hashtag_posts[key]},
                 ignore_index=True)

        return df

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


def is_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def get_months_between_dates(date1, date2):
    if date1 < date2:
        diff = date2 - date1
    elif date1 > date2:
        diff = date1 - date2
    else:
        return 0

    return diff.days // 30


def wait_for_loading():
    time.sleep(2)


def wait_for_scrolling():
    time.sleep(1)

class HashtagResultsSaver():
    """
        Helper to save hashtag results to a file dependent on the output format
    """

    def __init__(self, output_format, output_folder):
        self.output_format = output_format
        self.output_folder = output_folder

    def allocate_object(self):
        if self.output_format=='flat':
            scraping_results = pd.DataFrame()
        elif self.output_format=='json':
            scraping_results = {}
        
        return scraping_results

    def aggregate(self, scraping_results, hashtag_results):
        if self.output_format=='flat':
            # Write results to csv
            scraping_results = scraping_results.append(hashtag_results.as_dataframe())
        
        elif self.output_format=='json':
            # Write results to json
            scraping_results = {**scraping_results, **hashtag_results.as_json()}

        return scraping_results

    def save_to_file(self,scraping_results):
        # Save to file
        if self.output_format=='flat':
            scraping_results.to_csv(self.output_folder + 'output_hashtags.csv',index=False)
        elif self.output_format=='json':
            with open(self.output_folder + 'output_hashtags.json', 'w') as outfile:
                json.dump(scraping_results, outfile,indent=4)