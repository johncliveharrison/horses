import sys
import os
import time
import datetime
from minmax import minMaxDraw
from minmax import meanStdGoing
from minmax import minMaxRaceLength
from minmax import minMaxSpeed
from minmax import normaliseDrawMinMax
from minmax import normaliseGoing
from minmax import normaliseRaceLengthMinMax
from minmax import normaliseSpeed
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


def sortResult(decimalResult, horse, extra1, extra2, extra3, error, sortList, sortDecimal, sortHorse):
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

def testFunction(self, databaseNames, horseName, raceLength, going, draw, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList):
    """This function will determine the inputs for the neural net for a horse"""
    anInput = [None] * 6
    horse = []
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    print "databaseNamesList is " + str(databaseNamesList)
    for databaseName in databaseNamesList:
        print "databaseName is " + str(databaseName)
        SqlStuffInst.connectDatabase(databaseName)
        horse=horse + SqlStuffInst.getHorse(horseName)
        if len(horse) > 2:
            break

    anInput[0] = horse[-1][4]/horse[-1][6]
    anInput[1] = horse[-2][4]/horse[-2][6]
    anInput[2] = horse[-3][4]/horse[-3][6]
    # get the draw
    try:
        anInput[3] = normaliseDrawMinMax(draw,minMaxDrawList)
    except TypeError:
        print "skipping horse %s with problem draw" % (horseName)
        raise Exception

    # get the going
    try:
        anInput[4] = normaliseGoing(getGoing(going), meanStdGoingList)
    except TypeError:
        print "skipping horse %s with no going" % (horseName)
        raise Exception
    # get the race length
    anInput[5] = normaliseRaceLengthMinMax(raceLength, minMaxRaceLengthList)


    return anInput



def neuralNet(net, databaseNames, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList, makeResult = False, date=time.strftime("%Y-%m-%d")):
    #lengths=[]
    #draws=[]
    print "the date is " + str(date)
    print "and todays date is " + str(datetime.datetime.today().strftime('%Y-%m-%d'))
    try:
        if date >= datetime.datetime.today().strftime('%Y-%m-%d'):
            print "trying to make a test card from the days test card as date is today or later"
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
        else:
            print "tring to make a test card from past results"
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues, odds=makeATestcardFromResults(date)
    except Exception:
        print "making a testcard from results failed"

    if makeResult != False:
        todaysResults=makeAResult(date)
    print todaysRaceVenues
    
    returnSortHorse=[]
    returnPastPerf=[]
    returnResults=[]

    for raceNo, race in enumerate(horses):
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        sortList=[]
        sortDecimal=[]
        sortHorse=[]
        skipFileWrite=0

        for idx, horse in enumerate(race):
            errors=0
            yValues=0
            bO=0
            if skipFileWrite==1:
                break;
            if len(race) > 40:
                skipFileWrite=1
                break;
             
            try:
                testinput=testFunction(databaseNames, horses[raceNo][idx],lengths[raceNo],goings[raceNo], draws[raceNo][idx],minMaxDrawList, meanStdGoingList,minMaxRaceLengthList)

                result=net.activate(testinput)

                sortDecimal, sortList, sortHorse=sortResult(result, str(horse), str(0), 0, sortList, sortDecimal, sortHorse)
            
            except Exception, e:
                print "something not correct in testFunction"
                #skipFileWrite=1

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

    return returnSortHorse, returnResults, oddsWinnings




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

def getWinnersSubsetHorse(races, winnerdb, databaseNames):
    """ this function will look in the resultsdb for every
    horse that is in the winnerdb to check it has run at 
    least <races> number of races"""
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    print "databaseNamesList is " + str(databaseNamesList)

    # save the winners races in a winners_races.db
    winner_racesSqlStuffInst=SqlStuff2()
    winner_racesSqlStuffInst.connectDatabase("winners_races.db")
    winner_racesSqlStuffInst.createResultTable()

    # get all the horsenames from the winnerdb
    winnerSqlStuffInst=SqlStuff2()
    winnerSqlStuffInst.connectDatabase("winners.db")
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


