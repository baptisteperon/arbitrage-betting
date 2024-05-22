# Football arbitrage betting bot

This program is designed to scrape the odds of football matches on the websites of the main french bookmakers (Betclic, Unibet, ZEBet) and find arbitrage opportunities.

If an arbitrage opportunity arises, the user is informed via an automatic message on telegram.

## Arbitrage betting explanation

An arbitrage oppotunity (or surebet) occurs when several bookmakers offer different odds for the same event.

If we consider the event Team A vs Team B, a bookmaker will offer decimal odds for the 3 possible outcomes of the match : 
- Team A wins($odds_A$), 
- draw ($odds_D$),
- Team B wins ($odds_B$).

The actual probability of the event occuring could be implied from the decimal odds of an event : $Prob_A = \displaystyle\frac{1}{odds_A}$, but bookmaker make money by taking a margin on these odds, resulting in the actual odds being lower than the fair odds.
The margin taken by the bookmaker as a percentage can be calculated as follows :
$$
margin = 100*((\displaystyle\frac{1}{odds_A} + \displaystyle\frac{1}{odds_D} + \displaystyle\frac{1}{odds_B}) - 1)
$$

Sometimes, the odds offered for the same event on different bookmakers will differ significantly. So much that the margin, when betting each outcome on the most advantageous bookmaker, will become negative. That's an arbitrage opportunity ! In that case, selecting the best odds for each outcome and betting on all of them will result in a sure profit.

For instance, if we consider the event Team A vs Team B and the decimal odds offered by 3 different bookmakers :

bookmaker/outcome  | Team A | Draw | Team B 
:--- | :---: | :---: | :---:
Bookmaker1 | 2.15 | 3.05 | 3.75
Bookmaker2 | 2.1 | 2.85 | 4
Bookmaker3 | 2.45 | 2.9  | 3.7

In that case, if we bet Team A wins on Bookmaker3, Draw on Bookmaker1 and Team B wins on Bookmaker2, we end up with a margin of $-1.40\%$ for the bookmakers. That means an edge of $1.40\%$ for us. The amount to bet on each outcome needs to be proportional to the odds :
$$
Amount\ to\ bet\ on\ A = Total\ Stake*\displaystyle\frac{\displaystyle\frac{1}{odds_A}}{\displaystyle\frac{1}{odds_A} + \displaystyle\frac{1}{odds_D} + \displaystyle\frac{1}{odds_B}}
$$

In the previous example, with a total stake of 1000€, we would have to bet :
- $1000 * \displaystyle\frac{1}{2.45}/(\displaystyle\frac{1}{2.45} + \displaystyle\frac{1}{3.05} + \displaystyle\frac{1}{4}) = 413.95€$ on Team A on boomaker3
- 332.51€ on Draw on bookmaker1
- 253.54 on Team B on bookmaker2

No matter the outcome of the match, we will win 1014.16€ ($= 413.95*2.45 = 332.51*3.05 = 253.54*4$). That's a sure profit of 14.16€ !

## Project structure

The main program scapes all supported bookmakers at the same time every *refresh_time_delta* minutes (*refresh_time_delta* is given as a parameter of the program) and stores all events with the odds associated in a dictionary of events. The dictionary is then scaned for arbitrage opportunity. If an oppotunity is detected, a Telegram message containing all the infos to place the bets is sent to the user.

Every bookmaker as it own implementation of the *scrape()* method. We use *Selenium* to extract the full html from the bookmaker's website (we have to interact with the javascript) and then *BeautifulSoup* to parse it (faster than *Selenium*).

The most difficult part of the project is the fuzzy matching of team names : a same team can have a different name in each bookmaker's referential. For instance 'Paris Saint Germain' and 'PSG' or 'Manchester United' and Man Utd' or 'Anvers' and 'Antwerp'. We need to detect that those teams are the same.

We use the website https://www.matchendirect.fr/ as a referential containing all matches as bookmakers don't offer odds on all matches. The names under which teams appear on this website is used as the baseline for team names in the program. These events are stored in a dictionary called standard_events. For every event we scan when scraping the bookmakers, we try to match it with an event from the standard_event dictionary.

Two events (teamA1 vs teamB1 and teamA2 vs teamB2) are considered the same if : 
- they occur at the same date and time,
- if teamA1 and teamA2 share at least one similar word,
- if teamB1 and teamB2 share at least one similar word.

Word similarity is checked using the Levenshtein distance (*FuzzyWuzzy* package). The matching ratio is set to 0.75.

Every team encountered (and its several name declinations) is given a unique ID and is stored in 2 dictionaries : team_names and team_ids

Some names referencing to the same team are too far appart (e.g. 'PSG' and 'Paris Saint Germain'). They need to be matched manually. If the corresponding option is set to True, the program will pause after each scraping session and ask the user to manually map the events that couldn't be mapped automatically. This is done via Telegram messages.

The team names matching part of the program is implemented in the StandardNames class.

## Getting started

Add the path to the repo in the PYTHONPATH environment variable by adding the following line to your .bashrc (or .zshrc on MacOS) :

`export PYTHONPATH=$HOME/path_to_the_repo/:$PYTHONPATH`

CD into the right folder :

`cd arbitrage-betting`

Install the latest version of chromedriver : https://developer.chrome.com/docs/chromedriver/downloads

Install the required modules : 

`pip install -r requirements.tx`

Launch the program :

`python src/main.py [-h] [-m M] [-r R] [-s s]`

    usage: main.py [-h] [-m M] [-r R] [-s s]

    options:
    -h, --help              show this help message and exit
    -m M, --manualmapping M
                            when True, the program asks the user (via Telegram messages) to manually map
                            events that couldn't be mapped automatically (default = False)
    -r R, --refresh R       time delta in minutes between each scraping session (the default behavior is one
                            every 10mins, minimum value = 1)
    -s s, --stake s         total amount to bet, distributed between the different outcomes (default value is
                            100)