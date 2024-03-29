import os, sys, csv
from datetime import datetime, timedelta
from utility import strToDate, clearDir

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
                    timeCheck = strToDate(row[1])
                    postData[row[0]] = [timeCheck, row[2], row[3], row[4]]
    
        # Get most recent reddit posts and update history dict 
        for post in self.subreddit.new(limit=lim):
            n+=1
            postData[post.id] = [datetime.utcfromtimestamp(post.created_utc), post.title.replace(',', '،'), post.score, post.upvote_ratio]
    
        #write file with updated dict
        with open(path, 'w', encoding='utf-8') as f:
            msg = ''
            for key, val in postData.items():
                msg += "{},{},{},{},{}\n".format(key,val[0],val[1],val[2], val[3])
        
            f.write(msg)
    
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
        ## Uses a dict of posts to create an index of all words in the posts (excluding stop words) and their respective post ID. Also return a set of id's of post containing key terms. Also returns a dict containing each key terms and their respective post
        # postData - dict {post_id: [date, title, upvote, upvote_ratio]}
        # return count - dict { word: set(id) }
        # return keyPost - set(id's of post w/ key terms)
        count = {}
        keyPost = set()
        for id, val in postData.items():
            for w in val[1].split(' '):
                #if '🚀' in w.lower() or 'moon' in w.lower():
                #    keyPost.add(id) #Add id to keypost set
            
                #Add all words made of letters to count dict
                nw = "".join(c for c in w if c.isalpha())
                if nw.lower() not in self.stopTerms and nw != '':
                    if nw in count: count[nw].add(id)
                    else: count[nw] = {id}
    
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
        ## get count of posts with a certain word
        return len(count[key])

    def getScore(self, count, key, postData):
        ## get sum of scores from posts with a certain word

        return sum([int(postData[p][2]) for p in count[key]])

    def getScoreDensity(self, count, key, postData):
        ## get average score from posts with a certain word
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
        # rank words with the highest post count
        return self.rankData(count, postData, self.getCount, title), 'Count'
    
    def rankScore(self, count, postData, title=''):
        # rank words with the highest sum post score
        return self.rankData(count, postData, self.getScore, title), 'Score'

    def rankContext(self, context, postData, title=''):
        # rank *relevant* words with the highest post count
        return self.rankData(context, postData, self.getCount, title), 'Context'
    
    def rankSDensity(self, count, postData, title=''):
        # rank words with the highest average post score
        return self.rankData(count, postData, self.getScoreDensity, title), 'SDensity'

    def multiRanks(self, fromTime, toTime):
        # rank words count, sum score, and *relevant* count
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
        for r in ranks:
            desc = r[1]
            for key, val in r[0].items():
                path = os.path.join(sys.path[0], '../Log_data/{}_{}.csv'.format(val[0],desc))

                with open(path, mode) as f:            
                    f.write('{},{},{}\n'.format(fromTime, toTime, val[1]))

    def exportFoward(self, cumulative=False):
        ## Export from earliest date to latest date
        # cumulative - bool on whether to accumulate ranks
        path = os.path.join(sys.path[0], '../Log_data')
        clearDir(path)

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
        path = os.path.join(sys.path[0], '../Log_data')
        
        maxpath = os.path.join(path, 'maxDate.txt')
        maxTime = self.postData[self.maxID][0]
        fromTime = self.postData[self.minID][0] 
        toTime = fromTime + timedelta(days=1) - timedelta(seconds=1)
        lastDate =  datetime.min
        
        if os.path.exists(maxpath):
            with open(maxpath, 'r') as f:
                lastDate = strToDate(f.readline().strip())
        
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
        path = os.path.join(sys.path[0], '../Log_data')
        clearDir(path)
        
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
        path = os.path.join(sys.path[0], '../Log_data')
        clearDir(path)
        
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