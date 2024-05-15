from .scraper import Scraper 
from event import Event
from standardnames import StandardNames

from unidecode import unidecode
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from time import sleep


class BetclicScraper(Scraper):

    def __init__(self, url):
        super().__init__(url)
        # wait for page to load and reject cookies
        sleep(self.LONG_PAUSE_TIME)
        decline = self.driver.find_element(By.XPATH, '//*[@id="popin_tc_privacy_button_3"]')
        decline.click()
        self.scroll_to_bottom(self.SHORT_PAUSE_TIME, 1500)
        self.html = BeautifulSoup(self.driver.page_source, 'html.parser')

    def scrape(self, dict_event):
        events = self.html.findAll('sports-events-event')
        for event in events:            
            if (        (not 'is-live' in event.find('a')['class'])     # cannot handle live events
                    and Scraper.check_if_markup_exists(event, 'div', 'class', 'event_infoTime')             # 
                    and Scraper.check_if_markup_exists(event, 'div', 'class', 'scoreboard_contestant-1')    # checking that the event has a date and two teams associated
                    and Scraper.check_if_markup_exists(event, 'div', 'class', 'scoreboard_contestant-2')    #
                ):      
                event_date_time = Scraper.to_date_time(event.find('div', {'class': 'event_infoTime'}).text.strip())
                team1 = event.find('div', {'class': 'scoreboard_contestant-1'}).find('div').text.strip()
                team2 = event.find('div', {'class': 'scoreboard_contestant-2'}).find('div').text.strip()
                team1 = unidecode(team1.lower())
                team2 = unidecode(team2.lower())
                competition_name = event.find('span', {'class': 'breadcrumb_itemLabel'}).text.strip()
                if (('women' in competition_name) or ('f.' in competition_name) or ('(f)' in competition_name)):
                    team1 = team1 + ' women'
                    team2 = team2 + ' women'
                ids = StandardNames.assign_ids(event_date_time, team1, team2, 'Betclic') # tuple containing the ids of the 2 teams
                if not ids is None: # if no match has been found for the event
                    if (Scraper.check_if_markup_exists(event, 'button', 'class', 'is-odd')):    # checking that odds are associated with the event         
                        odds_panel = event.findAll('button', {'class': 'is-odd'})
                        if (len(odds_panel) == 3): 
                            odds1 = float(odds_panel[0].findAll('span', {'class': 'btn_label'})[1].text.strip().replace(',', '.'))
                            oddsx = float(odds_panel[1].findAll('span', {'class': 'btn_label'})[1].text.strip().replace(',', '.'))
                            odds2 = float(odds_panel[2].findAll('span', {'class': 'btn_label'})[1].text.strip().replace(',', '.'))
                            #print(eventDateTime.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + ' (' + str(odds1) + ', ' + str(oddsX) + ', ' + str(odds2) + ')')
                            dict_event.append_event(event_date_time, team1, team2, 'Betclic', odds1, oddsx, odds2)