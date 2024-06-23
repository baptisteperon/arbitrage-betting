from sqlitedict import SqliteDict
from bs4 import BeautifulSoup
from unidecode import unidecode
from fuzzywuzzy import fuzz

import datetime
import requests
import re
import os
import asyncio
import logging


class StandardNames:
    """ Static class used to link each team with its unique ID.
        Names like 'Paris Saint Germain' and 'PSG' identify the same team, both names need to correspond to the same ID.

        The mapping is stored in a persistent dictionary using SqliteDict (https://github.com/RaRe-Technologies/sqlitedict/tree/master)
        
        team_names : dictionary with teams names as keys and IDs as values
                     e.g. : {'PSG': 12345, 'Manchester United': 5678, 'Paris Saint Germain': 12345, 'Man. U.': 5678}
        
        team_ids : still a mapping between teams names and IDs but this time the keys are the IDs and the values are dictionaries
                   containing the name of the team on each bookmaker's referential
                   e.g. : {12345: {'Standard': 'Paris Saint Germain', 'Betclic': 'Paris Saint Germain', 'Unibet': 'PSG'}}

        next_id : keeps track of the next ID to create when encountering a new team name

        standard_events : dictionary containing every upcoming event 

        unmatched_events : dictionary of events that could not be mapped to an event in the standard_events dictionary
                        this appends when fuzzy names matching does not work (with 'Paris Saint Germain' and 'PSG' or 'Anvers' and 'Antwerpen')
                        the mapping needs to be done manually
                        keys : datetime of events
                        values : tuple containing the two teams and the name of the bookmaker that mentiones those teams (or list of tuples if several events with the same date are unmatched)
    """

    team_names = SqliteDict("TeamNames.sqlite", tablename="team_Names", autocommit=True)
    team_ids = SqliteDict("TeamNames.sqlite", tablename="team_IDs", autocommit=True)
    standard_events = SqliteDict("TeamNames.sqlite", tablename="standard_Events", autocommit=True)
    next_id = len(team_ids)
    unmatched_events = {}

    @staticmethod
    def get_standard_events():
        """ fill a dictionary containing all the upcoming events
            team names in this dictionary are considered baseline data for fuzzy team names matching
            data comes from the website www.matchendirect.fr which gathers all the upcomming football matches in the world for the next 14 days
            returns True if we updated the standard_events dictionary (only once a day), False otherwise
        """
        file_name = 'TeamNames.sqlite'
        headers = {'User-Agent': 'Mozilla/5.0'} # to fix 403 Forbidden response when getting url
        if (datetime.date.today() != datetime.date.fromtimestamp(os.path.getmtime(file_name))) or (len(StandardNames.standard_events) == 0):
            """ we only refill standard_events dictionary if it is the first run of the day 
                (i.e if the sqlite dictionary has not been modified today) 
                or if its is empty (first run of the program)
            """
            StandardNames.standard_events.clear()
            today = datetime.datetime.today()
            for i in range(15):
                event_date = today + datetime.timedelta(i)
                url = 'https://www.matchendirect.fr/resultat-foot-' + event_date.strftime('%d-%m-%Y') + '/'
                response = requests.get(url, headers=headers)
                html = BeautifulSoup(response.content, 'html.parser')
                competitions = html.findAll('div', {'class': 'homeMatchPanel'})
                for competition in competitions:
                    competition_name = competition.find('h3', {'class': 'panel-title'}).text
                    events = competition.findAll('tr')
                    for event in events:
                        event_time = event.findAll('td')[0].text.strip()
                        if (':' in event_time) and (not '--' in event_time):
                            hour, minute = event_time.split(':')
                            event_date_time = event_date.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
                            team1 = event.findAll('td')[1].find('span', {'class': 'lm3_eq1'}).text.strip()
                            team2 = event.findAll('td')[1].find('span', {'class': 'lm3_eq2'}).text.strip()
                            team1 = unidecode(team1.lower())
                            team2 = unidecode(team2.lower())
                            if  (    ('Women' in competition_name) or ('women' in competition_name) 
                                or ('Féminine' in competition_name) or ('féminine' in competition_name) 
                                or ('Feminin' in competition_name) or ('feminin' in competition_name)
                                or ('Dames' in competition_name) or ('dames' in competition_name) ):
                                team1 = team1 + ' women'
                                team2 = team2 + ' women'
                            if 'U23' in competition_name:
                                team1 = team1 + ' U23'
                                team2 = team2 + ' U23'
                            if 'U22' in competition_name:
                                team1 = team1 + ' U22'
                                team2 = team2 + ' U22'
                            if 'U21' in competition_name:
                                team1 = team1 + ' U21'
                                team2 = team2 + ' U21'
                            if 'U20' in competition_name:
                                team1 = team1 + ' U20'
                                team2 = team2 + ' U20'
                            if 'U19' in competition_name:
                                team1 = team1 + ' U19'
                                team2 = team2 + ' U19'
                            if 'U18' in competition_name:
                                team1 = team1 + ' U18'
                                team2 = team2 + ' U18'
                            if 'U17' in competition_name:
                                team1 = team1 + ' U17'
                                team2 = team2 + ' U17'
                            if 'U16' in competition_name:
                                team1 = team1 + ' U16'
                                team2 = team2 + ' U16'
                            if 'U15' in competition_name:
                                team1 = team1 + ' U15'
                                team2 = team2 + ' U15'
                            if event_date_time in StandardNames.standard_events:
                                tmp_dict = StandardNames.standard_events[event_date_time] # using a temporary variable to store the dictionary because SqliteDict cannot know when the persitent dictionary is modified in RAM (see https://github.com/RaRe-Technologies/sqlitedict/tree/master#more)
                                tmp_dict.append((team1, team2))
                                StandardNames.standard_events[event_date_time] = tmp_dict
                            else:
                                StandardNames.standard_events[event_date_time] = [(team1, team2)]
            return True
        else:
            return False

    @staticmethod
    def dict_to_string(dict):
        res = ''
        for key, val in dict.items():
            res += (str(key) + ' : ' + str(val) + '\n')
        return res

    @staticmethod
    def standard_event_to_string():
        res = ''
        count = 0
        for event_date_time, events in StandardNames.standard_events.items():
            for event in events:
                count+=1
                res += (event_date_time + ' : ' + event[0] + ' * ' + event[1] + '\n')
        res += ('\n' + str(count) + ' events in dict')
        return res

    @staticmethod
    def update_mapping(team_name, standard_team_name, bookmaker, id):
        if not standard_team_name in StandardNames.team_names:
            StandardNames.team_names[standard_team_name] = id
            StandardNames.team_ids[id] = {'Standard': standard_team_name}
        if not team_name in StandardNames.team_names:
            StandardNames.team_names[team_name] = id
        if not bookmaker in StandardNames.team_ids[id]:
            tmp_dict = StandardNames.team_ids[id] # using a temporary variable to store the dictionary because SqliteDict cannot know when the persitent dictionary is modified in RAM (see https://github.com/RaRe-Technologies/sqlitedict/tree/master#more)
            tmp_dict[bookmaker] = team_name
            StandardNames.team_ids[id] = tmp_dict


    @staticmethod
    def assign_ids(event_date_time, team1, team2, bookmaker):
        """ assign an ID to both teams by comparing the event with the standard events in standard_events dictionary
            returns a tuple containing the IDs of the 2 teams
        """
        if (team1 in StandardNames.team_names) and (team2 in StandardNames.team_names):
            # in this case, both teams names have already been encountered and their IDs are already in the database
            id1 = StandardNames.team_names[team1]
            id2 = StandardNames.team_names[team2]
            standard_team1 = StandardNames.team_ids[id1]['Standard']
            standard_team2 = StandardNames.team_ids[id2]['Standard']
            StandardNames.update_mapping(team1, standard_team1, bookmaker, id1) # we still need to update mapping in case..
            StandardNames.update_mapping(team2, standard_team2, bookmaker, id2) # ..the bookmaker has not been encountered yet
            return (id1, id2)
        
        if event_date_time in StandardNames.standard_events:  
            # one or both theams have not been encountered
            if (team1 in StandardNames.team_names) and (not team2 in StandardNames.team_names):
                team1 = StandardNames.team_ids[StandardNames.team_names[team1]]['Standard']
            if (team2 in StandardNames.team_names) and (not team1 in StandardNames.team_names):
                team2 = StandardNames.team_ids[StandardNames.team_names[team2]]['Standard']
            for standard_event in StandardNames.standard_events[event_date_time]:
                if StandardNames.is_same_event(team1, team2, standard_event[0], standard_event[1]):
                    if standard_event[0] in StandardNames.team_names:
                        id1 = StandardNames.team_names[standard_event[0]]
                    else:
                        id1 = StandardNames.next_id
                        StandardNames.next_id += 1
                    if standard_event[1] in StandardNames.team_names:
                        id2 = StandardNames.team_names[standard_event[1]]
                    else:
                        id2 = StandardNames.next_id
                        StandardNames.next_id += 1
                    StandardNames.update_mapping(team1, standard_event[0], bookmaker, id1)
                    StandardNames.update_mapping(team2, standard_event[1], bookmaker, id2)
                    return (id1, id2)
                elif StandardNames.is_same_event(team1, team2, standard_event[1], standard_event[0]): # in case names are inverted
                    if standard_event[1] in StandardNames.team_names:
                        id1 = StandardNames.team_names[standard_event[1]]
                    else:
                        id1 = StandardNames.next_id
                        StandardNames.next_id += 1
                    if standard_event[0] in StandardNames.team_names:
                        id2 = StandardNames.team_names[standard_event[0]]
                    else:
                        id2 = StandardNames.next_id
                        StandardNames.next_id += 1
                    StandardNames.update_mapping(team1, standard_event[1], bookmaker, id1)
                    StandardNames.update_mapping(team2, standard_event[0], bookmaker, id2)
                    return (id1, id2)
            #raise ValueError('Unable to find the event (' + eventDateTime.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + ') in standardEvents dictionary')
            # events with no match in the dictionary of standard events are saved to be checked at the end of the program
            if event_date_time in StandardNames.unmatched_events:
                StandardNames.unmatched_events[event_date_time].append((team1, team2, bookmaker))
            else:
                StandardNames.unmatched_events[event_date_time] = [(team1, team2, bookmaker)]
            return None
        
        # if the event is not present in standardEvents
        logging.info('No event at this time (' + event_date_time.strftime('%d-%m-%Y %H:%M') + ') in standardEvents dictionary\ncould not assign id to event : ' + team1 + ' vs ' + team2)
        return None


    @staticmethod
    def is_same_event(eventA_team1, eventA_team2, eventB_team1, eventB_team2):
        """ We consider that eventA and eventB are equals if : 
                - eventA_team1 and eventB_team1 share one similar word other than 'fc', 'sc' and 'club'
                - eventA_team2 and eventB_team2 share one similar word other than 'fc', 'sc' and 'club'
            Word similarity is computed using Levenshtein distance (https://pypi.org/project/fuzzywuzzy/)
        """
        eventA_team1_splited = re.split(' |-|/', unidecode(eventA_team1.lower()))
        eventA_team2_splited = re.split(' |-|/', unidecode(eventA_team2.lower()))
        eventB_team1_splited = re.split(' |-|/', unidecode(eventB_team1.lower()))
        eventB_team2_splited = re.split(' |-|/', unidecode(eventB_team2.lower()))
        for word1 in eventA_team1_splited:
            for word2 in eventB_team1_splited:
                if ((word1 != 'fc') and (word2 != 'fc')
                    and (word1 != 'sc') and (word2 != 'sc')
                    and (word1 != 'club') and (word2 != 'club')):
                    #print(word1 + ' - ' + word2 + ' : ratio = ' + str(fuzz.ratio(word1, word2)))
                    if (fuzz.ratio(word1, word2) > 75):
                        for word3 in eventA_team2_splited:
                            for word4 in eventB_team2_splited:
                                #print(word3 + ' - ' + word4 + ' : ratio = ' + str(fuzz.ratio(word3, word4)))
                                if (fuzz.ratio(word3, word4) > 75):
                                    return True
        return False
    
    @staticmethod
    def manual_mapping():
        """ Manually mapping event with no matching found (user inputs needed) 
            Done in command line interface
            no timeout here
        """
        for as_of_date, teams_list in StandardNames.unmatched_events.items():
            for teams in teams_list:
                bookmaker = teams[2]
                print('\nNo matching found for event : ')
                print(as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + str(teams[0]) + ' vs ' + str(teams[1]))
                print('Standard events occuring at the same time : ')
                i = 1
                tmp_dict = {}
                for team1, team2 in StandardNames.standard_events[as_of_date]:
                    print('\t' + str(i) + ') ' + as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2)
                    tmp_dict[i] = (team1, team2)
                    i=i+1
                choice = input('Select the number corresponding to the matching event (0 if none) : ')
                if int(choice) != 0:
                    std_team1 = tmp_dict[int(choice)][0]
                    std_team2 = tmp_dict[int(choice)][1]
                    if (std_team1 in StandardNames.team_names) and (std_team2 in StandardNames.team_names):
                        id1 = StandardNames.team_names[std_team1]
                        id2 = StandardNames.team_names[std_team2]
                    else:
                        if std_team1 in StandardNames.team_names:
                            id1 = StandardNames.team_names[std_team1]
                        else:
                            id1 = StandardNames.next_id
                            StandardNames.next_id += 1
                        if std_team2 in StandardNames.team_names:
                            id2 = StandardNames.team_names[std_team2]
                        else:
                            id2 = StandardNames.next_id
                            StandardNames.next_id += 1
                    StandardNames.update_mapping(teams[0], std_team1, bookmaker, id1)
                    StandardNames.update_mapping(teams[1], std_team2, bookmaker, id2)
                else:
                    print('0 : no match found in this list, skipping this event\n')

    @staticmethod
    def manual_mapping_telegram(bot):
        """ Manually mapping event with no matching found (user inputs needed)
            Done via Telegram messages    
            timeout if the user doesn't respond fast enough (defined in TelegramBot class)
        """
        for as_of_date, teams_list in StandardNames.unmatched_events.items():
            for teams in teams_list:
                bookmaker = teams[2]
                msg = 'No matching found for event :\n'
                msg += as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + str(teams[0]) + ' vs ' + str(teams[1]) + '\n\n'
                msg += 'Standard events occuring at the same time :\n'
                i = 1
                tmp_dict = {}
                for team1, team2 in StandardNames.standard_events[as_of_date]:
                    msg += str(i) + ') ' + as_of_date.strftime('%d-%m-%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + '\n'
                    tmp_dict[i] = (team1, team2)
                    i=i+1
                msg += '\nSelect the number corresponding to the matching event (0 if none, anything else to skip mapping) : '
                asyncio.run(bot.send_message(msg))
                try:
                    choice = asyncio.run(bot.get_response())
                except:
                    return print('Skipping manual mapping') # skipping manual mapping if response is unexpected
                if not choice.isdigit():
                    bot.send_message('Unrecognized user input : skipping manual mapping')
                    return print('Unrecognized user input : skipping manual mapping')
                elif int(choice) != 0:
                    std_team1 = tmp_dict[int(choice)][0]
                    std_team2 = tmp_dict[int(choice)][1]
                    if (std_team1 in StandardNames.team_names) and (std_team2 in StandardNames.team_names):
                        id1 = StandardNames.team_names[std_team1]
                        id2 = StandardNames.team_names[std_team2]
                    else:
                        if std_team1 in StandardNames.team_names:
                            id1 = StandardNames.team_names[std_team1]
                        else:
                            id1 = StandardNames.next_id
                            StandardNames.next_id += 1
                        if std_team2 in StandardNames.team_names:
                            id2 = StandardNames.team_names[std_team2]
                        else:
                            id2 = StandardNames.next_id
                            StandardNames.next_id += 1
                    StandardNames.update_mapping(teams[0], std_team1, bookmaker, id1)
                    StandardNames.update_mapping(teams[1], std_team2, bookmaker, id2)
                else:
                    bot.send_message('0 : no match found in this list, skipping this event\n')