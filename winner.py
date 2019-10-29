import sys
import os
import time
import datetime
import pickle
from common import daterange
from minmax import minMaxDraw
from minmax import meanStdGoing
from minmax import minMaxRaceLength
from minmax import minMaxSpeed
from minmax import minMaxWeight
from minmax import minMaxJockey
from minmax import normaliseDrawMinMax
from minmax import normaliseGoing
from minmax import normaliseRaceLengthMinMax
from minmax import normaliseWeightMinMax
from minmax import normaliseSpeed
from minmax import normaliseFinish
from minmax import normaliseJockeyTrainerMinMax
from minmax import getGoing
from sqlstuff2 import SqlStuff2
from webscrape import ResultStuffObj
from commands import makeATestcard, makeAResult, makeATestcardFromResults
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import SigmoidLayer
from pybrain.structure import TanhLayer
from pybrain.structure import LinearLayer
from pybrain.structure import SoftmaxLayer
from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader

def minMaxJockeyTrainer(horses, databaseNamesList,jockeyTrainer="jockey"):
    jockeys={}
    if jockeyTrainer=="jockey":
        dbNo=7
        minMaxJockeyListFilename = "minMaxJockeyList_"
    else:
        dbNo=13
        minMaxJockeyListFilename = "minMaxTrainerList_"
    for databaseName in databaseNamesList:
        minMaxJockeyListFilename = minMaxJockeyListFilename + str(databaseName)
    minMaxJockeyListFilename = minMaxJockeyListFilename + ".mm"
    SqlStuffInst=SqlStuff2()

    if os.path.exists(minMaxJockeyListFilename):
        print "reading jockeys/trainers from file in " + minMaxJockeyListFilename
        with open (minMaxJockeyListFilename, 'rb') as fp:
            jockeys = pickle.load(fp)

    if not jockeys:
        # first create a list where each jockey in the DS appears once
        for idx, horse in enumerate(horses):
            if idx%1000==0:
                print "db entry %d of %d" % (idx,len(horses)) 
            jockey=[]
            jockeyName=horse[dbNo]
            if not jockeyName in jockeys.keys():
                jockeys[jockeyName]= []
                #now loop through the databases and add all entries in the dict
                for databaseName in databaseNamesList:
                    #print "databaseName is " + str(databaseName)
                    SqlStuffInst.connectDatabase(databaseName)
                    if jockeyTrainer=="jockey":
                        jockey=jockey + SqlStuffInst.getJockey(jockeyName)
                    else:
                        jockey=jockey + SqlStuffInst.getTrainer(jockeyName)
                #now loop through the jockey and find the median score
                finish=0.0
                for ride in jockey:
                    OldRange = (ride[6] - 1)
                    if (OldRange == 0):
                        NewValue = 0.0
                    else:
                        NewRange = (1.0 - 0.0)  
                        NewValue = (((float(ride[4]) - 1.0) * NewRange) / float(OldRange)) #+ 0
                        # the 1.0- here makes it so a better jockey has a bigger value
                    finish=finish+float(1.0-NewValue)            
                meanFinishes=(finish/len(jockey))
                #now put this value in the dictionary
                jockeys[jockeyName]=meanFinishes
            
        print "There are " + str(len(jockeys)) + " in the minMaxJockey/Trainer function"

    with open(minMaxJockeyListFilename, 'wb') as fp:
        pickle.dump(jockeys, fp)

    return jockeys


def sortResult(decimalResult, horse, extra1, extra2, extra3, sortList, sortDecimal, sortHorse):
    """ sort the results by date and return the most recent x"""
    if len(sortList)==0:
        sortList.append(str(horse) + '('+str(decimalResult)+')('+str(extra1)+')('+str(extra2)+')('+str(extra3)+')')  # appemd the first horse
        sortDecimal.append(decimalResult)
        sortHorse.append(str(horse))
        return sortDecimal, sortList, sortHorse
    
    iterations = len(sortList)
    decimal1=decimalResult
    for idx in range(0, iterations):

        decimal0=sortDecimal[idx]

        if decimal1==0.0:
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(extra1)+')('+str(extra2)+')('+str(extra3)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))
            break
        elif decimal0==0.0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(extra1)+')('+str(extra2)+')('+str(extra3)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif decimal1 > decimal0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(extra1)+')('+str(extra2)+')('+str(extra3)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif idx == (iterations-1):
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(extra1)+')('+str(extra2)+')('+str(extra3)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))

    return sortDecimal, sortList, sortHorse

