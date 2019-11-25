#import urllib2,  time, re

#from BeautifulSoup import BeautifulSoup

#from string import whitespace

#from sqlstuff import SqlStuff
from sqlstuff2 import SqlStuff2
import datetime
#import os.path
import os
import pickle
import webscrape
import webscrape_legacy
import webscrape_legacy2
import time
from common import daterange
from minmax import convertRaceLengthMetres
from minmax import convertWeightKilos

def tryLegacy(date):
    """try the legacy result format and if it fails try the current. 
    Return the HrefStuffInst"""
    # check if the legacy webscrape file exists
    try:        
        HrefStuffInst_legacy=webscrape_legacy.HrefStuff_legacy()
        """ get the hrefs that must be appended to http://www.racingpost.com/"""
        fullResultHrefs_legacy=HrefStuffInst_legacy.getFullResultHrefs(date)
        return (HrefStuffInst_legacy, fullResultHrefs_legacy, 1)
    except Exception, e:
        print e;
        pass

    try:        
        HrefStuffInst_legacy2=webscrape_legacy2.HrefStuff_legacy2()
        """ get the hrefs that must be appended to http://www.racingpost.com/"""
        fullResultHrefs_legacy2=HrefStuffInst_legacy2.getFullResultHrefs(date)
        return (HrefStuffInst_legacy2, fullResultHrefs_legacy2, 2)
    except Exception, e:
        print "webscrape_legacy2.getFullResultHrefs failed to find legacy results"
        #print e;
        pass

    try:        
        HrefStuffInst=webscrape.HrefStuff()
        """ get the hrefs that must be appended to http://www.racingpost.com/"""
        fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)
        return (HrefStuffInst, fullResultHrefs, 0)
    except Exception, e:
        print e
        raise Exception("problem getting href in any format")

    
def makeATestcardFromResults(date):
    """ This function will make a test card from the results.  This is required as the actual
    test cards on the racingpost website are only acvailable on the day and one day in advance of
    a race"""
    print date
    ResultStuffInsts=[]

    testCardResultsFilename = "./resultsFiles/testCardResults" + str(date) + ".sv"
    if os.path.exists(testCardResultsFilename):
        try:
            print "reading ResultStuffInsts from file %s " % (testCardResultsFilename)
            with open (testCardResultsFilename, 'rb') as fp:
                ResultStuffInsts= pickle.load(fp)
                horseName=[]       
                jockeyName=[]       
                trainerName=[]
                raceLength=[]       
                weights=[]       
                goings=[]       
                draws=[]       
                todaysRaceTimes=[]       
                todaysRaceVenues=[]     
                odds=[]
        except Exception, e:
            print "problem loading the ResultStuffInsts from file"
            print str(e)
    else:

        try:
            HrefStuffInst, fullResultHrefs, legacy = tryLegacy(date)
        except Exception, e:
            print e

        print "legacy is " + str(legacy)
        horseName=[]       
        jockeyName=[]       
        trainerName=[]
        raceLength=[]       
        weights=[]       
        goings=[]       
        draws=[]       
        todaysRaceTimes=[]       
        todaysRaceVenues=[]     
        odds=[]

        """loop through the number of races and make a ResultStuff object for each"""
        for fullResultHref in fullResultHrefs:
            if not fullResultHref:
                print "skipping abandoned race"
                continue
            try:
                HrefStuffInst.getFullResults(fullResultHref)
            except Exception, e:
                print e
                print "makeATestcardFromResults: skipping this result"
            #print "got full results webpage for..."
            fullResult=HrefStuffInst.getFullResultsGrid()
            fullHeader=HrefStuffInst.getFullResultsHeader()
            fullInfo=HrefStuffInst.getFullRaceInfo()
            if legacy == 1:
                ResultStuffInst=webscrape_legacy.ResultStuff(fullResult, fullHeader, fullInfo, date)
            elif legacy == 2:
                ResultStuffInst=webscrape_legacy2.ResultStuff(fullResult, fullHeader, fullInfo, date)
            else:
                ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, fullInfo, date)
            ResultStuffInst.getAllResultInfo()            
            ResultStuffObjInst = webscrape.ResultStuffObj()

            ResultStuffObjInst.horseNames= ResultStuffInst.horseNames
            ResultStuffObjInst.jockeys= ResultStuffInst.jockeys
            ResultStuffObjInst.trainers= ResultStuffInst.trainers
            ResultStuffObjInst.raceLength = ResultStuffInst.raceLength
            ResultStuffObjInst.horseWeights= ResultStuffInst.horseWeights
            ResultStuffObjInst.going = ResultStuffInst.going
            ResultStuffObjInst.draw= ResultStuffInst.draw
            ResultStuffObjInst.raceTime = ResultStuffInst.raceTime
            ResultStuffObjInst.raceName = ResultStuffInst.raceName
            ResultStuffObjInst.odds= ResultStuffInst.odds

            ResultStuffInsts.append(ResultStuffObjInst)
    
        try:
            with open(testCardResultsFilename, 'wb') as fp:
                pickle.dump(ResultStuffInsts, fp)
        except Exception,e:
            print "problem dumping ResultStuffInsts to file"
            print str(e)
    """loop through the ResultStuff class objects and add them to the database"""        
    for ResultStuffInst in ResultStuffInsts:
        horseName.append(ResultStuffInst.horseNames)
        jockeyName.append(ResultStuffInst.jockeys)
        trainerName.append(ResultStuffInst.trainers)
        raceLength.append(ResultStuffInst.raceLength)
        weights.append(ResultStuffInst.horseWeights)
        goings.append(ResultStuffInst.going)
        draws.append(ResultStuffInst.draw)
        todaysRaceTimes.append(ResultStuffInst.raceTime)
        todaysRaceVenues.append(ResultStuffInst.raceName.replace(u'\n', ''))
        odds.append(ResultStuffInst.odds)

    return (horseName, jockeyName, raceLength, weights, goings, draws, trainerName, todaysRaceTimes, todaysRaceVenues, odds)    



