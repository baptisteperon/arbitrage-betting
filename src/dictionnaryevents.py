import pandas as pd
import datetime

from event import Event
from standardnames import StandardNames

class DictEvents:
    """ Dictionary containing :
        As keys : Events (date + name of the 2 teams)
        As values : dataframe containing the odds offered by the different bookmakers
                   (odds1 : odds for team 1 to win
                    oddsx : odds for a tie
                    oddds2 : odds for team 2 to win)
    """
    def __init__(self):
        self.dict = {}

    def append_event(self, as_of_date, team1, team2, bookmaker, odds1, oddsx, odds2):
        """ add the event and its odds to the dictionary containing all the events """
        event = Event(as_of_date, team1, team2)
        if not event in self.dict.keys():
            self.dict[event] = pd.DataFrame({'1': odds1, 'x': oddsx, '2': odds2}, index=[bookmaker])
        else:
            self.dict[event] = pd.concat([self.dict[event], pd.DataFrame({'1': odds1, 'x': oddsx, '2': odds2}, index=[bookmaker])], axis=0)

    def to_string(self):
        res = ""
        for event, odds in self.dict.items():
            res += str(event)
            res += odds.to_string()
            res += '\n'
        return res

    def build_dataframe_from_dico(self):
        pass

    def odds_to_string(self):
        res = ""
        for event, odds in self.dict.items():
            res += str(event)
            res += odds.to_string()
            res += '\n'
            res += 'best odds 1 : ' + str(odds['1'].max()) + ' (' + str(odds['1'].idxmax()) + ')\n'
            res += 'best odds x : ' + str(odds['x'].max()) + ' (' + str(odds['x'].idxmax()) + ')\n'
            res += 'best odds 2 : ' + str(odds['2'].max()) + ' (' + str(odds['2'].idxmax()) + ')\n'
            res += str(1/odds['1'].max() + 1/odds['x'].max() + 1/odds['2'].max())
            res += '\n\n'
        return res

    def look_for_arbitrage(self, bot, stake):
        """ Search for arbitrage opportunity in the dictionary containing all odds and send a telegram message if one is found
            For a given event, an arbitage oppotunity arises when :

                x = (1 / odds1) + (1 / oddsx) + (1 / odds2) < 1

            if that is the case, the expected profit margin is equal to :
            
                (1-x) * total investment

            The amount to bet on each outcome is :

                amount1 = total stake * (1 / odds1) / (1 / ((1 / odds1) + (1 / oddsx) + (1 / odds2))) = total stake * (margin / odds1)
        """
        for event, odds in self.dict.items():
            margin = 1/odds['1'].max() + 1/odds['x'].max() + 1/odds['2'].max()
            if (margin < 1):
                team1 = StandardNames.team_ids[event.id1],
                team2 = StandardNames.team_ids[event.id2],
                message = ""
                message += 'Found arbitrage opportunity (profit margin = ' + str((1 - margin)*100) + '%):\n'
                message += 'event = ' + datetime.datetime.strftime(event.as_of_date, '%d/%m/%Y %H:%M') + ' : ' + team1 + ' vs ' + team2 + '\n'
                message += 'Bet ' + str(stake*(margin/odds['1'].max())) + '€ on ' + team1 + ' on ' + odds['1'].idxmax() + ' (odds : ' + str(odds['1'].max()) + ')\n'
                message += 'Bet ' + str(stake*(margin/odds['x'].max())) + '€ on draw on ' + odds['x'].idxmax() + ' (odds : ' + str(odds['x'].max()) + ')\n'
                message += 'Bet ' + str(stake*(margin/odds['2'].max())) + '€ on ' + team2 + ' on ' + odds['2'].idxmax() + ' (odds : ' + str(odds['2'].max()) + ')\n'
                bot.send_message(message)