# arbitrage-betting

This program is designed to scrape the odds of football matches on the websites of the main french bookmakers (betclic, unibet) and find arbitrage opportunities.

If an arbitrage opportunity arises, the user is informed via an automatic message on telegram.

Add the path to the repo in the PYTHONPATH environment variable by adding the following line to your .bashrc (or .zshrc on MacOS) :

export PYTHONPATH=$HOME/path_to_the_repo/:$PYTHONPATH