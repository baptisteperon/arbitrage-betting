import time
import argparse

from standardnames import StandardNames
from dictionnaryevents import DictEvents
from scrapers.betclic import BetclicScraper
from scrapers.unibet import UnibetScraper
from telegrambot import TelegramBot

import time
import pandas as pd
import concurrent.futures

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--manualmapping",  nargs='?', const=True, type=bool)
    args = parser.parse_args()
    perform_manual_mapping = args.manualmapping
        
    try:
        bot = TelegramBot()
    except:
        print('error while creating bot object.\nQuiting')
        return None

    while True:
        start_time = time.time()
        try:
            StandardNames.get_standard_events()
            with open('standard_events.txt', 'w') as f:
                f.write(StandardNames.standard_event_to_string())
            dict_events = DictEvents()
            bookmakers_dict = {'Betclic': (BetclicScraper, 'https://www.betclic.fr/football-s1'),
                            'Unibet':  (UnibetScraper, 'https://www.unibet.fr/sport/football')}
            scrapers = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for bookmaker in bookmakers_dict:
                    scraping_method = bookmakers_dict[bookmaker][0]
                    url = bookmakers_dict[bookmaker][1]
                    futures.append(executor.submit(scraping_method, url))
                for future in concurrent.futures.as_completed(futures):
                    scrapers.append(future.result())
            for scraper in scrapers:
                scraper.scrape(dict_events)
                scraper.close()

            print(StandardNames.dict_to_string(StandardNames.team_names), file=open('team_names.txt', 'w'))
            print(StandardNames.dict_to_string(StandardNames.team_ids), file=open('team_ids.txt', 'w'))

            print(str(len(StandardNames.unmatched_events)) + ' unmatched events : \n')
            if perform_manual_mapping:
                print('Unmatched events : \n')
                cpt=0
                for as_of_date, matches in StandardNames.unmatched_events.items():
                    for (team1, team2, bookmaker) in matches:
                        cpt+=1
                        print(as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2)
                print('\n' + str(len(StandardNames.unmatched_events)) + ' unmatched events : \n')
                #StandardNames.manual_mapping()
                StandardNames.manual_mapping_telegram(bot)
            else:
                print('Skipping manual mapping\n')

            with open('arb_opportunities.txt', 'w') as f:
                f.write(dict_events.arbitrage_to_string())
            dict_events.look_for_arbitrage(bot)
        except:
            break
        time_delta = time.time()-start_time
        # we scrape the websites every 10mins
        if (time_delta >= 600):
            continue
        else:
            time.sleep(600-time_delta)

    StandardNames.team_ids.close()
    StandardNames.team_names.close()

if __name__ == "__main__":
    main()