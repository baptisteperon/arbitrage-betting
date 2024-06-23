from .scraper import Scraper 
from standardnames import StandardNames

from unidecode import unidecode
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep


class UnibetScraper(Scraper):
    
    def __init__(self, url):
        super().__init__(url)
        # wait for page to load and reject cookies
        sleep(self.LONG_PAUSE_TIME)
        sleep(self.LONG_PAUSE_TIME)
        #decline = self.driver.find_element(By.XPATH, '//*[@id="ui-cookienotification"]/div/div/div/div[2]/a[1]')
        decline = self.driver.find_element(By.XPATH, '//*[@id="onetrust-close-btn-container"]/button')
        decline.click()
        self.scroll_to_bottom(self.SHORT_PAUSE_TIME, 1500)
        self.html = BeautifulSoup(self.driver.page_source, 'html.parser')

    def scrape(self, dict_event):
        content = self.html.find('section', {'class': 'eventsdays-list'})
        events = content.findAll('section', {'class': 'eventcard--toplight'})
        for event in events:
            if (event == None) :
                events.remove(event)
                continue
            event_date_time_string = event.find('div', {'class': 'eventcard-header-meta'}).text.replace('h', ':')
            if (not ' ' in event_date_time_string):
                event_date_time_string = "Aujourd'hui " + event_date_time_string
            event_date_time = Scraper.to_date_time(event_date_time_string)
            oddsbox1, oddsboxx, oddsbox2 = event.findAll('section', {'id': 'cps-oddbox'})
            team1 = oddsbox1.find('div', {'class': 'oddbox-label'}).text
            team2 = oddsbox2.find('div', {'class': 'oddbox-label'}).text
            team1 = unidecode(team1.lower())
            team2 = unidecode(team2.lower())
            competition_name = event.find('div', {'class': 'eventcard-header-title'}).find('span').text.strip()
            if (('women' in competition_name) or ('f.' in competition_name) or ('(f)' in competition_name)):
                team1 = team1 + ' women'
                team2 = team2 + ' women'
            ids = StandardNames.assign_ids(event_date_time, team1, team2, 'Unibet') # tuple containing the ids of the 2 teams
            if not ids is None: # if no match has been found for the event
                odds1 = float(oddsbox1.find('div', {'class': 'oddbox-value'}).text.strip())
                oddsx = float(oddsboxx.find('div', {'class': 'oddbox-value'}).text.strip())
                odds2 = float(oddsbox2.find('div', {'class': 'oddbox-value'}).text.strip())
                #print(event_date_time.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + ' (' + str(odds1) + ', ' + str(oddsx) + ', ' + str(odds2) + ')')
                dict_event.append_event(event_date_time, team1, team2, 'Unibet', odds1, oddsx, odds2)