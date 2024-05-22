import config
import datetime
import time
from event import Event
from standardnames import StandardNames
from dictionnaryevents import DictEvents
from scrapers.betclic import BetclicScraper
from scrapers.unibet import UnibetScraper
from scrapers.zebet import ZEBetScraper

def maintest():
    """ This main is used to test the different scrapers
    """
    dict_events = DictEvents()
    #scraper = UnibetScraper('https://www.unibet.fr/sport/football')
    #scraper = BetclicScraper('https://www.betclic.fr/football-s1')
    scraper = ZEBetScraper('https://www.zebet.fr/fr/sport/13-football')
    scraper.scrape(dict_events)
    scraper.close()

if __name__ == "__main__":
    maintest()