def testFunction(databaseNames, horseName, jockeyName, trainerName, raceLength, going, draw, weight, odds, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList,minMaxWeightList,minMaxJockeyList,minMaxTrainerList,jockeyDict,trainerDict, date, verbose=False):
    """This function will determine the inputs for the neural net for a horse"""
    anInput = [None] * 10
    horse = []
    SqlStuffInst=SqlStuff2()
    try:
        databaseNamesList=map(str, databaseNames.strip('[]').split(','))
        for databaseName in databaseNamesList:
            SqlStuffInst.connectDatabase(databaseName)
            horse=horse + SqlStuffInst.getHorse(horseName,date)
            if len(horse) > 2:
                break
    except Exception,e:
        print "problem with the database in testFunction"
        print "databaseNames is %s" % databaseNames
        print str(e)
        raise Exception(str(e))

    try:
        anInput[0] = normaliseFinish(horse[-1][4],horse[-1][6])
        anInput[1] = normaliseFinish(horse[-2][4],horse[-2][6])
        anInput[2] = normaliseFinish(horse[-3][4],horse[-3][6])
    except Exception,e:
        if verbose:
            print "skipping horse %s with problem form" % (horseName)
            print "found %d entries" % (int(len(horse)))
            print str(horse)
        raise Exception(str(e))
    # get the draw
    try:
        anInput[3] = normaliseDrawMinMax(draw,minMaxDrawList)
    except Exception,e:
        if verbose:
            print "skipping horse %s with problem draw" % (horseName)
            print "the draw is %s" % (str(draw))
            print "the minMaxDrawList is %s" % (str(minMaxDrawList))
        raise Exception(str(e))
    # get the going
    try:
        anInput[4] = normaliseGoing(getGoing(going), meanStdGoingList)
    except Exception,e:
        if verbose:
            print "skipping horse %s with no going" % (horseName)
        raise Exception(str(e))
    # get the race length
    try:
        anInput[5] = normaliseRaceLengthMinMax(raceLength, minMaxRaceLengthList)
    except Exception,e:
        if verbose:
            print "skipping horse %s with no or bad racelength" % (horseName)
        raise Exception(str(e))
    # get the weight
    try:
        anInput[6] = normaliseWeightMinMax(weight, minMaxWeightList)
    except Exception,e:
        if verbose:
            print "skipping horse %s with no or bad weight" % (horseName)
        raise Exception(str(e))
    # get the jockey
    try:
        anInput[7]= normaliseJockeyTrainerMinMax(jockeyDict[jockeyName], minMaxJockeyList)
    except Exception,e:
        print "problem with the jockey normalise in the testfunction"
        raise Exception(str(e))
    # get the trainer
    try:
        anInput[8]= normaliseJockeyTrainerMinMax(trainerDict[trainerName], minMaxTrainerList)
    except Exception,e:
        print "problem with the trainer normalise in the testfunction"
        raise Exception(str(e))
    # get the odds
    try:
        anInput[9] = float(odds.split("/")[0])/float(odds.split("/")[1])
    except Exception,e:
        print "problem with the odds %s" % str(odds)
        print str(odds.split("/"))
        print str(e)
        raise Exception(str(e))


    #if verbose:
    #    print str(anInput)
    return anInput



