import praw, os, sys, time
from datetime import datetime
from utility import clearCache
from plotData import exportGrowthPlt
from termscraper import termScraper

credentialPath = os.path.join(sys.path[0], 'input_file/credentials')
with open(credentialPath) as f:
    id, secret, agent, username, password = f.read().splitlines() 
reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent, username=username, password=password)

if __name__ == "__main__":
    subreddit = reddit.subreddit('wallstreetbets')
    tpath = os.path.join(sys.path[0], 'input_file/findWords.csv')
    spath = os.path.join(sys.path[0], 'input_file/stopWords.csv')
    output = os.path.join(sys.path[0], '../Log_data')
    
    while True: 
        stocks = termScraper(subreddit, tpath, spath, 350)
        stocks.exportFowardSimple()
        clearCache(output, 3)
        exportGrowthPlt(15,20)
        print("Export complete at {}".format(datetime.now()), end='\r')
        time.sleep(10*60)
