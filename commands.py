#import urllib2,  time, re

#from BeautifulSoup import BeautifulSoup

#from string import whitespace

#from sqlstuff import SqlStuff
from sqlstuff2 import SqlStuff2
import datetime
#import os.path
import os

import time
from common import daterange
from minmax import convertRaceLengthMetres
from minmax import convertWeightKilos


def writeAResult(date, filenameAppend):
    """write the dates result to a file"""
    todaysResults=makeAResult(date)
    f = open(str(date)+str(filenameAppend),'a')
    original = sys.stdout
    sys.stdout = Tee(sys.stdout, f)
    for idx, ii in enumerate(todaysResults):
        print ("race number " + str(idx) )
        for jdx, jj in enumerate(todaysResults[idx].horseNames):
            print (str(jj))
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
        print ("ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS")
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    return SqlStuffInst.viewHorse(horseName, verbose)

def viewJockey(jockeyName, databaseName):
    print ("ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS")
    SqlStuffInst=SqlStuff2()
    SqlStuffInst.connectDatabase(databaseName)
    SqlStuffInst.viewJockey(jockeyName)

def viewMultiple(databaseName, horseName="", horseAge="", horseWeight="", position="", raceLength="", numberHorses="", jockeyName="", going="", raceDate="", raceTime="", raceVenue="", draw="", trainerName=""):
    info = []
    if isinstance(databaseName, list):
        for dbName in databaseName:
            SqlStuffInst=SqlStuff2()
            SqlStuffInst.connectDatabase(dbName)
            info = info + SqlStuffInst.getMultiple(horseName=horseName, horseAge=horseAge, horseWeight=horseWeight, position=position, raceLength=raceLength, numberHorses=numberHorses, jockeyName=jockeyName, going=going, raceDate=raceDate, raceTime=raceTime, raceVenue=raceVenue, draw=draw, trainerName=trainerName)
    else:
        SqlStuffInst=SqlStuff2()
        SqlStuffInst.connectDatabase(databaseName)
        info = info + SqlStuffInst.getMultiple(horseName=horseName, horseAge=horseAge, horseWeight=horseWeight, position=position, raceLength=raceLength, numberHorses=numberHorses, jockeyName=jockeyName, going=going, raceDate=raceDate, raceTime=raceTime, raceVenue=raceVenue, draw=draw, trainerName=trainerName)

    return info

def viewDate(date, databaseName):
    dateInfo = []
    print ("ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS")
    if isinstance(databaseName, list):
        for dbName in databaseName:
            SqlStuffInst=SqlStuff2()
            SqlStuffInst.connectDatabase(dbName)
            dateInfo = dateInfo + SqlStuffInst.viewDate(date)
    else:
        SqlStuffInst=SqlStuff2()
        SqlStuffInst.connectDatabase(databaseName)
        dateInfo = dateInfo + SqlStuffInst.viewDate(date)
    return dateInfo

def viewNewestDate(databaseName, verbose = True):
    if isinstance(databaseName, list):
        for dbName in databaseName:
            SqlStuffInst=SqlStuff2()
            SqlStuffInst.connectDatabase(dbName)
            newestDate=SqlStuffInst.viewNewestDate(verbose = verbose)
    else:
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
        print (single_date)
        delDate(single_date, databaseName)


def get_average_odds(database, year):
    odds_cumm_list=100*[float(0.0)]
    odds_hit_list=100*[0]
    date_start = str(year) + "-01-01"
    date_end = str(year) + "-12-31"
    dateStartSplit = date_start.split("-")
    dateEndSplit = date_end.split("-")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date_results = viewMultiple(database, raceDate=str(single_date))
        raceTime=date_results[0][10]
        raceVenue=date_results[0][11]
        race_results = viewMultiple(database, raceDate=str(single_date), raceTime=raceTime, raceVenue=raceVenue)
        race_odds_list = []
        for race_result in race_results:
            odds_str = race_result[15]
            odds_split = odds_str.split("/")
            try:
                odds = float(odds_split[0])/float(odds_split[1])
            except ValueError as e:
                print("skipping one odds")
                continue
            race_odds_list.append(odds)
        race_odds_list.sort()
        for ii, race_odds in enumerate(race_odds_list):
            odds_cumm_list[ii] = odds_cumm_list[ii] + race_odds
            odds_hit_list[ii] = odds_hit_list[ii] + 1
    odds_list = []
    for ii, entry in enumerate(odds_cumm_list):
        if odds_hit_list[ii] == 0:
            continue
        else:
            odds_list.append(entry/float(odds_hit_list[ii]))
    for ii, entry in enumerate(odds_list):
        print("position %d,   %f" % (ii, entry))
    print (odds_list)


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
    except Exception as e:
        print (str(e))
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
        except Exception as e:
            print (str(e))
            continue

    for firstPlace in firstPlaceValidRaceLength:
        try:
            weight = convertWeightKilos(firstPlace[3])
            if weight != 60.0:
                firstPlaceValidWeight.append(firstPlace)
        except Exception as e:
            print (str(e))
            continue



    for firstPlace in firstPlaceValidWeight:
        horse = []
        for databaseName in databaseNamesList:        
            try:
                horse = horse + viewHorse(firstPlace[1], databaseName, verbose=False)
                if len(horse) > 2:
                    firstPlaceValidHorse.append(firstPlace)
                    break
            except Exception as e:
                #print str(e)
                continue
            

    print ("There are %d winners" % len(firstPlaces))
    print ("There are %d winners with integer draws" % len(firstPlaceIntDraws))
    print ("There are %d winners with valid draws" % len(firstPlaceValidDraws))
    print ("There are %d winners with valid draws and odds" % len(firstPlaceValidOdds))
    print ("There are %d winners with valid draws, odds and racelength" % len(firstPlaceValidRaceLength))
    print ("There are %d winners with valid draws, odds, raceLength and weight" % len(firstPlaceValidWeight))
    print ("There are %d winners with valid draws, odds, raceLength, weight and 3 runs" % len(firstPlaceValidHorse))

