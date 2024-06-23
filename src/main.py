import datetime
import argparse
import logging
import time
import concurrent.futures

from standardnames import StandardNames
from dictionnaryevents import DictEvents
from scrapers.betclic import BetclicScraper
from scrapers.unibet import UnibetScraper
from scrapers.zebet import ZEBetScraper
from telegrambot import TelegramBot

def main():

    #logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--manualmapping', action='store_true',
                        help="when this flag is given, the program asks the user (via Telegram messages) to manually map events that couldn't be mapped automatically")
    parser.add_argument('-r', '--refresh', metavar='R', type=int, default=10,
                        help='time delta in minutes between each scraping session (the default behavior is one every 10mins, minimum value = 1)')
    parser.add_argument('-s', '--stake', metavar='s', type=int, default=100,
                        help='Total amount to bet, distributed between the different outcomes (default value is 100)')
    args = parser.parse_args()
    perform_manual_mapping = args.manualmapping
    refresh_time_delta = datetime.timedelta(minutes=args.refresh)
    stake = args.stake

    #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Initializing Telegram bot...') 
    logging.info('Initializing Telegram bot...')   
    try:
        bot = TelegramBot()
    except Exception as e:
        logging.exception('error while creating bot object.\nQuiting', exc_info=e)
        return None
    #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Telegram Boot successfully created')
    logging.info('Telegram Boot successfully created')

    while True:
        start_time = datetime.datetime.now()
        try:
            #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Retrieving standard events...')
            logging.info('Retrieving standard events...')
            is_dict_updated = StandardNames.get_standard_events()
            if is_dict_updated:
                with open('standard_events.txt', 'w') as f:
                    f.write(StandardNames.standard_event_to_string())
                #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Standard events retrieved (exported in standard_events.txt)')
                logging.info('Standard events retrieved (exported in standard_events.txt)')
            else:
                #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Standard events already retrieved for today')
                logging.info('Standard events already retrieved for today')
            dict_events = DictEvents()
            bookmakers_dict = {'Betclic': (BetclicScraper, 'https://www.betclic.fr/football-s1'),
                            'Unibet':  (UnibetScraper, 'https://www.unibet.fr/sport/football'),
                            'ZEBet': (ZEBetScraper, 'https://www.zebet.fr/fr/sport/13-football')}
            scrapers = []
            #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Scraping bookmakers...')
            logging.info('Scraping bookmakers...')
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
            #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Done scraping bookmakers')
            logging.info('Done scraping bookmakers')

            print(StandardNames.dict_to_string(StandardNames.team_names), file=open('team_names.txt', 'w'))
            print(StandardNames.dict_to_string(StandardNames.team_ids), file=open('team_ids.txt', 'w'))

            logging.info(str(len(StandardNames.unmatched_events)) + ' unmatched events')
            if perform_manual_mapping:
                print('\nUnmatched events :')
                cpt=0
                for as_of_date, matches in StandardNames.unmatched_events.items():
                    for (team1, team2, bookmaker) in matches:
                        cpt+=1
                        print('\t' + as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2)
                print('\n' + str(len(StandardNames.unmatched_events)) + ' unmatched events : \n')
                #StandardNames.manual_mapping()
                #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Starting manual mapping...')
                logging.info('Starting manual mapping...')
                StandardNames.manual_mapping_telegram(bot)
            else:
                #print(datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S') + ' : Skipping manual mapping\n')
                logging.info('Skipping manual mapping\n')

            with open('odds_recap.txt', 'w') as f:
                f.write(dict_events.odds_to_string())
            dict_events.look_for_arbitrage(bot, stake)
        except Exception as e:
            logging.exception('exception occured', exc_info=e)
            break
        print('\n')
        time_delta = datetime.datetime.now()-start_time
        # we scrape the websites every 10mins
        if (time_delta >= refresh_time_delta):
            continue
        else:
            time.sleep(refresh_time_delta.seconds-time_delta.seconds)

    StandardNames.team_ids.close()
    StandardNames.team_names.close()

if __name__ == "__main__":
    main()