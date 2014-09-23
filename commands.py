#import urllib2,  time, re

#from BeautifulSoup import BeautifulSoup

#from string import whitespace

#from sqlstuff import SqlStuff
from sqlstuff2 import SqlStuff2
import datetime
#import os.path    
import webscrape
import time
from common import daterange
    
def makeATestcardFromResults(date):
    """ This function will make a test card from the results.  This is required as the actual
    test cards on the racingpost website are only acvailable on the day and one day in advance of
    a race"""
    print date
    ResultStuffInsts=[]       
    
    HrefStuffInst=webscrape.HrefStuff()
    """ get the hrefs that must be appended to http://www.racingpost.com/"""
    fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)

    horseName=[]       
    jockeyName=[]       
    raceLength=[]       
    weights=[]       
    goings=[]       
    draws=[]       
    todaysRaceTimes=[]       
    todaysRaceVenues=[]       

    """loop through the number of races and make a ResultStuff object for each"""
    for fullResultHref in fullResultHrefs:
        HrefStuffInst.getFullResults(fullResultHref)
        #print "got full results webpage for..."
        fullResult=HrefStuffInst.getFullResultsGrid()
        fullHeader=HrefStuffInst.getFullResultsHeader()
        ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, date)
        ResultStuffInst.getAllResultInfo()            
        ResultStuffInsts.append(ResultStuffInst)
    """loop through the ResultStuff class objects and add them to the database"""        
    for ResultStuffInst in ResultStuffInsts:
        horseName.append(ResultStuffInst.horseNames)
        jockeyName.append(ResultStuffInst.jockeys)
        raceLength.append(ResultStuffInst.raceLength)
        weights.append(ResultStuffInst.horseWeights)
        goings.append(ResultStuffInst.going)
        draws.append(ResultStuffInst.draw)
        todaysRaceTimes.append(ResultStuffInst.raceTime)
        todaysRaceVenues.append(ResultStuffInst.raceName.replace(u'\n', ''))


    return (horseName, jockeyName, raceLength, weights, goings, draws, todaysRaceTimes, todaysRaceVenues)    



def makeATestcard(date):
    """ extract the information from the days cards"""
    HrefStuffInst=webscrape.HrefStuff()
    horseName=[]
    jockeyName=[]
    raceLength=[]
    weights=[]
    goings=[]
    draws=[]
    """ get the href for the days test card"""
    todaysTestCardHref=HrefStuffInst.getTestCardHref(date)
    """ extract all of the links for the races from the days card"""
    todaysRaces, todaysRaceTimes, todaysRaceVenues=HrefStuffInst.getTodaysRaces(todaysTestCardHref)
    for todaysRace in todaysRaces:
        horse, jockey, length, weight, going, draw=HrefStuffInst.getCardContents(todaysRace)
        horseName.append(horse)
        jockeyName.append(jockey)
        raceLength.append(length)
        weights.append(weight)
        goings.append(going)
        draws.append(draw)
    return (horseName, jockeyName, raceLength, weights, goings, draws, todaysRaceTimes, todaysRaceVenues)    

        
