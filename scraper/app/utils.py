import json
import re
import time


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
    def __init__(self, hashtag_url: str, scraping_date: str, hashtag_posts: {str}):
        self.hashtag_url = hashtag_url
        self.scraping_date = scraping_date
        self.hashtag_posts = hashtag_posts

    def as_json(self):
        return dict(hashtag_url=self.hashtag_url, 
                    scraping_date=self.scraping_date, 
                    hashtag_posts=self.hashtag_posts)

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