def neuralNet(net, databaseNames, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList,minMaxWeightList,minMaxJockeyList,minMaxTrainerList,jockeyDict,trainerDict, result = False, date=time.strftime("%Y-%m-%d"), verbose=False):
    #lengths=[]
    #draws=[]
    print "the date is " + str(date)
    print "and todays date is " + str(datetime.datetime.today().strftime('%Y-%m-%d'))
    try:
        if date >= datetime.datetime.today().strftime('%Y-%m-%d'):
            print "trying to make a test card from the days test card as date is today or later"
            horses, jockeys, lengths, weights, goings, draws, trainers, odds, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
            makeResult = False
        else:
            print "tring to make a test card from past results"
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues, odds=makeATestcardFromResults(date)
            makeResult = result
    except Exception:
        print "making a testcard from results failed"

    if makeResult != False:
        todaysResults=makeAResult(date)
    print todaysRaceVenues
    
    returnSortHorse=[]
    returnPastPerf=[]
    returnResults=[]

    for raceNo, race in enumerate(horses):
        if verbose:
            print str(race)
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        sortList=[]
        sortDecimal=[]
        sortHorse=[]
        skipFileWrite=0

        for idx, horse in enumerate(race):
            if verbose:
                print str(horse)
            errors=0
            yValues=0
            bO=0
            if skipFileWrite==1:
                break;
            if len(race) > 40:
                skipFileWrite=1
                break;
             
            try:
                if verbose:
                    print "calling test function"
                testinput=testFunction(databaseNames, horses[raceNo][idx],jockeys[raceNo][idx],trainers[raceNo][idx],lengths[raceNo],goings[raceNo], draws[raceNo][idx], weights[raceNo][idx], odds[raceNo][idx], minMaxDrawList, meanStdGoingList,minMaxRaceLengthList,minMaxWeightList,minMaxJockeyList,minMaxTrainerList,jockeyDict,trainerDict,date)
                if verbose:
                    print "after test function / before net"
                result=net.activate(testinput)
                if verbose:
                    print "after net / before sort"
                sortDecimal, sortList, sortHorse=sortResult(result, str(horse), str(odds[raceNo][idx]), str(0), str(0), sortList, sortDecimal, sortHorse)
                if verbose:
                    print "after sort"
            except Exception, e:
                if verbose:
                    print "something not correct in testFunction"
                    print str(e)
                skipFileWrite=1

        if skipFileWrite==0:
            
            returnSortHorse.append(sortHorse)
            
            if makeResult == True:
                returnResults.append(todaysResults[raceNo])

            print str(raceNo) + ' ' + str(todaysRaceVenues[raceNo]) + ' ' + str(todaysRaceTimes[raceNo]) 
            for ii, pos in enumerate(sortList):
                try:
                    if makeResult == False:
                        print str(ii+1) + pos 
                    else:
                        print str(ii+1) + pos + '       ' + str(todaysResults[raceNo].horseNames[ii]) + ' ' + str(todaysResults[raceNo].odds[ii])
                except IndexError:
                    """if there are none finishers this will be the exception"""

    return returnSortHorse, returnResults



