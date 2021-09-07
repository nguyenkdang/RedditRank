import matplotlib.pyplot as plt
from datetime import datetime
import os, sys, csv

def exportGrowthPlt(width, height):
    ## Export picture graph of all data generated
    # width - int of width of export image
    # height - int of height of export image
    directory = os.path.join(sys.path[0], '../Log_data/')
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
        savePath = os.path.join(sys.path[0], '../Plot_result/plot_{}.png'.format(key))
        fig = plt.figure()
        ax = plt.axes()
        for k, v in val.items():
            ax.plot(dates[key][k], v, label=k)
    
        fig.add_axes(ax)
        plt.title(key)
        plt.legend()
        fig.set_size_inches(width, height)
        plt.savefig(savePath, dpi=150)