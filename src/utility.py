import os
from datetime import datetime, timedelta

def strToDate(s):
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

def clearDir(path):
    ## Delete all csv file in a directory
    # path - str of directory path
    for f in os.listdir(path):
        if f.endswith(".csv"): 
            os.remove(os.path.join(path, f))

def clearCache(path, maxDay=1):
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
                    curDate = strToDate(line.split(',')[1])
                    if curDate > fmax: fmax = curDate
                fileMax[f] = fmax
                if fmax > maxDate: maxDate = fmax
                    
    for key, val in fileMax.items():
        if maxDate-val > timedelta(days=maxDay):
            os.remove(os.path.join(path, key))