def checkResults(netOut, results):

    fpFpOdds =[]
    spFpOdds =[]
    fpEwOdds =[]
    spEwOdds =[]

    fpEwMoney = 0.0
    spEwMoney= 0.0

    if len(results) == 0 or len(netOut) == 0:
        print "No results to check"
        return 0

    for net, result in zip(netOut, results):

        try:
            if net[0]==result.horseNames[0]:
                odd_split=result.odds[0].split("/")
                fpFpOdds.append((float(odd_split[0])/float(odd_split[1])))
                fpEwOdds.append((float(odd_split[0])/float(odd_split[1])))
                fpEwMoney = fpEwMoney + 10.0 + (10.0 *(float(odd_split[0])/float(odd_split[1])))
        except Exception,e:
            print "problem with fpFpOdds"
            pass

        try:
            if net[1]==result.horseNames[0]:
                odd_split=result.odds[0].split("/")
                spFpOdds.append((float(odd_split[0])/float(odd_split[1])))
                spEwOdds.append((float(odd_split[0])/float(odd_split[1])))
                spEwMoney = spEwMoney + 10.0 + (10.0 *(float(odd_split[0])/float(odd_split[1])))
        except Exception,e:
            print "problem with fpFpOdds"
            pass

    # do the each way oodds too
    for net, result in zip(netOut, results):
        try:
            fpEwMoney = fpEwMoney - 20.0
            spEwMoney = spEwMoney - 20.0
        except Exception, e:
            print str(e)

        try:
            if net[0]==result.horseNames[0]:
                odd_split=result.odds[0].split("/")
                fpEwOdds[-1] = fpEwOdds[-1] + ((float(odd_split[0])/float(odd_split[1]))/2.0)
                fpEwMoney = fpEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
            if net[0]==result.horseNames[1]:
                odd_split=result.odds[1].split("/")
                fpEwOdds.append((float(odd_split[0])/float(odd_split[1]))/2.0)
                fpEwMoney = fpEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
            if net[0]==result.horseNames[2]:
                odd_split=result.odds[2].split("/")
                fpEwOdds.append((float(odd_split[0])/float(odd_split[1]))/2.0)
                fpEwMoney = fpEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
        except Exception,e:
            print "problem with fpEwOdds"
            pass


        try:
            if net[1]==result.horseNames[0]:
                odd_split=result.odds[0].split("/")
                spEwOdds[-1] = spEwOdds[-1] + ((float(odd_split[0])/float(odd_split[1]))/2.0)
                spEwMoney = spEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
            if net[1]==result.horseNames[1]:
                odd_split=result.odds[1].split("/")
                spEwOdds.append((float(odd_split[0])/float(odd_split[1]))/2.0)
                spEwMoney = spEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
            if net[1]==result.horseNames[2]:
                odd_split=result.odds[2].split("/")
                spEwOdds.append((float(odd_split[0])/float(odd_split[1]))/2.0)
                spEwMoney = spEwMoney + 10.0 + (10.0 * ((float(odd_split[0])/float(odd_split[1]))/4.0))
        except Exception,e:
            print "problem with spEwOdds"
            pass

    try:
        print "1st place prediction won %d times with average odds %f" % (len(fpFpOdds), sum(fpFpOdds)/len(fpFpOdds))
    except ZeroDivisionError:
        pass
    try:
        print "1st place prediction came top 3 %d times with average odds %f" % (len(fpEwOdds), sum(fpEwOdds)/len(fpEwOdds))
    except ZeroDivisionError:
        pass
    try:
        print "2nd place prediction won %d times with average odds %f" % (len(spFpOdds), sum(spFpOdds)/len(spFpOdds))
    except ZeroDivisionError:
        pass
    try:
        print "2nd place prediction came top 3 %d times with average odds %f" % (len(spEwOdds), sum(spEwOdds)/len(spEwOdds))
    except ZeroDivisionError:
        pass

    print "The total number of races was %d" % len(netOut)
    print "So the average odds over all races....."
    
    try:
        print "1st place prediction won %d times with average odds %f" % (len(fpFpOdds), sum(fpFpOdds)/len(netOut))
    except ZeroDivisionError:
        pass
    try:
        print "1st place prediction came top 3 %d times with average odds %f" % (len(fpEwOdds), sum(fpEwOdds)/len(netOut))
    except ZeroDivisionError:
        pass
    try:
        print "2nd place prediction won %d times with average odds %f" % (len(spFpOdds), sum(spFpOdds)/len(netOut))
    except ZeroDivisionError:
        pass
    try:
        print "2nd place prediction came top 3 %d times with average odds %f" % (len(spEwOdds), sum(spEwOdds)/len(netOut))
    except ZeroDivisionError:
        pass
    try:
        print "the 1st place top 3 prediction made %f" % (fpEwMoney)
    except Exception, e:
        pass
    try:
        print "the 2nd place top 3 prediction made %f" % (spEwMoney)
    except Exception, e:
        pass


    return (sum(fpFpOdds), sum(fpEwOdds), sum(spFpOdds), sum(spEwOdds), len(netOut), fpEwMoney, spEwMoney)