def makeATestcard(date):
    """ extract the information from the days cards"""
    HrefStuffInst=webscrape.HrefStuff()
    horseName=[]
    jockeyName=[]
    raceLength=[]
    weights=[]
    goings=[]
    draws=[]
    trainers=[]
    odds=[]
    """ get the href for the days test card"""
    todaysTestCardHref=HrefStuffInst.getTestCardHref(date)
    """ extract all of the links for the races from the days card"""

    print "got the test card name"
    todaysRaces, todaysRaceTimes, todaysRaceVenues=HrefStuffInst.getTodaysRaces(todaysTestCardHref)
    
    print "scraped the test card"

    raceToRemove=[]
    for ii, todaysRace in enumerate(todaysRaces):
        print "gonna to the race " + str(todaysRace)
        try:
            horse, jockey, length, weight, going, draw, trainer, odd=HrefStuffInst.getCardContents(todaysRace)
        except Exception, e:
            print str(e)
            print "There was an error with the race " + str(todaysRace)
            print "This was " + str(todaysRaceVenues[ii]) + " at " + str(todaysRaceTimes[ii])
            raceToRemove.append(ii)
            continue
            raise Exception(e);
        print "did the race " + str(todaysRace)
        horseName.append(horse)
        jockeyName.append(jockey)
        raceLength.append(length)
        weights.append(weight)
        goings.append(going)
        draws.append(draw)
        trainers.append(trainer)
        odds.append(odd)
    for ii in reversed(raceToRemove):
        del todaysRaceVenues[ii]
        del todaysRaceTimes[ii]
        del todaysRaces[ii]

    return (horseName, jockeyName, raceLength, weights, goings, draws, trainers, odds, todaysRaceTimes, todaysRaceVenues)    





