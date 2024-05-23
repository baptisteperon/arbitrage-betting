import time
import argparse

from standardnames import StandardNames
from dictionnaryevents import DictEvents
from scrapers.betclic import BetclicScraper
from scrapers.unibet import UnibetScraper
from scrapers.zebet import ZEBetScraper
from telegrambot import TelegramBot

import time
import pandas as pd
import concurrent.futures

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--manualmapping', metavar='M', type=bool, default=False,
                        help="when True, the program asks the user (via Telegram messages) to manually map events that couldn't be mapped automatically (default = False)")
    parser.add_argument('-r', '--refresh', metavar='R', type=int, default=10,
                        help='time delta in minutes between each scraping session (the default behavior is one every 10mins, minimum value = 1)')
    parser.add_argument('-s', '--stake', metavar='s', type=int, default=100,
                        help='Total amount to bet, distributed between the different outcomes (default value is 100)')
    args = parser.parse_args()
    perform_manual_mapping = args.manualmapping
    refresh_time_delta = args.refresh
    stake = args.stake

    print(time.strftime(time.time()) + ' : Initializing Telegram bot...')    
    try:
        bot = TelegramBot()
    except:
        print('error while creating bot object.\nQuiting')
        return None
    print(time.strftime(time.time()) + ' : Telegram Boot successfully created')

    while True:
        start_time = time.time()
        try:
            print(time.strftime(time.time()) + ' : Retrieving standard events...')
            is_dict_updated = StandardNames.get_standard_events()
            if is_dict_updated:
                with open('standard_events.txt', 'w') as f:
                    f.write(StandardNames.standard_event_to_string())
                print(time.strftime(time.time()) + ' : Standard events retrieved (exported in standard_events.txt)')
            else:
                print(time.strftime(time.time()) + ' : Standard events already retrieved for today')
            dict_events = DictEvents()
            bookmakers_dict = {'Betclic': (BetclicScraper, 'https://www.betclic.fr/football-s1'),
                            'Unibet':  (UnibetScraper, 'https://www.unibet.fr/sport/football'),
                            'ZEBet': (ZEBetScraper, 'https://www.zebet.fr/fr/sport/13-football')}
            scrapers = []
            print(time.strftime(time.time()) + ' : Scraping bookmakers...')
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
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
            print(time.strftime(time.time()) + ' : Done scraping bookmakers')

            print(StandardNames.dict_to_string(StandardNames.team_names), file=open('team_names.txt', 'w'))
            print(StandardNames.dict_to_string(StandardNames.team_ids), file=open('team_ids.txt', 'w'))

            print(str(len(StandardNames.unmatched_events)) + ' unmatched events : \n')
            if perform_manual_mapping:
                print('Unmatched events :')
                cpt=0
                for as_of_date, matches in StandardNames.unmatched_events.items():
                    for (team1, team2, bookmaker) in matches:
                        cpt+=1
                        print('\t' + as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2)
                print('\n' + str(len(StandardNames.unmatched_events)) + ' unmatched events : \n')
                #StandardNames.manual_mapping()
                StandardNames.manual_mapping_telegram(bot)
            else:
                print('Skipping manual mapping\n')

            with open('odds_recap.txt', 'w') as f:
                f.write(dict_events.odds_to_string())
            dict_events.look_for_arbitrage(bot, stake)
        except:
            break
        print('\n')
        time_delta = time.time()-start_time
        # we scrape the websites every 10mins
        if (time_delta >= refresh_time_delta):
            continue
        else:
            time.sleep(refresh_time_delta-time_delta)

    StandardNames.team_ids.close()
    StandardNames.team_names.close()

if __name__ == "__main__":
    main()