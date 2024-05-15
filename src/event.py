import datetime
import re
from standardnames import StandardNames
from unidecode import unidecode

LENGHT_THRESHOLD = 0.75 
MATCHING_PERCENTAGE_THRESHOLD = 0.75

class Event:
    """ Each event is defined by its date and the IDs of the two teams participating """
    
    def __init__(self, asOfDate, team1, team2):
        self.as_of_date = asOfDate
        self.id1 = StandardNames.team_names[team1]
        self.id2 = StandardNames.team_names[team2]

    def __str__(self):
        """ Returns a console-friendly output """
        return '***  ' + datetime.datetime.strftime(self.as_of_date, '%d/%m/%Y %H:%M') + '  ***\n' + StandardNames.team_ids[self.id1]['Standard'] + '\tvs\t' + StandardNames.team_ids[self.id2]['Standard'] + '\n'

    def __eq__(self, event):
        """ overrides equality operator to check if 2 events are equals, returns a boolean """ 
        if (self.as_of_date == event.as_of_date) and (self.id1 == event.id1) and (self.id2 == event.id2):
            return True
        elif (self.as_of_date == event.as_of_date) and (self.id1 == event.id2) and (self.id2 == event.id1):
            # if team names are inverted
            return True
        else:
            return False
        
    def __hash__(self):
        """ defines a hash operator so that an Event can be used a key in a dictionary """
        datetime_as_int = self.as_of_date.year*100000000+self.as_of_date.month*1000000+self.as_of_date.day*10000+self.as_of_date.hour*100+self.as_of_date.minute
        return hash(int(str(datetime_as_int) + str(self.id1) + str(self.id2)))
        
    def is_same(self, date_time, id1, id2):
        """ checks if 2 events are the same, returns a boolean """
        if (self.as_of_date == date_time) and (self.id1 == id1) and (self.id2 == id2):
            return True
        elif (self.as_of_date == date_time) and (self.id1 == id2) and (self.id2 == id1):
            # if team names are inverted
            return True
        else:
            return False

        
    def __eq2__(self, event):
        """ overrides equality operator to check if 2 events are equals, returns a boolean """   
        if (self.asOfDate == event.asOfDate):
            return False
        else:
            team1_A = unidecode(self.team1.lower())
            team2_A = unidecode(self.team2.lower())
            team1_B = unidecode(event.team1.lower())
            team2_B = unidecode(event.team2.lower())
            team1_A_splited = re.split(' |-|/', team1_A)
            team2_A_splited = re.split(' |-|/', team2_A)
            team1_B_splited = re.split(' |-|/', team1_B)
            team2_B_splited = re.split(' |-|/', team2_B)
            for word1 in team1_A_splited:
                for word2 in team1_B_splited:
                    if (len(word1) > 2 or len(team1_A_splited) == 1) and (len(word2) > 2 or len(team1_B_splited) == 1) and Event.__word_correspond(word1, word2):
                        for word3 in team2_A_splited:
                            for word4 in team2_B_splited:
                                if (len(word3) > 2 or len(team2_A_splited) == 1) and (len(word4) > 2 or len(team2_B_splited) == 1) and Event.__word_correspond(word3, word4):
                                    return True
            for word1 in team1_A_splited:
                for word2 in team2_B_splited:
                    if (len(word1) > 2 or len(team1_A_splited) == 1) and (len(word2) > 2 or len(team2_B_splited) == 1) and Event.__word_correspond(word1, word2):
                        for word3 in team2_A_splited:
                            for word4 in team1_B_splited:
                                if (len(word3) > 2 or len(team2_A_splited) == 1) and (len(word4) > 2 or len(team1_B_splited) == 1) and Event.__word_correspond(word3, word4):
                                    print('attention inversion equipes : ')
                                    print(self)
                                    print(event)
                                    print('\n')
                                    return True
            return False
        
    @staticmethod
    def __word_correspond(word1, word2):
        """ Evaluates if 2 words have enough in common to be considered the same. 
        For example, 'Barcelone' and 'Barcelona' or 'Londres' and 'London' are refering to the same cities but the string are not the same.

        Returns a boolean 
        """
        # word1 = longest of the two
        len1 = len(word1)
        len2 = len(word2)
        if len1<len2:
            return Event.__word_correspond(word2, word1)
        if len2 == 0:
            print(' !!!! attention min_len=0 !!!! ')
        if len2/len1 < LENGHT_THRESHOLD: # len2/len1 = min_len/max_len
            return False
        offset = 0
        cpt = 0
        # i for word2, j for word1
        i, j = 0, 0
        while i < len2:
            while j+offset < len1:
                #print(word2[i] + '-' + word1[j+offset])
                if word2[i] == word1[j+offset]:
                    cpt+=1
                    i+=1
                    j+=offset
                    break
                else:
                    offset+=1
            if j+offset == len1:
                i+=1
            else:
                j+=1
            offset = 0
        return (cpt/len2) >= MATCHING_PERCENTAGE_THRESHOLD