def getWinners(databaseNames, filename, date=-1):
    """ This is a function that will extract all the winners from
    multiple databases and return them in an array and save them
    to a winners.db database"""
    SqlStuffInst=SqlStuff2()
    winners=[]
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    print "databaseNamesList is " + str(databaseNamesList)
    for databaseName in databaseNamesList:
        print "databaseName is " + str(databaseName)
        SqlStuffInst.connectDatabase(databaseName)
        winners=winners + SqlStuffInst.getPosition(1)

    # delete any existing winners.db file
    if os.path.exists(filename):
        os.remove(filename)
    # save the databaseNames string in a file
    f= open("databaseNames.txt","w+")
    f.write(databaseNames)
    # save the winners in a winners.db
    winnerSqlStuffInst=SqlStuff2()
    winnerSqlStuffInst.connectDatabase(filename)
    winnerSqlStuffInst.createResultTable()

    ResultStuffInstList = []
    for row in winners:
        ResultStuffInst=ResultStuffObj()
        ResultStuffInst.horseNames.append(row[1])
        ResultStuffInst.horseAges.append(row[2])
        ResultStuffInst.horseWeights.append(row[3])
        ResultStuffInst.raceLength = row[5]
        ResultStuffInst.numberOfHorses = row[6]
        ResultStuffInst.jockeys.append(row[7])
        ResultStuffInst.going = row[8]
        ResultStuffInst.raceDate = row[9]
        ResultStuffInst.raceTime = row[10]
        ResultStuffInst.raceName = row[11]
        ResultStuffInst.draw.append(row[12])
        ResultStuffInst.trainers.append(row[13])
        ResultStuffInst.finishingTime.append(row[14])
        ResultStuffInst.odds.append(row[15])
        ResultStuffInstList.append(ResultStuffInst)
        winnerSqlStuffInst.addResultStuffToTable(ResultStuffInst, pos=row[4])

def getWinnersSubsetHorse(races, winnerdb, winners_racesdb, databaseNames):
    """ this function will look in the resultsdb for every
    horse that is in the winnerdb to check it has run at 
    least <races> number of races"""
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    print "databaseNamesList is " + str(databaseNamesList)

    # save the winners races in a winners_races.db
    winner_racesSqlStuffInst=SqlStuff2()
    winner_racesSqlStuffInst.connectDatabase(winners_racesdb)
    winner_racesSqlStuffInst.createResultTable()

    # get all the horsenames from the winnerdb
    winnerSqlStuffInst=SqlStuff2()
    winnerSqlStuffInst.connectDatabase(winnerdb)
    winnerSqlStuffInst.getAllTable()


    SqlStuffInst=SqlStuff2()
    for horseInfo in winnerSqlStuffInst.rows:
        horseName= horseInfo[1]
        horse= []
        #check that horseName is not already in the winner_races.db
        if len(winner_racesSqlStuffInst.getHorse(horseName)) > 0:
            continue
        for databaseName in databaseNamesList:
            #print "databaseName is " + str(databaseName)
            SqlStuffInst.connectDatabase(databaseName)
            horse=horse + SqlStuffInst.getHorse(horseName)
        # if the horse has races or more entries then add them
        # all to the winner_races.db otherwise delete this horse
        # from the winners.db
        #print "the horseName is %s" % (str(horseName))
        #print "the length of horse is %d" % (int(len(horse)))
        if len(horse) > races-1:
            ResultStuffInstList = []
            for row in horse:
                ResultStuffInst=ResultStuffObj()
                ResultStuffInst.horseNames.append(row[1])
                ResultStuffInst.horseAges.append(row[2])
                ResultStuffInst.horseWeights.append(row[3])
                ResultStuffInst.raceLength = row[5]
                ResultStuffInst.numberOfHorses = row[6]
                ResultStuffInst.jockeys.append(row[7])
                ResultStuffInst.going = row[8]
                ResultStuffInst.raceDate = row[9]
                ResultStuffInst.raceTime = row[10]
                ResultStuffInst.raceName = row[11]
                ResultStuffInst.draw.append(row[12])
                ResultStuffInst.trainers.append(row[13])
                ResultStuffInst.finishingTime.append(row[14])
                ResultStuffInst.odds.append(row[15])
                ResultStuffInstList.append(ResultStuffInst)
                winner_racesSqlStuffInst.addResultStuffToTable(ResultStuffInst, pos=row[4])
        else:
            winnerSqlStuffInst.delHorse(horseName)

