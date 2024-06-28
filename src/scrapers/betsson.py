from .scraper import Scraper 
from standardnames import StandardNames

from unidecode import unidecode
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep


class BetssonScraper(Scraper):

    def __init__(self, url):
        super().__init__(url)
        # wait for page to load and reject cookies
        sleep(self.LONG_PAUSE_TIME)
        decline = self.driver.find_element(By.XPATH, '//*[@class="cookiePopupStepOne"]/div[1]/div[3]/span')
        decline.click()
        sleep(self.LONG_PAUSE_TIME)
        self.scroll_to_bottom(self.SHORT_PAUSE_TIME, 1500)
        self.html = BeautifulSoup(self.driver.page_source, 'html.parser')

    def scrape(self, dict_event):
        events = self.html.findAll('div', {'class': 'eventWrapper'}) 
        for event in events:
            competition_name = event.find('span', {'class': 'parentName'}).text.strip()
            event_date_time = Scraper.to_date_time(event.find('div', {'class': 'exhibitionDate'}).text.strip() + ' ' + event.find('div', {'class': 'exhibitionTime'}).text.strip()) 
            team1 = unidecode(event.find('div', {'class': 'exhibitionHome'}).text.strip().lower())
            team2 = unidecode(event.find('div', {'class': 'exhibitionAway'}).text.strip().lower())
            if (('women' in competition_name) or ('f.' in competition_name) or ('(f)' in competition_name)):
                team1 = team1 + ' women'
                team2 = team2 + ' women'
            ids = StandardNames.assign_ids(event_date_time, team1, team2, 'Betsson') # tuple containing the ids of the 2 teams
            if not ids is None: # if no match has been found for the event
                odds = event.findAll('div', {'class': 'betMarketOddCard'})
                if len(odds) >= 3: # if odds are associated with every outcome
                    odds1 = float(odds[0].find('div', {'class': 'betOddValue'}).text.strip().replace(',', '.'))
                    oddsx = float(odds[1].find('div', {'class': 'betOddValue'}).text.strip().replace(',', '.'))
                    odds2 = float(odds[2].find('div', {'class': 'betOddValue'}).text.strip().replace(',', '.'))
                    #print(event_date_time.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + ' (' + str(odds1) + ', ' + str(oddsx) + ', ' + str(odds2) + ')')
                    dict_event.append_event(event_date_time, team1, team2, 'Betsson', odds1, oddsx, odds2)