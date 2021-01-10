from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from datetime import datetime

import time
import json
import hashlib

import pandas as pd

from webdriver_manager.chrome import ChromeDriverManager

from utils import ScrapingException, HumanCheckException, wait_for_loading, wait_for_scrolling, is_url_valid, HashtagScrapingResult, Post, HashtagResultsSaver

class HashtagScraper(Thread):

    def __init__(self, linkedin_username, linkedin_password, hashtags, headless=False, output_format='flat'):

        # Initialize thread
        Thread.__init__(self)

        # Options of the Chrome instance
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--headless')

        # Instantiate Chrome
        self.browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)

        # Make linkedin credentials available to other functions
        self.linkedin_username = linkedin_username
        self.linkedin_password = linkedin_password

        # Make Hashtag urls available to other functions
        self.hashtags = hashtags

        # Output setting
        self.output_format = output_format
        self.output_folder = '../output/'

    def run(self):
        """
            Start parallel jobs. This function is required by the threading module.
        """
        
        # Login to LinkedIn
        self.browser.get('https://www.linkedin.com/uas/login')

        username_input = self.browser.find_element_by_id('username')
        username_input.send_keys(self.linkedin_username)

        password_input = self.browser.find_element_by_id('password')
        password_input.send_keys(self.linkedin_password)
        password_input.submit()

        # Check, if we are on the correct page
        if not self.browser.current_url == "https://www.linkedin.com/feed/":
            time.sleep(40)
            raise AuthenticationException()

        # Actual work: For each url, scrape posts and store data
        hashtag_results_saver = HashtagResultsSaver(self.output_format,self.output_folder)
        scraping_results = hashtag_results_saver.allocate_object()

        # Loop
        for hashtag in self.hashtags:

            # Create hashtag url
            hashtag_url = 'https://www.linkedin.com/feed/hashtag/?keywords=' + hashtag

            # Scrape hashtag posts of this url
            hashtag_posts = self.scrape_hashtag_posts(hashtag_url)

            # Get date of scraping
            scraping_date = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

            # Collect results for hashtag in data class
            hashtag_results = HashtagScrapingResult(
                hashtag=hashtag,
                scraping_date=scraping_date,
                hashtag_posts=hashtag_posts
            )

            # Store results for all hashtags
            scraping_results = hashtag_results_saver.aggregate(scraping_results, hashtag_results)

        # Save to file
        hashtag_results_saver.save_to_file(scraping_results)

        # Closing the Chrome instance
        self.browser.quit()

    def scrape_hashtag_posts(self, hashtag_url, waiting_time=10):    
        """
            Main scraping function: Calls pageload_and_scrape() function. Or recursively itself with delay on error (e.g. when showing a captcha).
        """
        
        try:
            # Try scrape posts
            hashtag_posts = self.pageload_and_scrape_posts(hashtag_url)

        except HumanCheckException:
            # If Human Check Exception occurs, wait ...
            time.sleep(waiting_time)

            # and call this function again
            hashtag_posts = self.scrape_hashtag_posts(hashtag_url, int(waiting_time*1.5))

        except ScrapingException:
            # If Scraping Exception, return with None
            hashtag_posts = None

        return hashtag_posts

    def pageload_and_scrape_posts(self, hashtag_url):
        """
            Main function that will load the full page (to a certain extend) by "scrolling" down and scrape all posts that have been loaded.
        """
        # Check, if the current url is valid (syntax)
        if not is_url_valid(hashtag_url):
            raise ScrapingException

        # Load the url
        self.browser.get(hashtag_url)

        # Check correct loading of page and eventual Human Check
        if not str(self.browser.current_url).strip() == hashtag_url.strip():
            if self.browser.current_url == 'https://www.linkedin.com/in/unavailable/':
                raise ScrapingException
            else:
                raise HumanCheckException

        # Scroll down to see more posts
        self.load_full_page()

        # Scrape posts
        posts = self.scrape_posts()

        return posts

    def scrape_posts(self):
        """
            Scrape each post from the loaded hastag feed.
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
                
                # Convert to json
                posts[post_id_hash] = post.as_json()
  
            except:
                pass

        return posts

    def load_full_page(self):
        """
            Load the full page by imitating a "scrolling".
        """
        window_height = self.browser.execute_script("return window.innerHeight")
        scrolls = 1
        while scrolls * window_height < self.browser.execute_script("return document.body.offsetHeight"):
            
            self.browser.execute_script('window.scrollTo(0, ' + str(window_height * scrolls) + ');')
           
            wait_for_scrolling()
           
            scrolls += 1

            # DEBUG: Manual break loop (for dev)
            if scrolls > 10:
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