def getInOutputsToNet(winnerdb, winner_racesdb, databaseNames, dateIn):
    """ create a text file of all the inputs to the net"""

    #input 0,1,2 the past positions of this horse when it won
    #input 3 draw
    #input 4 going
    #input 5 race length
    anInput = [None] * 6

    netFilename = "net"
    print "create the DS"
    DS = SupervisedDataSet(len(anInput), 1)
    hiddenLayer0=(len(anInput)+1)/2
    hiddenLayer1=0
    netFilename = netFilename + "_" + str(hiddenLayer0) + "_" + str(hiddenLayer1) + ".xml"

    # get all the winner horses from the winnerdb
    winnerSqlStuffInst=SqlStuff2()
    winnerSqlStuffInst.connectDatabase(winnerdb)
    firstPlaceHorses=winnerSqlStuffInst.getAllTable()
    minMaxDrawList = minMaxDraw(firstPlaceHorses)
    meanStdGoingList = meanStdGoing(firstPlaceHorses)
    minMaxRaceLengthList = minMaxRaceLength(firstPlaceHorses)
    minMaxSpeedList = minMaxSpeed(firstPlaceHorses)
    # save the winners races in a winners_races.db
    winner_racesSqlStuffInst=SqlStuff2()
    winner_racesSqlStuffInst.connectDatabase(winner_racesdb)

    if os.path.exists(netFilename):
        print "found network training file"
        net = NetworkReader.readFrom(netFilename) 
    else:
        for idx, horseInfo in enumerate(winnerSqlStuffInst.rows):
            horseName= horseInfo[1]
            date=horseInfo[9]
            horse= []
            horse=horse + winner_racesSqlStuffInst.getHorse(horseName, date)
            # if the length of horse is less than 3 then this cannot 
            # be used
            if len(horse) < 3:
                continue
            # get the positions from the 3 races before the win
            # put the positions into the input list in pos 0,1,2
            try:
                anInput[0] = horse[-1][4]/horse[-1][6]
                anInput[1] = horse[-2][4]/horse[-2][6]
                anInput[2] = horse[-3][4]/horse[-3][6]
            except Exception:
                print "skipping horse %d of %d  with bad form" % (idx, len(winnerSqlStuffInst.rows))   
                continue
            # get the draw
            try:
                anInput[3] = normaliseDrawMinMax(horseInfo[12],minMaxDrawList)
            except TypeError:
                print "skipping horse %d of %d  with bad/no draw" % (idx, len(winnerSqlStuffInst.rows))   
                continue
            # get the going
            try:
                anInput[4] = normaliseGoing(getGoing(horseInfo[8]), meanStdGoingList)
            except TypeError:
                print "skipping horse %d of %d  with no going" % (idx, len(winnerSqlStuffInst.rows))
                continue
            # get the race length
            try:
                anInput[5] = normaliseRaceLengthMinMax(horseInfo[5], minMaxRaceLengthList)
            except:
                print "skipping horse %d of %d  with no length" % (idx, len(winnerSqlStuffInst.rows))
                continue

            # get the output speed
            output = normaliseSpeed(horseInfo, minMaxSpeedList)

            DS.appendLinked(anInput, output) 

        tstdata, trndata = DS.splitWithProportion( 0.25 )
        #trndata=DS
        #tstdata=DS

        # number of hidden layers and nodes

        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer) # 4,10,5,1
        trainer=BackpropTrainer(net,trndata, momentum=0.1, verbose=True, learningrate=0.01)

        aux=trainer.trainUntilConvergence(dataset=DS, maxEpochs=10, verbose=True, continueEpochs=2, validationProportion=0.25)

        mse=trainer.testOnData(dataset=tstdata)
        print "Mean Squared Error = " + str(mse)

        # save the net params
        NetworkWriter.writeToFile(net, netFilename)
    
    neuralNet(net, databaseNames, minMaxDrawList, meanStdGoingList,minMaxRaceLengthList, makeResult = False, date=dateIn)
    
