from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import datetime
from time import sleep


class Scraper(ABC):
    """ Base class to gather all the methods that will be helpfull to scrape odds on the different bookmakers websites """
    
    LONG_PAUSE_TIME = 2
    SHORT_PAUSE_TIME = 0.3

    @abstractmethod
    def __init__(self, url):
        """ Create the driver and get the url """
        chrome_options = Options()
        #chrome_options.add_argument('--headless')   # comment this line to debug the scraper
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(url)

    def close(self):
        self.driver.quit()

    @abstractmethod
    def scrape(self):
        """ specific to each bookmaker """
        pass

    def scroll_down(self, last_height, new_height):
        """ Scroll down from last_heigth to new_heigth """
        self.driver.execute_script("window.scrollTo({0}, {1});".format(last_height, new_height))

    def scroll_to_bottom(self, scroll_wait_time, pace):
        """ Scroll down to the bottom of the page """
        last_height = 0
        new_height = pace
        while True:
            self.scroll_down(last_height,new_height)
            # Wait to load page
            sleep(scroll_wait_time)
            last_height = new_height
            new_height = min(new_height+pace, self.driver.execute_script("return document.body.scrollHeight"))
            if last_height == new_height:
                break

    @staticmethod
    def check_if_markup_exists(html, markup, attr=None, value=None):
        item = html.find(markup, {attr: value})
        if item is None:
            return False
        else:
            return True
        
    @staticmethod
    def to_date_time(date_time_str):
        """ To be completed as more bookmakers are added to the list """
        if "Aujourd'hui" in date_time_str:
            date, time = date_time_str.split()
            hour, min = time.split(':')
            res = datetime.datetime.today().replace(hour=int(hour), minute=int(min), second=0, microsecond=0)
        elif 'Après-demain' in date_time_str:
            date, time = date_time_str.split()
            hour, min = time.split(':')
            res = (datetime.datetime.today() + datetime.timedelta(days=2)).replace(hour=int(hour), minute=int(min), second=0, microsecond=0)
        elif 'Demain' in date_time_str:
            date, time = date_time_str.split()
            hour, min = time.split(':')
            res = (datetime.datetime.today() + datetime.timedelta(days=1)).replace(hour=int(hour), minute=int(min), second=0, microsecond=0)
        else:
            date, time = date_time_str.split()
            if len(date) == 5:  # if year is missing in the date
                day, month = date.split('/')
                day_int = int(day)
                month_int = int(month)
                current_month = datetime.date.today().month
                current_day = datetime.date.today().day
                if (month_int < current_month or (month_int == current_month and day_int < current_day)):
                    day = day + '/' + month + '/' + str(datetime.date.today().year + 1)
                else:
                    date = day + '/' + month + '/' + str(datetime.date.today().year)
                date_time_str = date + ' ' + time
            res = datetime.datetime.strptime(date_time_str, '%d/%m/%Y %H:%M')
        return res

    