def makeAPoliteDatabase(dateStart, dateEnd, databaseName, test = "false"):
    """ the polite database is based on the original database but has the extra fields...
    raceName, raceTime
    the going variable will be corrected so that goings with several words are stored correctly.
    The webpages will be retrieved with several minutes between them so as to be polite to the
    target website"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)        
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
        try:
            HrefStuffInst, fullResultHrefs, legacy = tryLegacy(date)
        except Exception, e:
            print e
            
        """loop through the number of races and make a ResultStuff object for each"""
        for fullResultHref in fullResultHrefs:
            if not fullResultHref:
                print "skipping abandoned race"
                continue
            try:
                HrefStuffInst.getFullResults(fullResultHref)
            except Exception, e:
                print e
                print "makeAPoliteDatabase: skipping this result"
            #print "got full results webpage for..."
            fullResult=HrefStuffInst.getFullResultsGrid()
            fullHeader=HrefStuffInst.getFullResultsHeader()
            fullInfo=HrefStuffInst.getFullRaceInfo()
            if legacy == 1:
                ResultStuffInst=webscrape_legacy.ResultStuff(fullResult, fullHeader, fullInfo, date)
            elif legacy == 2:
                ResultStuffInst=webscrape_legacy2.ResultStuff(fullResult, fullHeader, fullInfo, date)
            else:
                ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, fullInfo, date)
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
                try:
                    SqlStuffInst.addResultStuffToTable(ResultStuffInst)
                except Exception, e:
                    print "could not add to database"
                    print str(ResultStuffInst)
                    print str(e)
            else:
                for idx, horseName in enumerate(ResultStuffInst.horseNames):
                    """create a string with this horses values"""
                    val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}, '{}', '{}', '{}', '{}', '{}', '{}'".format(\
                    ResultStuffInst.horseNames[idx].replace("'", "''"),\
                    ResultStuffInst.horseAges[idx], ResultStuffInst.horseWeights[idx], idx+1, \
                    ResultStuffInst.raceLength, ResultStuffInst.numberOfHorses, \
                    ResultStuffInst.jockeys[idx].replace("'", "''"), \
                    ResultStuffInst.going, ResultStuffInst.raceDate, ResultStuffInst.raceTime, \
                    ResultStuffInst.raceName, ResultStuffInst.draw[idx], \
                    ResultStuffInst.trainers[idx].replace("'", "''"), \
                    ResultStuffInst.finishingTime, \
                    ResultStuffInst.odds[idx]
                    )
                    print val_str

def makeAPoliteFileStash(dateStart, dateEnd, test = "false"):
    """ the polite filestash is just to get files that may be needed sometime, without
    adding them to the database"""

    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    
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
        try:
            fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)
        except Exception, e:
            print e
        """loop through the number of races and make a ResultStuff object for each"""
        for fullResultHref in fullResultHrefs:
            if not fullResultHref:
                print "skipping abandoned race"
                continue
            try:
                HrefStuffInst.getFullResults(fullResultHref)
            except Exception, e:
                print e
                print "makeAPoliteDatabase: skipping this result"


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

    try:
        HrefStuffInst, fullResultHrefs, legacy = tryLegacy(date)
    except Exception, e:
        print e


    """loop through the number of races and make a ResultStuff object for each"""
    for fullResultHref in fullResultHrefs:
        if not fullResultHref:
            print "skipping abandoned race"
            continue
        try:
            HrefStuffInst.getFullResults(fullResultHref)
        except Exception, e:
            print e
            print "makeAResult: skipping this result"
        #print "got full results webpage for..."
        fullResult=HrefStuffInst.getFullResultsGrid()
        fullHeader=HrefStuffInst.getFullResultsHeader()
        fullInfo=HrefStuffInst.getFullRaceInfo()
        if legacy == 1:
            ResultStuffInst=webscrape_legacy.ResultStuff(fullResult, fullHeader, fullInfo, date)
        elif legacy == 2:
            ResultStuffInst=webscrape_legacy2.ResultStuff(fullResult, fullHeader, fullInfo, date)
        else:
            ResultStuffInst=webscrape.ResultStuff(fullResult, fullHeader, fullInfo, date)
        ResultStuffInst.getAllResultInfo()
        ResultStuffObjInst = webscrape.ResultStuffObj()
        ResultStuffObjInst.raceDate = ResultStuffInst.raceDate
        ResultStuffObjInst.horseNames= ResultStuffInst.horseNames
        ResultStuffObjInst.odds= ResultStuffInst.odds
        ResultStuffObjInst.draw= ResultStuffInst.draw
        ResultStuffObjInst.horseAges= ResultStuffInst.horseAges
        ResultStuffObjInst.horseWeights= ResultStuffInst.horseWeights
        ResultStuffObjInst.lengthGoingTypeTemp= ResultStuffInst.lengthGoingTypeTemp
        ResultStuffObjInst.jockeys= ResultStuffInst.jockeys
        ResultStuffObjInst.trainers= ResultStuffInst.trainers
        ResultStuffObjInst.finishingTime= ResultStuffInst.finishingTime

        """ResultStuffInst.getRaceDate()
        ResultStuffInst.getHorseNames()
        ResultStuffInst.getNumberOfHorses()
        ResultStuffInst.getRaceLength()
        ResultStuffInst.getHorseAge()
        ResultStuffInst.getHorseWeight()
        ResultStuffInst.getJockeyName()
        ResultStuffInst.getGoing()"""
        ResultStuffInsts.append(ResultStuffObjInst)
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

def viewADatabase(databaseName):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.viewAllTable()
    
def viewTopWinners(databaseName):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.getTopWinners()


def viewHorse(horseName, databaseName, verbose=True):
    if verbose:
        print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS"
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    return SqlStuffInst.viewHorse(horseName, verbose)

def viewJockey(jockeyName, databaseName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS"
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.viewJockey(jockeyName)

def viewDate(date, databaseName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS"
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.viewDate(date)

def viewNewestDate(databaseName, verbose = True):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    newestDate=SqlStuffInst.viewNewestDate(verbose = verbose)
    return newestDate

def viewOldestDate(databaseName):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.viewOldestDate()

def delDate(date, databaseName):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.delDate(date)

def delDuplicates(databaseName):
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.delDuplicates()


def delDateRange(dateStart, dateStop, databaseName):
    dateStartSplit=dateStart.split("-")
    dateStopSplit=dateStop.split("-")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateStopSplit[0]),int(dateStopSplit[1]),int(dateStopSplit[2]))):
        print single_date
        delDate(single_date, databaseName)

def countWinners(databaseNames):
    firstPlaces = []
    firstPlaceIntDraws = []
    firstPlaceValidDraws = []
    firstPlaceValidOdds = []
    firstPlaceValidRaceLength = []
    firstPlaceValidWeight = []
    firstPlaceValidHorse = []
    try:
        databaseNamesList=map(str, databaseNames.strip('[]').split(','))
        for databaseName in databaseNamesList:
    
            SqlStuffInst=SqlStuff2()
            SqlStuffInst.connectDatabase(databaseName)
            firstPlaces = firstPlaces + SqlStuffInst.getPosition(1)
    except Exception,e:
        print str(e)
    for firstPlace in firstPlaces:
        if isinstance(firstPlace[12], int):
            firstPlaceIntDraws.append(firstPlace)
            if firstPlace[12] != 255:
                firstPlaceValidDraws.append(firstPlace)

    for firstPlace in firstPlaceValidDraws:
        if "/" in firstPlace[15]:
            firstPlaceValidOdds.append(firstPlace)

    for firstPlace in firstPlaceValidOdds:
        try:
            meters = convertRaceLengthMetres(firstPlace[5])
            if meters > 0:
                firstPlaceValidRaceLength.append(firstPlace)
        except Exception, e:
            print str(e)
            continue

    for firstPlace in firstPlaceValidRaceLength:
        try:
            weight = convertWeightKilos(firstPlace[3])
            if weight != 60.0:
                firstPlaceValidWeight.append(firstPlace)
        except Exception,e:
            print str(e)
            continue



    for firstPlace in firstPlaceValidWeight:
        horse = []
        for databaseName in databaseNamesList:        
            try:
                horse = horse + viewHorse(firstPlace[1], databaseName, verbose=False)
                if len(horse) > 2:
                    firstPlaceValidHorse.append(firstPlace)
                    break
            except Exception,e:
                #print str(e)
                continue
            

    print "There are %d winners" % len(firstPlaces)
    print "There are %d winners with integer draws" % len(firstPlaceIntDraws)
    print "There are %d winners with valid draws" % len(firstPlaceValidDraws)
    print "There are %d winners with valid draws and odds" % len(firstPlaceValidOdds)
    print "There are %d winners with valid draws, odds and racelength" % len(firstPlaceValidRaceLength)
    print "There are %d winners with valid draws, odds, raceLength and weight" % len(firstPlaceValidWeight)
    print "There are %d winners with valid draws, odds, raceLength, weight and 3 runs" % len(firstPlaceValidHorse)

