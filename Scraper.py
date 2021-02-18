import praw, os, sys, csv, time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

credentialPath = os.path.join(sys.path[0], 'credentials.txt')
with open(credentialPath) as f:
    id = f.readline().strip()
    secret = f.readline().strip()
    agent =  f.readline().strip()
    username =  f.readline().strip()
    password=  f.readline().strip()

reddit = praw.Reddit(client_id=id, client_secret=secret, user_agent=agent, username=username, password=password)

def exportGrowthPlt(width, height):
    ## Export picture graph of all data generated
    # width - int of width of export image
    # height - int of height of export image
    directory = os.path.join(sys.path[0], 'Log Data/')
    #{dataType:{ticker:[val,...],...}}
    vals = {} 
    dates = {}
    for filename in os.listdir(directory):
        if filename.endswith(".csv") == False: continue
        path = directory+filename
        fname = filename.split('.')[0]
        ticker = fname.split('_')[0]
        dt = fname.split('_')[1]
        
        if dt not in vals: vals[dt] = {}
        if dt not in dates: dates[dt] = {}
        
        with open(path, 'r') as f:
            csvFile = csv.reader(f)
            for row  in csvFile:
                if row[2].isnumeric():        
                    if ticker not in vals[dt]: vals[dt][ticker] = []
                    vals[dt][ticker].append(int(row[2]))
                        
                    if ticker not in dates[dt]: dates[dt][ticker] = []
                    dates[dt][ticker].append(datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'))
    
    plt.close('all')
    
    for key, val in vals.items():
        savePath = os.path.join(sys.path[0], 'plot_{}.png'.format(key))
        fig = plt.figure()
        ax = plt.axes()
        for k, v in val.items():
            ax.plot(dates[key][k], v, label=k)
    
        fig.add_axes(ax)
        plt.title(key)
        plt.legend()
        fig.set_size_inches(width, height)
        plt.savefig(savePath, dpi=150)

    

class termScraper():
    def __init__(self, sub, termPath, stopPath, lim=None):
        # sub - subreddit object for reddit to scrape
        # termPath - str to csv containing all the terms you want to look for
        # stopPath - str to csv containing all the terms you want to avoid
        self.subreddit = sub
        self.findTerms = self.buildTerms(termPath)
        self.stopTerms = self.buildTerms(stopPath)
        self.postData = self.buildData(lim)
        self.minID = min(self.postData, key=lambda key: self.postData[key][0] )
        self.maxID = max(self.postData, key=lambda key: self.postData[key][0] )
    
    #// UTILITY METHODS
    def strToDate(self, s):
        ## Try to convert a string date into a datetime type object
        # s - possible str to be converted to datetime
        dt = s
        if type(dt) == str:
            frmt = '%m/%d/%Y'
            if '-' in dt: frmt = '%Y-%m-%d' 
            splt = len(dt.split(':')) 
            
            if splt >= 1: frmt += ' %H'
            if splt >= 2: frmt += ':%M'
            if splt >= 3: frmt += ':%S'    
            
            dt = datetime.strptime(dt, frmt)
    
        return dt

    def clearDir(self, path):
        ## Delete all csv file in a directory
        # path - str of directory path
        for f in os.listdir(path):
            if f.endswith(".csv"): 
                os.remove(os.path.join(path, f))

    def clearCache(self, path, maxDay=1):
        ## Delete csv files that have not been updated for a certain amount of days
        # path - str of directory path
        # maxDay - int of maximum amount of days not updated until getting deleted
        maxDate = datetime.min
        fileMax = {}
        for f in os.listdir(path):
            if f.endswith(".csv"):
                fmax = datetime.min
                with open( os.path.join(path, f), 'r') as fs:
                    for line in fs:
                        curDate = self.strToDate(line.split(',')[1])
                        if curDate > fmax: fmax = curDate
                    fileMax[f] = fmax
                    if fmax > maxDate: maxDate = fmax
                    
        for key, val in fileMax.items():
            if maxDate-val > timedelta(days=maxDay):
                os.remove(os.path.join(path, key))

    #// BUILD METHODS
    def buildTerms(self, path, custom={}):
        ## Build a set of terms from a file
        # path - str of path to file to build terms around
        # custom - set containing additional terms
        # return - set of all terms
        terms = set()
        with open(path) as f:
            for line in f: terms.add(line.strip())
    
        for t in custom: terms.add(t)

        return terms
    
    def buildData(self, lim=1000):
        ## Build a dictionary containing all the post collected thus far. Update the original
        ## file containing all the post information with any new ones from the subreddit
        # lim - amount of post to get from subreddit (max 1000)
        # return - dict {post_id:[date, title, upvote, upvote_ratio ]}
        n = 0
        postData = {}
        path = os.path.join(sys.path[0], 'history.csv')

        # Open history file and add to history dict
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                csvFile = csv.reader(f)
                for row in csvFile:
                    if len(row[0]) == 0: continue
                    timeCheck = self.strToDate(row[1])
                    postData[row[0]] = [timeCheck, row[2], row[3], row[4]]
    
        # Get most recent reddit posts and update history dict 
        for post in self.subreddit.new(limit=lim):
            n+=1
            postData[post.id] = [datetime.utcfromtimestamp(post.created_utc), 
                                post.title.replace(',', '،'), post.score, post.upvote_ratio]
    
        #write file with updated dict
        with open(path, 'w', encoding='utf-8') as f:
            msg = ''
            for key, val in postData.items():
                msg += "{},{},{},{},{}\n".format(key,val[0],val[1],val[2], val[3])
        
            f.write(msg)
    
        #print('Post retrived:', n)
        return postData

    def buildDateRange(self, startDate, endDate):
        ## Filter data to only be between two dates
        # startDate - datetime obj
        # endDate - datetime obj
        # return - dict {post_id:[date, title, upvote, upvote_ratio ]}
        dateRange = {}
        for key, val in self.postData.items():
            if val[0] >= startDate and val[0] <= endDate: dateRange[key] = val
    
        return dateRange

    def buildIndex(self, postData):
        ## Uses a dict of posts to create an index of all words in the posts (excluding stop words) and their
        ## respective post ID. Also return a set of id's of post containing key terms. Also returns a dict
        ## containing each key terms and their respective post
        # postData - dict {post_id: [date, title, upvote, upvote_ratio]}
        # return count - dict { word: set(id) }
        # return keyPost - set(id's of post w/ key terms)
        count = {}
        keyPost = set()
        for id, val in postData.items():
            for w in val[1].split(' '):
                if '🚀' in w.lower() or 'moon' in w.lower():
                    keyPost.add(id) #Add id to keypost set
            
                #Add all words made of letters to count dict
                nw = "".join(c for c in w if c.isalpha())
                if nw.lower() not in self.stopTerms and nw != '':
                    if nw in count:
                        count[nw].add(id)
                    else:
                        count[nw] = {id}
    
        return count, keyPost
    
    def buildContext(self, count, keyPost):
        ## Take a dict of all the index word and compare each word id with a set of all the id
        ## that contains a special word. Create a dict containing all
        # count - dict { word: set(id) }
        # keyPost - set(id's of post w/ key terms)
        # return - dict { word: set(id) )
        context = {}
        for key, val in count.items():
            for id in val:
                if id in keyPost:
                    if key in context: context[key].add(id)
                    else: context[key] = set(id)
    
        return context
    
    #// RANK METHODS
    def getCount(self, count, key, postData = None):
        return len(count[key])

    def getScore(self, count, key, postData):
        return sum([int(postData[p][2]) for p in count[key]])

    def getScoreDensity(self, count, key, postData):
        return self.getScore(count, key, postData)/self.getCount(count, key)

    def rankData(self, count, postData, calcFunc, title = '', top=10):
        ## Rank data according to a spcific function
        # count - dict { word: set(id) }
        # postData - postData - dict {post_id: [date, title, upvote, upvote_ratio]}
        # calcFunc - func Some function to specify what is being ranked
        # title - str title of the rank. If provided, will also print rank at the end
        # top - int Maximum amount of rankings
        # return - dict {rank: (term, value)} 
        rank = {}
        n = 0
        countCopy = count.copy()
        
        while n < top:
            if len(countCopy) == 0: break
            maxTerm =  max(countCopy, key=lambda key: calcFunc(countCopy, key, postData) )
            if maxTerm in self.findTerms:
                val = round(calcFunc(countCopy, maxTerm, postData))
                if val == 0: break
                n += 1
                rank[n] = (maxTerm, val)
    
            del countCopy[maxTerm]

        #Print ranks if requested
        if title != '':
            msg = '\n' + title + '\n'
            for r in range(n):
                msg += '{}. {} {}\n'.format(r+1, rank[r+1][0], rank[r+1][1])
            print(msg)

        return rank

    def rankCount(self, count, postData, title=''):
        return self.rankData(count, postData, self.getCount, title), 'Count'
    
    def rankScore(self, count, postData, title=''):
        return self.rankData(count, postData, self.getScore, title), 'Score'

    def rankContext(self, context, postData, title=''):
        return self.rankData(context, postData, self.getCount, title), 'Context'
    
    def rankSDensity(self, count, postData, title=''):
        return self.rankData(count, postData, self.getScoreDensity, title), 'SDensity'

    def multiRanks(self, fromTime, toTime):
        dateRange = self.buildDateRange(fromTime, toTime)
        count, keyPost = self.buildIndex(dateRange)
        context = self.buildContext(count, keyPost)

        topCount = self.rankCount(count, dateRange)
        topScore = self.rankScore(count, dateRange)
        topContxt = self.rankContext(context, dateRange)
        
        return [topCount, topScore, topContxt]

    #// EXPORT METHODS
    def exportRanks(self, ranks, fromTime, toTime, mode='w'):
        ## Write rank into the correct csv file, with their times and value
        # ranks - dict {rank: (term, value)}
        # fromTime - datetime object
        # toTime - datetime object
        # mode - str indicating whether file should be overwritten or appended
        for rank in ranks:
            desc = rank[1]
            for key, val in rank[0].items():
                path = os.path.join(sys.path[0], 'Log Data/{}_{}.csv'.format(val[0],desc))
        
                with open(path, mode) as f:            
                    f.write('{},{},{}\n'.format(fromTime, toTime, val[1]))

    def exportFoward(self, cumulative=False):
        ## Export from earliest date to latest date
        # cumulative - bool on whether to accumulate ranks
        path = os.path.join(sys.path[0], 'Log Data')
        self.clearDir(path)

        maxTime = self.postData[self.maxID][0]
        fromTime = self.postData[self.minID][0] 
        toTime = fromTime + timedelta(days=1) - timedelta(seconds=1)
        mode = 'w'
        while True:
            if toTime > maxTime: toTime = maxTime
            tops = self.multiRanks(fromTime, toTime)
            self.exportRanks(tops, fromTime, toTime, mode)

            if toTime == maxTime: break
            if not cumulative: fromTime += timedelta(days=1)
            toTime += timedelta(days=1)
            mode = 'a+'

    def exportFowardSimple(self, cumulative=False):
        ## Export from earliest date, but only every 24 hours (much processing power, but can't get constant updates)
        # cumulative - bool on whether to accumulate ranks
        path = os.path.join(sys.path[0], 'Log Data')
        
        maxpath = os.path.join(path, 'maxDate.txt')
        maxTime = self.postData[self.maxID][0]
        fromTime = self.postData[self.minID][0] 
        toTime = fromTime + timedelta(days=1) - timedelta(seconds=1)
        lastDate =  datetime.min
        
        if os.path.exists(maxpath):
            with open(maxpath, 'r') as f:
                lastDate = self.strToDate(f.readline().strip())
        
        while True:
            if toTime > lastDate:
                tops = self.multiRanks(fromTime, toTime)
                self.exportRanks(tops, fromTime, toTime, 'a+')
                with open(maxpath, 'w') as f: f.write(str(toTime))

            if not cumulative: fromTime += timedelta(days=1)
            toTime += timedelta(days=1)
            if toTime > maxTime: break

    def exportBackward(self):
        ## Export from latest date to earliest date
        path = os.path.join(sys.path[0], 'Log Data')
        self.clearDir(path)
        
        minTime = self.postData[self.minID][0]
        toTime = self.postData[self.maxID][0]
        fromTime = toTime - timedelta(days=1) + timedelta(seconds=1)
        mode = 'w'
        while True:
            tops = self.multiRanks(fromTime, toTime)
            self.exportRanks(tops, fromTime, toTime, mode)

            fromTime -= timedelta(days=1)
            toTime -= timedelta(days=1)
            mode = 'a+'
            if fromTime < minTime: break 

    def exportUpTo(self):
        ## Export from up to the time of the latest date, for every day
        path = os.path.join(sys.path[0], 'Log Data')
        self.clearDir(path)
        
        minTime = self.postData[self.minID][0]
        toTime = self.postData[self.maxID][0]
        fromTime = datetime(toTime.year, toTime.month, toTime.day) 
        mode = 'w'
        while True:
            tops = self.multiRanks(fromTime, toTime)
            self.exportRanks(tops, fromTime, toTime, mode)

            fromTime -= timedelta(days=1)
            toTime -= timedelta(days=1)
            mode = 'a+'
            if fromTime < minTime: break
    
if __name__ == "__main__":
    subreddit = reddit.subreddit('wallstreetbets')
    tpath = os.path.join(sys.path[0], 'nasdaq 3000.csv')
    spath = os.path.join(sys.path[0], 'stopWords.csv')
    direct = os.path.join(sys.path[0], 'Log Data')
    
    while True: 
        stocks = termScraper(subreddit, tpath, spath, 150)
        stocks.exportFowardSimple()
        stocks.clearCache(direct, 3)
        exportGrowthPlt(15,20)
        print("Export complete at {}".format(datetime.now()), end='\r')
        time.sleep(10*60)