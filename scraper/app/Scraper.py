from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from datetime import datetime

import time
import json
import hashlib

from webdriver_manager.chrome import ChromeDriverManager

from utils import ScrapingException, HumanCheckException, wait_for_loading, wait_for_scrolling, is_url_valid, HashtagScrapingResult, Post

class HashtagScraper(Thread):

    def __init__(self, linkedin_username, linkedin_password, hashtag_urls, headless=False):

        Thread.__init__(self)

        # Creation of a new instance of Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        if headless:
            options.add_argument('--headless')

        self.browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)

        self.hashtag_urls = hashtag_urls

        self.results = []

        self.linkedin_username = linkedin_username
        self.linkedin_password = linkedin_password

    def run(self):
        print('LOG: Enter function run()')
        
        # Login in LinkedIn
        self.browser.get('https://www.linkedin.com/uas/login')

        username_input = self.browser.find_element_by_id('username')
        username_input.send_keys(self.linkedin_username)

        password_input = self.browser.find_element_by_id('password')
        password_input.send_keys(self.linkedin_password)
        password_input.submit()

        if not self.browser.current_url == "https://www.linkedin.com/feed/":
            time.sleep(40)
            raise AuthenticationException()

        for linkedin_url in self.hashtag_urls:
            hashtag_feed = self.scrape_hashtag_feed(linkedin_url)
            scraping_date = datetime.now().strftime('%Y-%m-%d')
            scraping_results = HashtagScrapingResult(
                hashtag_url=linkedin_url,
                scraping_date=scraping_date,
                hashtag_feed=hashtag_feed,
            )
        
        # Write to json
        with open('../output/output.txt', 'w') as outfile:
            json.dump(scraping_results.as_json(), outfile,indent=4)

        # Closing the Chrome instance
        self.browser.quit()

    def scrape_hashtag_feed(self, linkedin_url, waiting_time=10):    
        print('LOG: Enter function scrape_hashtag_feed()')
        
        try:
            hashtag_feed = self.__scrape_hashtag_feed(linkedin_url)

        except HumanCheckException:
            print("Please solve the captcha.")
            print("Another try will be performed within 10 seconds...")
            time.sleep(waiting_time)

            hashtag_feed = self.scrape_hashtag_feed(linkedin_url, int(waiting_time*1.5))

        except ScrapingException:
            hashtag_feed = None

        return hashtag_feed

    def __scrape_hashtag_feed(self, hashtag_linkedin_url):
        print('LOG: Enter function __scrape_hashtag_feed()')
        
        if not is_url_valid(hashtag_linkedin_url):
            raise ScrapingException

        self.browser.get(hashtag_linkedin_url)

        # Check correct loading of profile and eventual Human Check
        if not str(self.browser.current_url).strip() == hashtag_linkedin_url.strip():
            if self.browser.current_url == 'https://www.linkedin.com/in/unavailable/':
                raise ScrapingException
            else:
                raise HumanCheckException

        # Scrall down to see more posts
        self.load_full_page()

        # SCRAPING
        posts = self.scrape_posts()

        #print(posts)

        return posts

    def scrape_posts(self):
        """
            Scrape each post from hastag feed.
        """
        print("LOG: Enter scrape_posts()")
        
        # Get number of posts (depending on scroll-depth)
        num_posts = self.browser.execute_script("return document.querySelectorAll('[data-id]').length")
        
        # Initialize dict
        posts = {}

        for i in range(0,num_posts):
            try:
                # Get id of post
                post_id = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getAttribute('data-id')")
                
                # Get user name of post
                post_username = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__name')[0].innerText")
                
                # Get user description of post
                post_userdescription = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__description')[0].innerText")

                # Get time of post
                post_published = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__sub-description')[0].innerText")

                # Get text of post
                post_text = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-text')[0].innerText")
                
                # Create post object
                post = Post(id=post_id,
                            username=post_username,
                            userdescription=post_userdescription,
                            published=post_published,
                            text=post_text
                        )
                
                # Create hash from id
                post_id_hash = hashlib.sha1(bytes(post_id, encoding='utf-8')).hexdigest()
                
                # Save as json
                posts[post_id_hash] = post.as_json()
            except:
                pass

        return posts

    def load_full_page(self):
        print('LOG: Enter function load_full_page()')
        window_height = self.browser.execute_script("return window.innerHeight")
        scrolls = 1
        while scrolls * window_height < self.browser.execute_script("return document.body.offsetHeight"):
            self.browser.execute_script('window.scrollTo(0, ' + str(window_height * scrolls) + ');')
            wait_for_scrolling()
            scrolls += 1
            print(f"Scrolling progress: {scrolls}")
            # DEBUG: Manual break loop (for dev)
            if scrolls > 50:
                break

        # Code snippets, maybe use later, otherwise delete
        """
    def scrape_post_names(self):
        names = []
        for i in range(5):
            names.append(self.browser.execute_script("return document.getElementsByClassName('feed-shared-actor__name') \
                [" + str(i) + "].children[0].innerText"))
        return names

    def scrape_post_texts(self):
        texts = []
        for i in range(5):
            texts.append(self.browser.execute_script("return document.getElementsByClassName('feed-shared-text') \
                [" + str(i) + "].children[0].innerText"))
        return texts
        """
        # Comment out for now, as I don't know what it's good for. Maybe we need it later. 
        """
        for i in range(self.browser.execute_script(
                "return document.getElementsByClassName('pv-profile-section__see-more-inline').length")):
            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[" + str(
                        i) + "].click()")
            except WebDriverException:
                pass

            wait_for_loading()
        """