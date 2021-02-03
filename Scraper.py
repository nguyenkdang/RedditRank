import praw, os, sys, csv, time
from datetime import datetime, timedelta

credentialPath = os.path.join(sys.path[0], 'credentials.txt')
with open(credentialPath) as f:
    id = f.readline().strip()
    secret = f.readline().strip()
    agent =  f.readline().strip()
    username =  f.readline().strip()
    password=  f.readline().strip()

reddit = praw.Reddit(client_id=id, \
                     client_secret=secret, \
                     user_agent=agent, \
                     username=username, \
                     password=password)

stop = {"i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", 
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", 
    "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", 
    "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", 
    "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", 
    "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", 
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "like"}
custom = {'dd', 'f', 'new', "-", 'ceo', 'im', 'ipo', 'mod', 'k', 'tv'}

class termScraper():
    def __init__(self, sub, termPath, lim=None):
        self.subreddit = sub
        self.termPath = termPath
        self.findTerms = self.buildFindTerms()
        self.postData = self.buildData(lim)   
        self.count, self.keyPost = self.buildIndex(self.postData, stop)
        self.context = self.buildContext(self.count, self.keyPost)
    
    def strToDate(self, s):
        #Try to convert a string date into a datetime type object
        #s - possible str representing datetime
        dt = s
        if type(dt) == str:
            frmt = '%m/%d/%Y'
            if '-' in dt: frmt = '%Y-%m-%d' 
            splt = dt.split(':') 
            
            if len(splt) >= 1: frmt += ' %H'
            if len(splt) >= 2: frmt += ':%M'
            if len(splt) >= 3: frmt += ':%S'    
            
            dt = datetime.strptime(dt, frmt)
    
        return dt
    
    def buildFindTerms(self, custom=[]):
        ## Build a set of tickers from a file
        # custom - set containing additional tickers
        # return - set of all tickers
        findTerms = set()
        with open(self.termPath) as f:
            for line in f:
                findTerms.add(line.split(',')[0])
    
        for t in custom:
            findTerms.add(t)
    
        return findTerms
    
    def buildData(self, lim):
        ## Build a dictionary containing all the post collected thus far. Update the original
        ## file containing all the post information with any new ones from the subreddit
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
    
        print(n)
        return postData

    def buildDateRange(self, startDate, endDate):
        ## Filter data to only be between two dates
        # data - dict {post_id:[date, title, upvote, upvote_ratio ]}
        # startDate - datetime obj
        # endDate - datetime obj
        # return - dict {post_id:[date, title, upvote, upvote_ratio ]}
        dateRange = {}
        for key, val in self.postData.items():
            if val[0] >= startDate and val[0] <= endDate: dateRange[key] = val
    
        return dateRange

    def buildIndex(self, data, stopWords):
        ## Uses a dict of posts to create an index of all words in the posts (excluding stop words) and their
        ## respective post ID. Also return a set of id's of post containing key terms. Also returns a dict
        ## containing each key terms and their respective post
        # stopWords - set of words to not index
        # return count- dict { word: set(id) )
        # return keyPost - set(id's of post w/ key terms)
        count = {}
        keyPost = set()
        for id, val in data.items():
            for w in val[1].split(' '):
                if '🚀' in w.lower() or 'moon' in w.lower():
                    keyPost.add(id) #Add id to keypost set
            
                #Add all words made of letters to count dict
                nw = "".join(c for c in w if c.isalpha())
                if nw.lower() not in stop and nw.lower() not in custom and nw != '':
                    if nw in count:
                        count[nw].add(id)
                    else:
                        count[nw] = {id}
    
        return count, keyPost
    
    def buildContext(self, count, keyPost):
        ## Take a dict of all the index word and compare each word id with a set of all the id
        ## that contains a special word. Create a dict containing all 
        # return - dict { word: set(id) )
        context = {}
        for key, val in count.items():
            for id in val:
                if id in keyPost:
                    if key in context: context[key].add(id)
                    else: context[key] = set(id)
    
        return context
    #// RANK METHODS
    def getCount(self, data, key, pData = None):
        return len(data[key])

    def getScore(self, data, key, pData):
        return sum([int(pData[p][2]) for p in data[key]])

    def getScoreDensity(self, data, key, pData):
        return self.getScore(data, key, pData)/self.getCount(data, key)

    def rankData(self, data, pData, calcFunc, title = '', top=10, otherCF=None):
        ## Rank data
        # data -
        # pData
        # calcFunc
        # title - str
        # top
        # otherCF
        # return 
        if title != '': print('\n' + title)
        rank = {}
        n = 0
        dc = data.copy()
        while n < top:
            if len(dc) == 0: break
    
            s =  max(dc, key=lambda key: calcFunc(dc,key, pData) )
            if s in self.findTerms:
                m = round(calcFunc(dc, s, pData))
                msg = "{} {}".format(s, m)
                if otherCF != None: msg += " ({})".format(otherCF(dc, s))
                if title != '': print(msg)

                n += 1
                if m != 0: rank[n] = (s, m)
    
            del dc[s]
    
        return rank
    
    def exportRank(self, rank, desc, fromDate, toDate, mode='w'):
        for key, val in rank.items():
            path = os.path.join(sys.path[0], 'Log Data/{}_{}.csv'.format(val[0],desc))
        
            '''
            if os.path.exists(path):
                with open(path, 'r') as f:
                    csvFile = csv.reader(f)
                    lastestTime = 0
                    for row in csvFile:
                        lastestTime = row[1] #flawed? - this assumes the rows are ordered
                    
                    if toDate <= datetime.strptime(lastestTime, '%Y-%m-%d %H:%M:%S'):
                        continue
            '''
        
            with open(path, mode) as f:            
                f.write('{},{},{}\n'.format(fromDate, toDate, val[1]))
        
    def exportHist(self):
        minID = min(self.postData, key=lambda key: self.postData[key][0] )
        maxID = max(self.postData, key=lambda key: self.postData[key][0] )
        minDate = self.postData[minID][0]
        toDate = self.postData[maxID][0]
        fromDate = toDate - timedelta(days=1) + timedelta(seconds=1)
        mode = 'w'
        while True:
            dateRange = self.buildDateRange(fromDate, toDate)
            count, keyPost = self.buildIndex(dateRange, stop.union(custom))
            context = self.buildContext(count, keyPost)

            topCount = self.rankData(count, dateRange, self.getCount)
            topScore = self.rankData(count, dateRange, self.getScore)
            topContxt = self.rankData(context, dateRange, self.getCount)
            #topSDensity = rankData(count, dateRange, getScoreDensity)
            
            self.exportRank(topContxt, 'Context', fromDate, toDate, mode)
            self.exportRank(topCount, 'Count', fromDate, toDate, mode)
            self.exportRank(topScore, 'Score', fromDate, toDate, mode)
            #exportRank2(topSDensity, 'SDensity', fromDate, toDate, mode)

            fromDate -= timedelta(days=1)
            toDate -= timedelta(days=1)
            mode = 'a+'
            #if toDate < minDate: break
            if fromDate < minDate: break #fromDate = minDate
    
    def exportAll(self):
        toTime = datetime.now().replace(microsecond=0)
        fromTime = datetime(2020, 1, 1, 1, 1, 1) #toTime - timedelta(days=1)
    
        dateRange = self.buildDateRange(fromTime, toTime)
        count, keyPost = self.buildIndex(dateRange, stop.union(custom))
        context = self.buildContext(count, keyPost)
        
        #Rank Data
        topCount = self.rankData(count, dateRange, self.getCount, '--- TOP COUNT ---')
        topScore = self.rankData(count, dateRange, self.getScore, '--- TOP SCORE ---')
        topSDensity = self.rankData(count, dateRange, self.getScoreDensity, '--- TOP SCORE DENSITY ---', otherCF= getCount)
        topContxt = self.rankData(context, dateRange, self.getCount, '--- TOP CONTEXT ---')
        
        #Export Ranks
        self.exportRank(topContxt, 'Context', fromTime, toTime)
        self.exportRank(topCount, 'Count', fromTime, toTime)
        self.exportRank(topScore, 'Score', fromTime, toTime)
        self.exportRank(topSDensity, 'SDensity', fromTime, toTime)


if __name__ == "__main__":
    subreddit = reddit.subreddit('wallstreetbets')
    customT = customT = {'DOGE'}
    tpath = os.path.join(sys.path[0], 'nasdaq 3000.csv')

    #s = termScraper('wallstreetbets', tpath )
    
    while True: 
        #Build Data
        writedir = os.path.join(sys.path[0], 'Log Data')
        for f in os.listdir(writedir):
            if f.endswith(".csv"): 
                os.remove(os.path.join(writedir, f))
        
        stocks = termScraper(subreddit, tpath, 500)
        stocks.exportHist()
        #exportHist()
        time.sleep(10*60)
    
        
        