def getInOutputsToNet(winnerdb, winner_racesdb, databaseNames, dateStart, dateEnd=False, verbose=False):
    """ create a text file of all the inputs to the net"""

    if not dateEnd:
        dateEnd=dateStart
    #input 0,1,2 the past positions of this horse when it won
    #input 3 draw
    #input 4 going
    #input 5 race length
    anInput = [None] * 10

    netFilename = "net"
    print "create the DS"
    DS = SupervisedDataSet(len(anInput), 1)
    hiddenLayer0=8 #(len(anInput)+1)/2
    hiddenLayer1=6 #(len(anInput)+1)/2 -1
    hiddenLayer2=4 #(len(anInput)+1)/2 -1
    hiddenLayer3=4
    hiddenLayer4=3
    hiddenLayer5=3
    netFilename = netFilename + "_" + str(hiddenLayer0) + "_" + str(hiddenLayer1) + "_" + str(hiddenLayer2) + "_" + str(hiddenLayer3) + "_" + str(hiddenLayer4) + "_" + str(hiddenLayer5) + ".xml"

    # get all the winner horses from the winnerdb
    winnerSqlStuffInst=SqlStuff2()
    winnerSqlStuffInst.connectDatabase(winnerdb)
    firstPlaceHorses=winnerSqlStuffInst.getAllTable()

    #base the min max values on all the databases (not just the winners)
    allHorseSqlStuffInst=SqlStuff2()
    allHorses=[]
    try:
        databaseNamesList=map(str, databaseNames.strip('[]').split(','))
        for databaseName in databaseNamesList:
            allHorseSqlStuffInst.connectDatabase(databaseName)
            allHorses=allHorses + allHorseSqlStuffInst.getAllTable()

    except Exception,e:
        print "problem with the database in testFunction"
        print "databaseNames is %s" % databaseNames
        print str(e)
        raise Exception

    lessThanThree = 0
    pastPerf = 0
    badDraw = 0
    badGoing = 0
    badRaceLength = 0
    badWeight = 0
    badJockey = 0
    badTrainer = 0
    badOdds = 0
    badSpeed = 0


    minMaxDrawList = minMaxDraw(allHorses)
    meanStdGoingList = meanStdGoing(allHorses)
    minMaxRaceLengthList = minMaxRaceLength(allHorses)
    minMaxWeightList = minMaxWeight(allHorses)
    minMaxSpeedList = minMaxSpeed(firstPlaceHorses)
    jockeyDict=minMaxJockeyTrainer(allHorses, databaseNamesList,jockeyTrainer="jockey")
    minMaxJockeyList = minMaxJockey(jockeyDict)
    trainerDict=minMaxJockeyTrainer(allHorses, databaseNamesList,jockeyTrainer="trainer")
    minMaxTrainerList = minMaxJockey(trainerDict)

    # save the winners races in a winners_races.db
    winner_racesSqlStuffInst=SqlStuff2()
    winner_racesSqlStuffInst.connectDatabase(winner_racesdb)

    if os.path.exists(netFilename):
        print "found network training file"
        net = NetworkReader.readFrom(netFilename) 
    else:
        for idx, horseInfo in enumerate(winnerSqlStuffInst.rows):
            if idx%1000==0:
                print "Net input %d of %d generated" % (idx, len(winnerSqlStuffInst.rows))
            horseName= horseInfo[1]
            date=horseInfo[9]
            horse= []
            horse=horse + winner_racesSqlStuffInst.getHorse(horseName, date)
            # if the length of horse is less than 3 then this cannot 
            # be used
            if len(horse) < 3:
                lessThanThree = lessThanThree+1
                continue
            # get the positions from the 3 races before the win
            # put the positions into the input list in pos 0,1,2
            try:
                anInput[0] = normaliseFinish(horse[-1][4],horse[-1][6])
                anInput[1] = normaliseFinish(horse[-2][4],horse[-2][6])
                anInput[2] = normaliseFinish(horse[-3][4],horse[-3][6])
                if verbose:
                    print "horseName %s - dates %s   %s   %s" % (str(horse[-1][1]), str(horse[-1][9]), str(horse[-2][9]), str(horse[-3][9]))
            except Exception,e:
                print "skipping horse %d of %d  with bad form" % (idx, len(winnerSqlStuffInst.rows))   
                print str(e)
                pastPerf = pastPerf + 1
                continue
            # get the draw
            try:
                anInput[3] = normaliseDrawMinMax(horseInfo[12],minMaxDrawList)
            except Exception,e:
                print "skipping horse %d of %d  with bad/no draw" % (idx, len(winnerSqlStuffInst.rows))   
                print str(e)
                badDraw = badDraw + 1
                continue
            # get the going
            try:
                anInput[4] = normaliseGoing(getGoing(horseInfo[8]), meanStdGoingList)
            except Exception,e:
                print "skipping horse %d of %d  with no going" % (idx, len(winnerSqlStuffInst.rows))
                print str(e)
                badGoing = badGoing + 1
                continue
            # get the race length
            try:
                anInput[5] = normaliseRaceLengthMinMax(horseInfo[5], minMaxRaceLengthList)
            except:
                print "skipping horse %d of %d  with no length" % (idx, len(winnerSqlStuffInst.rows))
                badRaceLength = badRaceLength + 1
                continue

            try:
                anInput[6] = normaliseWeightMinMax(horseInfo[3], minMaxWeightList)
            except Exception, e:
                print str(e)
                print "the weight is " + str(horseInfo[3])
                print "skipping horse %d of %d  with no weight" % (idx, len(winnerSqlStuffInst.rows))
                badWeight = badWeight + 1
                continue

            try:
                jockeyName=horseInfo[7]
                anInput[7] = normaliseJockeyTrainerMinMax(jockeyDict[jockeyName], minMaxJockeyList)
            except Exception,e:
                print "problem with the jockey normalise"
                print "jockey is %s, median is %s.  Min is %s, max is %s" % (str(jockeyName), str(jockeyDict[jockeyName]),str(minMaxJockeyList[0]), str(minMaxJockeyList[1])) 
                print str(e)
                badJockey = badJockey + 1
                continue

            try:
                trainerName=horseInfo[13]
                anInput[8] = normaliseJockeyTrainerMinMax(trainerDict[trainerName], minMaxTrainerList)
            except Exception,e:
                print "problem with the trainer normalise"
                print "trainer is %s, median is %s.  Min is %s, max is %s" % (str(trainerName), str(trainerDict[trainerName]),str(minMaxTrainerList[0]), str(minMaxTrainerList[1])) 
                print str(e)
                badTrainer = badTrainer + 1
                continue


            try:
                odds=horseInfo[15]
                anInput[9] = float(odds.split("/")[0])/float(odds.split("/")[1])
            except Exception,e:
                print "problem with the odds %s" % str(odds)
                print str(odds.split("/"))
                badOdds = badOdds + 1
                continue

            # get the output speed
            try:
                output = normaliseSpeed(horseInfo, minMaxSpeedList)
            except Exception, e:
                print "problem normalising speed"
                print str(e)
                badSpeed = badSpeed + 1
                continue

            DS.appendLinked(anInput, output) 

        tstdata, trndata = DS.splitWithProportion( 0.25 )
        #trndata=DS
        #tstdata=DS
        print "winners with less that three runs = %d" % lessThanThree
        print "bad past performance = %d" % pastPerf
        print "bad draw = %d" % badDraw
        print "bad going = %d" % badGoing
        print "bad race length = %d" % badRaceLength
        print "bad weight = %d" % badWeight
        print "bad jockey = %d" % badJockey
        print "bad trainer = %d" % badTrainer
        print "bad odds = %d" % badOdds
        print "bad speed = %d" % badSpeed


        print "length of trndata is " + str(len(trndata))
        print "length of tstdata is " + str(len(tstdata))
        # number of hidden layers and nodes

        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, hiddenLayer5, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer) # 4,10,5,1
        trainer=BackpropTrainer(net,trndata, momentum=0.1, verbose=True, learningrate=0.01)

        aux=trainer.trainUntilConvergence(dataset=DS, maxEpochs=30, verbose=True, continueEpochs=2, validationProportion=0.25)

        mse=trainer.testOnData(dataset=tstdata)
        print "Mean Squared Error = " + str(mse)

        # save the net params
        NetworkWriter.writeToFile(net, netFilename)

    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')

    allFpFpOdds = []
    allFpEwOdds = []
    allSpFpOdds = []
    allSpEwOdds = []
    allLenNetOut = []
    fpFpOdds = 0.0
    fpEwOdds = 0.0
    spFpOdds = 0.0
    spEwOdds = 0.0
    lenNetOut = 0.0
    fpEwMoneyTotal = 0.0
    spEwMoneyTotal = 0.0


    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):

        dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       
        print dateIn

        netOut, results = neuralNet(net, databaseNames, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList,minMaxWeightList,minMaxJockeyList,minMaxTrainerList,jockeyDict,trainerDict, result = True, date=dateIn)
    
        fpFpOdds, fpEwOdds, spFpOdds, spEwOdds, lenNetOut, fpEwMoney, spEwMoney = checkResults(netOut, results)

        allFpFpOdds.append(fpFpOdds)
        allFpEwOdds.append(fpEwOdds)
        allSpFpOdds.append(spFpOdds)
        allSpEwOdds.append(spEwOdds)
        allLenNetOut.append(lenNetOut)

        totalFpFpOdds = sum(allFpFpOdds)
        totalFpEwOdds = sum(allFpEwOdds)
        totalSpFpOdds = sum(allSpFpOdds)
        totalSpEwOdds = sum(allSpEwOdds)
        totalLenNetOut = sum(allLenNetOut)
        fpEwMoneyTotal = fpEwMoneyTotal + fpEwMoney
        spEwMoneyTotal = spEwMoneyTotal + spEwMoney

        try:
            print "1st place prediction average odds %f" % (float(totalFpFpOdds)/float(totalLenNetOut))
        except ZeroDivisionError:
            pass
        except TypeError:
            print str(totalFpFpOdds)
            print str(totalLenNetOut)
            print str(allFpFpOdds)
            print str(allLenNetOut)
        try:
            print "1st place prediction came top 3 with average odds %f" % (float(totalFpEwOdds)/float(totalLenNetOut))
        except ZeroDivisionError:
            pass
        try:
            print "2nd place prediction won with average odds %f" % (float(totalSpFpOdds)/float(totalLenNetOut))
        except ZeroDivisionError:
            pass
        try:
            print "2nd place prediction came top 3 with average odds %f" % (float(totalSpEwOdds)/float(totalLenNetOut))
        except ZeroDivisionError:
            pass
        try:
            print "the total number of racee is %d" % (int(totalLenNetOut))
        except Exception,e:
            print str(e)
            pass
        try:
            print "the total 1st place top 3 money is %f" % (fpEwMoneyTotal)
        except Exception,e:
            pass
        try:
            print "the total 2nd place top 3 money is %f" % (spEwMoneyTotal)
        except Exception,e:
            pass
        
