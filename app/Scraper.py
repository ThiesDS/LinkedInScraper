from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from datetime import datetime

import time
import json
import hashlib

import pandas as pd

from webdriver_manager.chrome import ChromeDriverManager

from utils import *

class HashtagScraper(Thread):

    def __init__(self, linkedin_username, linkedin_password, hashtags, headless=False, scroll_depth=50, output_format='json'):

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

        # Scroll depth
        self.scroll_depth = scroll_depth

        # Output setting
        self.output_format = output_format
        self.output_folder = '../output/'

    def run(self):
        """
            Start parallel jobs. This function is required by the threading module.
        """
        
        # Login to LinkedIn
        linkedin_login(self.browser,self.linkedin_username,self.linkedin_password)

        # Check, if we are on the correct page. After login, we should've been redirected to the feed
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
                hashtag=remove_escapes(hashtag),
                scraping_date=remove_escapes(scraping_date),
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
        
        # Get number of posts (depending on scroll-depth)
        num_posts = self.browser.execute_script("return document.querySelectorAll('[data-id]').length")
        
        # Initialize dict
        posts = {}

        for i in range(0,num_posts):
            try:
                # Get id of post
                data_id = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getAttribute('data-id')")
                
                # Get user name of post
                post_username = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__name')[0].innerText")
                
                # Get user description of post
                post_userdescription = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__description')[0].innerText")

                # Get time of post
                post_published = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-actor__sub-description')[0].innerText")

                # Get text of post
                post_text = self.browser.execute_script("return document.querySelectorAll('[data-id]')[" + str(i) + "].getElementsByClassName('feed-shared-text')[0].innerText")
                
                # Create hash from data_id and use it as id
                post_id = hashlib.sha1(bytes(data_id, encoding='utf-8')).hexdigest()

                # Create post object
                post = Post(username=remove_escapes(post_username),
                            userdescription=remove_escapes(post_userdescription),
                            published=remove_escapes(post_published),
                            text=remove_escapes(post_text),
                            data_id = data_id
                        )
                
                # Convert to json
                posts[post_id] = post.as_json()
  
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
            if scrolls > int(self.scroll_depth):
                break