def makeAPoliteDatabase(dateStart, dateEnd, test = "false"):
    """ the polite database is based on the original database but has the extra fields...
    raceName, raceTime
    the going variable will be corrected so that goings with several words are stored correctly.
    The webpages will be retrieved with several minutes between them so as to be polite to the
    target website"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    SqlStuffInst=SqlStuff2()        
    SqlStuffInst.createResultTable()
    """ user enters the date """
    #date=raw_input("enter the required date yyyy-mm-dd")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
        #date="2014-07-{}".format(day)
        print date
        ResultStuffInsts=[]       
        """
        for fullResultHref in fullResultHrefs:
            webpage=urllib2.urlopen(fullResultHref.get("href"))"""

        HrefStuffInst=webscrape.HrefStuff()
        """ get the hrefs that must be appended to http://www.racingpost.com/"""
        fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)

        """loop through the number of races and make a ResultStuff object for each"""
        for fullResultHref in fullResultHrefs:
            HrefStuffInst.getFullResults(fullResultHref)
            #print "got full results webpage for..."
            fullResult=HrefStuffInst.getFullResultsGrid()
            fullHeader=HrefStuffInst.getFullResultsHeader()
            ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, date)
            ResultStuffInst.getAllResultInfo()            
            """ResultStuffInst.getRaceDate()
            ResultStuffInst.getHorseNames()
            ResultStuffInst.getNumberOfHorses()
            ResultStuffInst.getRaceLength()
            ResultStuffInst.getHorseAge()
            ResultStuffInst.getHorseWeight()
            ResultStuffInst.getJockeyName()
            ResultStuffInst.getGoing()"""
            ResultStuffInsts.append(ResultStuffInst)
        """loop through the ResultStuff class objects and add them to the database"""        
        for ResultStuffInst in ResultStuffInsts:
            if test == "false":
                SqlStuffInst.addResultStuffToTable(ResultStuffInst)
            else:
                for idx, horseName in enumerate(ResultStuffInst.horseNames):
                    """create a string with this horses values"""
                    val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}, '{}', '{}', '{}'".format(\
                    ResultStuffInst.horseNames[idx].replace("'", "''"),\
                    ResultStuffInst.horseAges[idx], ResultStuffInst.horseWeights[idx], idx+1, \
                    ResultStuffInst.raceLength, ResultStuffInst.numberOfHorses, \
                    ResultStuffInst.jockeys[idx].replace("'", "''"), \
                    ResultStuffInst.going, ResultStuffInst.raceDate, ResultStuffInst.raceTime, \
                    ResultStuffInst.raceName, ResultStuffInst.draw[idx]) 
                    print val_str




def makeAResult(date):
    """ make an array of all the result infos for the day"""
    #date=time.strftime("%Y-%m-%d")
    #date="2014-07-{}".format(day)
    print date
    time.sleep(1)
    ResultStuffInsts=[]       
    """
    for fullResultHref in fullResultHrefs:
    webpage=urllib2.urlopen(fullResultHref.get("href"))"""

    HrefStuffInst=webscrape.HrefStuff()
    """ get the hrefs that must be appended to http://www.racingpost.com/"""
    fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)

    """loop through the number of races and make a ResultStuff object for each"""
    for fullResultHref in fullResultHrefs:
        HrefStuffInst.getFullResults(fullResultHref)
        #print "got full results webpage for..."
        fullResult=HrefStuffInst.getFullResultsGrid()
        fullHeader=HrefStuffInst.getFullResultsHeader()
        ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, date)
        ResultStuffInst.getAllResultInfo()            
        """ResultStuffInst.getRaceDate()
        ResultStuffInst.getHorseNames()
        ResultStuffInst.getNumberOfHorses()
        ResultStuffInst.getRaceLength()
        ResultStuffInst.getHorseAge()
        ResultStuffInst.getHorseWeight()
        ResultStuffInst.getJockeyName()
        ResultStuffInst.getGoing()"""
        ResultStuffInsts.append(ResultStuffInst)
    return ResultStuffInsts

def writeAResult(date, filenameAppend):
    """write the dates result to a file"""
    todaysResults=makeAResult(date)
    f = open(str(date)+str(filenameAppend),'a')
    original = sys.stdout
    sys.stdout = Tee(sys.stdout, f)
    for idx, ii in enumerate(todaysResults):
        print "race number " + str(idx) 
        for jdx, jj in enumerate(todaysResults[idx].horseNames):
            print str(jj)
    sys.stdout = original

def viewADatabase():
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.viewAllTable()

def viewHorse(horseName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE"
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.viewHorse(horseName)

def viewJockey(jockeyName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE"
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.viewJockey(jockeyName)

def delDate(date):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.delDate(date)

def delDateRange(dateStart, dateStop):
    dateStartSplit=dateStart.split("-")
    dateStopSplit=dateStop.split("-")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateStopSplit[0]),int(dateStopSplit[1]),int(dateStopSplit[2]))):
        print single_date
        delDate(single_date)
