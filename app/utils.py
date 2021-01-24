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
    def __init__(self, username: str, userdescription: str, published: str, text: str, data_id: str):
        self.username = username
        self.userdescription = userdescription
        self.published = published
        self.text = text
        self.data_id = data_id

    def as_json(self):
        return dict(username=self.username,
                    userdescription=self.userdescription,
                    published=self.published,
                    text=self.text,
                    data_id=self.data_id
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
        # Initialize df. Add columns dynamically, as we only have to change the columns in one place above.
        cols = ['hashtag','scraping_date'] + ['id'] + list(self.hashtag_posts[list(self.hashtag_posts.keys())[0]].keys())
        df = pd.DataFrame(columns=cols)

        # Loop over all hastag urls
        for key in self.hashtag_posts.keys():
            df = df.append({**{'hashtag':self.hashtag},
                            **{'scraping_date':self.scraping_date},
                            **{'id':key},
                            **self.hashtag_posts[key]},
                 ignore_index=True)

        return df

def is_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def wait_for_loading():
    time.sleep(2)

def wait_for_scrolling():
    time.sleep(1)

def remove_escapes(s):
    """
        Helper to remove escape characters from hashtag.
    """
    # Create escape characters
    escapes = ''.join([chr(char) for char in range(1, 32)])

    # Instantiate translator
    translator = s.maketrans('', '', escapes)

    # Replace
    t = s.translate(translator)

    return t

def linkedin_login(browser,linkedin_username,linkedin_password):

    browser.get('https://www.linkedin.com/uas/login')

    username_input = browser.find_element_by_id('username')
    username_input.send_keys(linkedin_username)

    password_input = browser.find_element_by_id('password')
    password_input.send_keys(linkedin_password)
    password_input.submit()

class Location:
    def __init__(self, location: str):
        self.location = location
        self.city = ''
        self.country = ''

        if ',' in location:
            try:
                self.city = location.split(',')[0].strip()
                self.country = location.split(',')[-1].strip()
            except:
                pass

    def reprJSON(self):
        return dict(location=self.location, city=self.city, country=self.country)

class Company:
    def __init__(self, name: str, industry: str, employees: str):
        self.name = name
        self.industry = industry
        self.employees = employees

    def reprJSON(self):
        return dict(name=self.name, industry=self.industry, employees=self.employees)

class Job:
    def __init__(self, position: str, company: Company, location: Location, date_range: str):
        self.position = position
        self.company = company
        self.location = location
        self.date_range = date_range

    def reprJSON(self):
        return dict(position=self.position, company=self.company, location=self.location, date_range=self.date_range)

class Profile:
    def __init__(self, name: str, email: str, skills: [str], jobs: [Job]):
        self.name = name
        self.email = email
        self.skills = skills
        self.jobs = jobs

    def reprJSON(self):
        return dict(name=self.name, email=self.email, skills=self.skills, jobs=self.jobs)

class ProfileScrapingResult:
    def __init__(self, profile: str, scraping_date: str, profile_information: dict):
        self.profile = profile
        self.scraping_date = scraping_date
        self.profile_information = profile_information

    def as_json(self):
        d = {}
        d[self.profile] = {
            'profile':self.profile, 
            'scraping_date':self.scraping_date, 
            'profile_information':self.profile_information
        }
        return d

    def is_error(self):
        return self.profile_information is None

class ResultsSaver():
    """
        Helper to save hashtag results to a file dependent on the output format
    """

    def __init__(self, output_format, output_folder):
        self.output_format = output_format
        self.output_folder = output_folder

    def initialize(self):
        if self.output_format=='csv':
            scraping_results = pd.DataFrame()
        elif self.output_format=='json':
            scraping_results = {}
        
        return scraping_results

    def update(self, scraping_results, results):
        if self.output_format=='csv':
            # Write results to csv
            scraping_results = scraping_results.append(results.as_dataframe())
        
        elif self.output_format=='json':
            # Write results to json
            scraping_results = {**scraping_results, **results.as_json()}

        else:
            sys.exit("Output format not specified.")

        return scraping_results

    def save_to_file(self,scraping_results, output_file):
        # Save to file
        if self.output_format=='csv':
            scraping_results.to_csv(self.output_folder + output_file + '.csv',index=False)
        elif self.output_format=='json':
            with open(self.output_folder + output_file + '.json', 'w') as outfile:
                json.dump(scraping_results, outfile,indent=4)