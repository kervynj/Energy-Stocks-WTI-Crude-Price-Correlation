import numpy as np
import matplotlib.pyplot as plt
import csv
import urllib
from datetime import date,datetime, timedelta
from scipy import signal

class historical_pricing:

    def __init__(self):
        self.m = [[0,31],[1,28],[2,31],[3,30],[4,31],[5,30],[6,31],[7,31],[8,30],[9,31],[10,30],[11,31]]

    def DateAdjustment(self,Date):

        dobj = Date
        RefWeekDay = dobj.weekday()
        RefDay = dobj.day
        RefMonth = dobj.month
        RefYear = dobj.year

        #Check if Reference week day is a business day
        if RefWeekDay > 4:
            if (RefDay + (4 - (RefWeekDay))) < 1:
                RefDay = self.m[(RefMonth-2)][1] + (RefDay + (4 - int(RefWeekDay)))
                RefMonth -= 1
            else:
                RefDay += (4 - int(RefWeekDay))

        self.Previous_Day = RefDay
        self.Previous_Year = RefYear
        self.Previous_Month = RefMonth
        self.Previous_Date_obj = date(RefYear,RefMonth,RefDay)
        return self.Previous_Date_obj

    def SixMonthDate(self,Date,key):

        SixDateobj = Date
        Year = SixDateobj.year
        Month = SixDateobj.month - key
        Day = SixDateobj.day


        try:
            SixDateobj = date(Year,Month,Day)
        except ValueError:
            if SixDateobj.month < key:
                Month = 12 + (SixDateobj.month-key)
                Year -=1
            try:
                SixDateobj = date(Year,Month,Day)
            except ValueError:
                if Day > self.m[Month-1][1]:
                    Day = self.m[Month-1][1]


        SixDateobj = self.DateAdjustment(date(Year,Month,Day))
        return SixDateobj

    def price_array(self,CurrentDate,PreviousDate,Ticker):

        yesterdate = CurrentDate - timedelta(days=1)
        yesterdate = self.DateAdjustment(yesterdate)
        CurrentYear = yesterdate.year
        CurrentMonth = yesterdate.month
        Yesterday = yesterdate.day

        BasePage = 'http://real-chart.finance.yahoo.com/table.csv?s='
        YesterdayObj = self.DateAdjustment(date(CurrentYear,CurrentMonth,Yesterday))

        #Create URL to fetch price changes
        file = BasePage + Ticker +'&d='+ str(YesterdayObj.month-1)+'&e='+str(YesterdayObj.day)+'&f='+str(YesterdayObj.year)+'&g=d&a='+str(PreviousDate.month -1)+'&b='+ str(PreviousDate.day)+ '&c=' + str(PreviousDate.year) + '&ignore=.csv'
        file_object = urllib.urlopen(file)
        pricereader = csv.DictReader(file_object)
        info = {}

        for row in pricereader:
            try:
                info[row['Date']]= [(float(row['Adj Close']))]
            except KeyError:
                pass
            try:
                day_change = 100*(float(row['Adj Close']) - float(row['Open']))/(float(row['Open']))
            except KeyError:
                continue

            info[row['Date']].append(day_change)

        return info

    def oil_fetch(self,PreviousDate):

        #yesterdate = CurrentDate - timedelta(days=1)
        #yesterdate = self.DateAdjustment(yesterdate)
        #CurrentYear = str(yesterdate.year)
        #CurrentMonth = str(yesterdate.month)
        #Yesterday = str(yesterdate.day)

        oil_file = 'https://www.quandl.com/api/v3/datasets/FRED/DCOILWTICO.csv?' + 'start_date='+ str(PreviousDate.year) +'-'+str(PreviousDate.month)+'-'+str(PreviousDate.day)
        file_object = urllib.urlopen(oil_file)
        pricereader = csv.DictReader(file_object)

        o_dict = {}

        for row in pricereader:

            try:
                o_dict[row['DATE']] = [float((row['VALUE']))]
            except ValueError:
                pass

        o_dict = self.change_array(o_dict)

        return o_dict

    def change_array(self,o_dict):

        for w in o_dict:

            y = w.split('-')
            yesterday = (date(int(y[0]),int(y[1]),int(y[2]))-timedelta(days=1))
            yesterday = str(self.DateAdjustment(yesterday))

            try:
                chng = 100*(o_dict[w][0]-o_dict[yesterday][0])/o_dict[yesterday][0]
            except KeyError:
                chng = 0
            try:
                o_dict[w].append(chng)
            except UnboundLocalError:
                pass

        return o_dict

    def date_matching(self,oil,stk):

        oil_price_match = []
        stock_price_match = []

        for entry in stk:

            try:
                change = oil[entry][1]
            except KeyError:
                pass

            oil_price_match.append(change)
            stock_price_match.append(stk[entry][1])

        return (np.array(oil_price_match),np.array(stock_price_match))


#Determine Today's Date
CurrentDate = date.today()
#Create historical pricing instance
instant = historical_pricing()
#Initialize Dicitonaries
commod_dict = {}
oil_dict = {}

adjObj = instant.DateAdjustment(CurrentDate)
sixmonth = instant.SixMonthDate(adjObj,6)

#with open('\Users\Administrator\Desktop\TrendingValue\TSX6.csv', 'rU') as c:
with open('\Users\Administrator\Documents\Stock Analysis\energy_constituents.csv', 'r') as c:
    reader =csv.DictReader(c)
    for row in reader:
        dict = instant.price_array(adjObj,sixmonth,row[' ticker']) # ' ticker'
        commod_dict[row[' ticker']] = dict # ' ticker'

oil_dict = instant.oil_fetch(sixmonth)

for i, company in enumerate(commod_dict):

    print company

    (oil_y,stock_y) = instant.date_matching(oil_dict,commod_dict[company])

    try:
        xcorr = signal.correlate(oil_y,stock_y)
    except ValueError:
        continue

    delay = np.argmax(xcorr) - (len(oil_y) -1)

    f, (ax1,ax2) = plt.subplots(2)
    ax1.plot(np.arange(0,np.size(oil_y),1),oil_y, 'g')
    ax1.plot(np.arange(0,np.size(stock_y),1),stock_y, 'b')
    ax2.scatter(oil_y,stock_y)
    plt.figtext(0.3,0.02,'Cross Correlation Delay = %s days'%(delay))
    ax1.set_title('WTI Daily vs %s'%(company))
    plt.show()