class ProfileScraper(Thread):

    def __init__(self, linkedin_username, linkedin_password, profiles, headless=False, output_format='json'):

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
        self.profiles = profiles

        # Output setting
        self.output_format = output_format
        self.output_folder = '../output/'

    def run(self):
        """
            Start parallel jobs. This function is required by the threading module.
        """
        
        # Login to LinkedIn
        linkedin_login(self.browser,self.linkedin_username,self.linkedin_password)

        # Check, if we are on the correct page. After login, we should've been redirected to the feed
        if not self.browser.current_url == "https://www.linkedin.com/feed/":
            time.sleep(40)
            raise AuthenticationException()

        # Actual work: For each url, scrape posts and store data
        #profiles_results_saver = ProfilesResultsSaver(self.output_format,self.output_folder)
        #scraping_results = profiles_results_saver.allocate_object()

        # Loop
        for profile in self.profiles:

            # Create profile url
            profile_url = 'https://www.linkedin.com/in/' + remove_escapes(profile) + '/'

            # Scrape profile
            profile_information = self.scrape_profile(profile_url)

            # Get date of scraping
            scraping_date = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

            # Collect results for hashtag in data class
            profile_results = ProfileScrapingResult(
                profile=remove_escapes(profile),
                scraping_date=scraping_date,
                profile_information=profile_information.reprJSON()
            )
            print(profile_results.reprJSON())
            # Store profile results by adding them to scraping results
            #scraping_results = profile_results_saver.aggregate(scraping_results, profile_results)

        # Save to file
        #profile_results_saver.save_to_file(scraping_results)

        # Closing the Chrome instance
        self.browser.quit()

    def scrape_profile(self, linkedin_url, waiting_time=10):

        try:
            profile = self.__scrape_profile(linkedin_url)

        except HumanCheckException:
            print("Please solve the captcha.")
            print("Another try will be performed within 10 seconds...")
            time.sleep(waiting_time)

            profile = self.scrape_profile(linkedin_url, int(waiting_time*1.5))

        except ScrapingException:
            profile = None

        return profile

    def __scrape_profile(self, profile_linkedin_url):

        if not is_url_valid(profile_linkedin_url):
            raise ScrapingException

        self.browser.get(profile_linkedin_url)

        # Check correct loading of profile and eventual Human Check
        if not str(self.browser.current_url).strip() == profile_linkedin_url.strip():
            if self.browser.current_url == 'https://www.linkedin.com/in/unavailable/':
                raise ScrapingException
            else:
                raise HumanCheckException
        
        self.load_full_page()

        # SCRAPING
        profile_name = self.scrape_profile_name()
        email = self.scrape_email()
        skills = self.scrape_skills()
        jobs = self.scrape_jobs()  # keep as last scraping

        return Profile(
            name=profile_name,
            email=email,
            skills=skills,
            jobs=jobs
        )

    def scrape_profile_name(self):
        return self.browser.execute_script(
            "return document.getElementsByClassName('pv-top-card--list')[0].children[0].innerText")

    def scrape_email(self):
        # > click on 'Contact info' link on the page
        self.browser.execute_script(
            "(function(){try{for(i in document.getElementsByTagName('a')){let el = document.getElementsByTagName("
            "'a')[i]; if(el.innerHTML.includes('Contact info')){el.click();}}}catch(e){}})()")
        wait_for_loading()

        # > gets email from the 'Contact info' popup
        try:
            email = self.browser.execute_script(
                "return (function(){try{for (i in document.getElementsByClassName('pv-contact-info__contact-type')){ "
                "let el = document.getElementsByClassName('pv-contact-info__contact-type')[i]; if("
                "el.className.includes( 'ci-email')){ return el.children[2].children[0].innerText; } }} catch(e){"
                "return '';}})()")
        except WebDriverException:
            email = ''

        try:
            self.browser.execute_script("document.getElementsByClassName('artdeco-modal__dismiss')[0].click()")
        except WebDriverException:
            pass

        return email

    def scrape_jobs(self):

        try:
            jobs = self.browser.execute_script(
                "return (function(){ var jobs = []; var els = document.getElementById("
                "'experience-section').getElementsByTagName('ul')[0].getElementsByTagName('li'); for (var i=0; "
                "i<els.length; i++){   if(els[i].className!='pv-entity__position-group-role-item-fading-timeline'){   "
                "  if(els[i].getElementsByClassName('pv-entity__position-group-role-item-fading-timeline').length>0){ "
                "     } else {       try {         position = els[i].getElementsByClassName("
                "'pv-entity__summary-info')[0].getElementsByTagName('h3')[0].innerText;       }       catch(err) { "
                "position = ''; }        try {         company_name = els[i].getElementsByClassName("
                "'pv-entity__summary-info')[0].getElementsByClassName('pv-entity__secondary-title')[0].innerText;     "
                "  } catch (err) { company_name = ''; }        try{         date_ranges = els["
                "i].getElementsByClassName('pv-entity__summary-info')[0].getElementsByClassName("
                "'pv-entity__date-range')[0].getElementsByTagName('span')[1].innerText;       } catch (err) {"
                "date_ranges = ''; }        try{         job_location = els[i].getElementsByClassName("
                "'pv-entity__summary-info')[0].getElementsByClassName('pv-entity__location')[0].getElementsByTagName("
                "'span')[1].innerText;       } catch (err) {job_location = ''; }        try{         company_url = "
                "els[i].getElementsByTagName('a')[0].href;       } catch (err) {company_url = ''; }        jobs.push("
                "[position, company_name, company_url, date_ranges, job_location]);     }   } } return jobs; })();")
        except WebDriverException:
            jobs = []
            
        clean_jobs = []
        for job in jobs: 
            if job[2] != '':
                clean_jobs.append(job)
                
        parsed_jobs = []
        for job in clean_jobs:
            company_industry, company_employees = self.scrape_company_details(job[2])

            # Get company information
            cmp_obj = Company(
                name=job[1],
                industry=company_industry,
                employees=company_employees
            )
            cmp_dict = cmp_obj.reprJSON()
            
            # Get location information
            loc_obj = location=Location(job[4])
            loc_dict = loc_obj.reprJSON()
            
            # Combine to job object
            job_obj = Job(position=job[0],
                company=cmp_dict,
                location=loc_dict,
                date_range=job[3]
            )
            job_dict = job_obj.reprJSON()

            # Update list
            parsed_jobs.append(job_dict)

        return parsed_jobs

    def scrape_company_details(self, company_url):

        self.browser.get(company_url)

        try:
            company_employees = self.browser.execute_script(
                "return document.querySelector('a[data-control-name" +
                '="topcard_see_all_employees"' +
                "]').innerText.split(' employees')[0].split(' ').lastObject;"
            )
        except WebDriverException:
            company_employees = ''

        try:
            company_industry = self.browser.execute_script(
                "return document.getElementsByClassName('org-top-card-summary-info-list__info-item')[0].innerText")
        except WebDriverException:
            company_industry = ''

        return company_industry, company_employees

    def scrape_skills(self):
        try:
            self.browser.execute_script(
                "document.getElementsByClassName('pv-skills-section__additional-skills')[0].click()")
        except WebDriverException:
            return []

        wait_for_loading()

        try:
            return self.browser.execute_script(
                "return (function(){els = document.getElementsByClassName('pv-skill-category-entity');results = ["
                "];for (var i=0; i < els.length; i++){results.push(els[i].getElementsByClassName("
                "'pv-skill-category-entity__name-text')[0].innerText);}return results;})()")
        except WebDriverException:
            return []

    def load_full_page(self):
        window_height = self.browser.execute_script("return window.innerHeight")
        scrolls = 1
        while scrolls * window_height < self.browser.execute_script("return document.body.offsetHeight"):
            self.browser.execute_script('window.scrollTo(0, ' + str(window_height * scrolls) + ');')
            wait_for_scrolling()
            scrolls += 1

        for i in range(self.browser.execute_script(
                "return document.getElementsByClassName('pv-profile-section__see-more-inline').length")):
            try:
                self.browser.execute_script(
                    "document.getElementsByClassName('pv-profile-section__see-more-inline')[" + str(
                        i) + "].click()")
            except WebDriverException:
                pass

            wait_for_loading()