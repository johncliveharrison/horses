import time
from commands import makeATestcard, makeAResult, makeATestcardFromResults
from neuralnetworks import NeuralNetwork
from pastperf import pastPerf
import sys
import os.path
from common import Tee
from common import daterange
import datetime
from sqlstuff2 import SqlStuff2

from pybrain.utilities import percentError
from neuralnetworkstuff import NeuralNetworkStuff
from dataprepstuff import dataPrepStuff
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import SigmoidLayer
from pybrain.structure import TanhLayer
from pybrain.structure import LinearLayer
from pybrain.structure import SoftmaxLayer
from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader

def sortResult(decimalResult, horse, basedOn, error, sortList, sortDecimal, sortHorse):
    """ sort the results by date and return the most recent x"""
    if len(sortList)==0:
        sortList.append(str(horse) + '('+str(decimalResult)+')('+str(basedOn)+')')  # appemd the first horse
        sortDecimal.append(decimalResult)
        sortHorse.append(str(horse))
        return sortDecimal, sortList, sortHorse
    
    iterations = len(sortList)
    decimal1=decimalResult
    for idx in range(0, iterations):

        decimal0=sortDecimal[idx]

        if decimal1==0.0:
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))
            break
        elif decimal0==0.0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif decimal1 > decimal0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif idx == (iterations-1):
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))

    return sortDecimal, sortList, sortHorse

#current Error Measure - You could add your own
def SumSquareError(Actual, Desired):
    error = 0.
    for i in range(len(Desired)):
        error = error + ((Actual[i] - Desired[i])**2)
    error = error**0.5
    return error

def neuralNetPrepTrain(databaseNames, date=-1):
    # The first thing that we need to do is get all horses from the database
    horses=[]
    netFilename = "net"
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    NeuralNetworkStuffInst=NeuralNetworkStuff()
    SqlStuffInst=SqlStuff2()
    print "databaseNamesList is " + str(databaseNamesList)
    for databaseName in databaseNamesList:
        print "databaseName is " + str(databaseName)
        SqlStuffInst.connectDatabase(databaseName)
        horses=horses + SqlStuffInst.getAllTable(date=date)#[0:1000]
        netFilename = netFilename + str(databaseName)
    netFilename = netFilename + ".xml"

    dataPrepStuffInst=dataPrepStuff(horses, databaseNamesList)
    #dataPrepStuffInst.subReduce5s()
    # correlation checks
    # is there a correelation between the best jockey and the winner
    #dataPrepStuffInst.getHorsesInRaces()
    #dataPrepStuffInst.correlateJockey()
    #dataPrepStuffInst.correlateTrainer()
    #dataPrepStuffInst.correlateHorse()
    #dataPrepStuffInst.correlateDraw()
    #dataPrepStuffInst.correlateWeight()

    # remove any unwanted entries from the database in memory
    #dataPrepStuffInst.subReduceDraw()
    # next we need to normalise the database in memory
    netInputs=dataPrepStuffInst.subNormaliseInputs()
    netOutputs=dataPrepStuffInst.subNormaliseOutputs()

    #for ii in range(2,10):
    print "create the DS"
    print str(len(netInputs))
    DS = SupervisedDataSet(len(netInputs[0]), 1)
    for resultNo, inputs in enumerate(netInputs):
        DS.appendLinked(inputs, netOutputs[resultNo]) 
        
    #tstdata, trndata = DS.splitWithProportion( 0.25 )
    trndata=DS
    tstdata=DS

    net=buildNetwork(len(trndata['input'][0]), 3, 7, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer) # 4,10,5,1
    trainer=BackpropTrainer(net,trndata, momentum=0.1, verbose=True, learningrate=0.1)
    # number of attempts to get training to converge

    if os.path.exists(netFilename):
        print "found network training file"
        net = NetworkReader.readFrom(netFilename) 
        #break
    else:
        aux=trainer.trainUntilConvergence(dataset=DS, maxEpochs=None, verbose=True, continueEpochs=10, validationProportion=0.25)
    
    mse=trainer.testOnData(dataset=tstdata)
    print "Mean Squared Error = " + str(mse)

    #sys.exit()
    # save the net params
    NetworkWriter.writeToFile(net, netFilename)

    return net, dataPrepStuffInst


def oddsWinningAnalysis(oddsWinnings):
    """group wins and losses by odds and number of horses"""
    winLoseArray=["win","lose"]

    print "in oddsWinningsAnalysis"
    for winLose in winLoseArray:
        for numberOfHorses in range(1,40):
            oddsLessThan2=0
            oddsLessThan5=0
            oddsLessThan10=0
            oddsLessThan20=0
            oddsLessThan40=0
            oddsOther=0
            for oddWinning in oddsWinnings:
                if oddWinning[2]==winLose and oddWinning[0]==numberOfHorses:
                    if oddWinning[1] < 2:
                        oddsLessThan2+=1
                    elif oddWinning[1] < 5:
                        oddsLessThan5+=1
                    elif oddWinning[1] < 10:
                        oddsLessThan10+=1
                    elif oddWinning[1] < 20:
                        oddsLessThan20+=1
                    elif oddWinning[1] < 40:
                        oddsLessThan40+=1
                    else:
                        oddsOther+=1
            print "For " + str(numberOfHorses) + " there were " + str(oddsLessThan2) + " " + winLose + " at oddsLessThan2"
            print "For " + str(numberOfHorses) + " there were " + str(oddsLessThan5) + " " + winLose + " at oddsLessThan5"
            print "For " + str(numberOfHorses) + " there were " + str(oddsLessThan10) + " " + winLose + " at oddsLessThan10"
            print "For " + str(numberOfHorses) + " there were " + str(oddsLessThan20) + " " + winLose + " at oddsLessThan20"
            print "For " + str(numberOfHorses) + " there were " + str(oddsLessThan40) + " " + winLose + " at oddsLessThan40"
            print "For " + str(numberOfHorses) + " there were " + str(oddsOther) + " " + winLose + " at oddsOther"
            


def neuralNet(net, dataPrepStuffInst, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d"), moneystart = 0.0, moneystart2 = 0.0, horseNumberWinnings=[0]*50, oddsWinnings=[]):
    horseName=[]
    jockeyName=[]
    lengths=[]
    draws=[]
    
    in_loop = True


    try:
        if date >= datetime.datetime.today().strftime('%Y-%m-%d'):
            print "trying to make a test card from the days test card as date is today or later"
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
        else:
            print "tring to make a test card from past results"
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues, odds=makeATestcardFromResults(date)
    except Exception:
        print "making a testcard from results failed"

    if afterResult != "noResult":
        todaysResults=makeAResult(date)
    print todaysRaceVenues
    

    moneypot=moneystart
    moneypot2=moneystart2
    horseNumberWinningsLocal=horseNumberWinnings
    returnSortHorse=[]
    returnPastPerf=[]
    returnResults=[]

    for raceNo, race in enumerate(horses):
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        #basedOn=[]
        sortList=[]
        sortDecimal=[]
        sortHorse=[]
        skipFileWrite=0
        # do a quick check on all of the horses in the race
        SqlStuffInst=SqlStuff2()

        if numberHorses>7:
            """if numberHorses<12:
                skipFileWrite=1
                print "skip race as number of horses is " + str(numberHorses)
                continue
            if numberHorses>14:
                skipFileWrite=1
                print "skip race as number of horses is " + str(numberHorses)
                continue
            """

        for idx, horse in enumerate(race):
            #try:
            #    tmp=int(draws[raceNo][idx])+1
            #    # if there is no exception (so there is a draw) then dont't use
            #    print "draw in this race = " + str(draws[raceNo][idx])
            #    skipFileWrite=1
            #    break

            #except Exception, e:
            #    tmp=0
            #    #print "no draw so using race/hor"

            dataPrepHorses=dataPrepStuffInst.getHorse(horse)
            #if len(dataPrepHorses)==0:
            #    skipFileWrite=1
            #    print "horse has no form so skip race"
            #    break;
           
                #skipFileWrite=1
                #print "horse less than 6 races of form so skip race"
                #break;


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
                testinput=dataPrepStuffInst.testFunction(horses[raceNo][idx],jockeys[raceNo][idx],trainers[raceNo][idx], numberHorses, lengths[raceNo], todaysRaceVenues[raceNo], weights[raceNo][idx], goings[raceNo], draws[raceNo][idx], date)

                result=net.activate(testinput)

                sortDecimal, sortList, sortHorse=sortResult(result, str(horse), str(0), 0, sortList, sortDecimal, sortHorse)
            
            except Exception, e:
                print "something not correct in testFunction"
                #skipFileWrite=1

        if skipFileWrite==0:
            
            returnSortHorse.append(sortHorse)
            if len(sortHorse) > 0 and afterResult !="noResult":

                if sortHorse[0]==todaysResults[raceNo].horseNames[0]:

                    try:
                        odd_split=todaysResults[raceNo].odds[0].split("/")
                        moneypot=moneypot+((float(odd_split[0])/float(odd_split[1]))*10)
                        horseNumberWinningsLocal[len(sortHorse)]+=((float(odd_split[0])/float(odd_split[1]))*10)
                        odds=float(odd_split[0])/float(odd_split[1])
                        oddsWinnings.append([len(sortHorse),odds,"win"])
                        
                        #break
                    except ValueError:
                        print str(todaysResults[raceNo].odds[0]) + " odds were not split properly"
                    except Exception:
                        print str(todaysResults[raceNo].odds[0]) + " odds were not split properly but not ValueError"
                else:
                    moneypot=moneypot-10.0
                    horseNumberWinningsLocal[len(sortHorse)]-=10
                    try:
                        # find the odds of the horse that we bet on so that it can be added to
                        # the correct oddsWinnings entry
                        for idx, resultHorseName in enumerate(todaysResults[raceNo].horseNames):
                            if sortHorse[0]==resultHorseName:
                                odd_split=todaysResults[raceNo].odds[idx].split("/")
                                odds=float(odd_split[0])/float(odd_split[1])
                                oddsWinnings.append([len(sortHorse),odds,"lose"])
                    except Exception:
                        print str(todaysResults[raceNo].odds[0]) + " odds were not split properly"

            temp=0.0
            temp2=0.0
            if len(sortHorse) > 1 and afterResult != "noResult":
                # go through the results to find the odds for our predicted winner
                for idx, idxHorse in enumerate(todaysResults[raceNo].horseNames):
                    if sortHorse[0]==idxHorse:

                        odd_split=todaysResults[raceNo].odds[idx].split("/")

                        try:
                            temp=float(odd_split[0])/float(odd_split[1])
                       
                        except ValueError:
                            print str(todaysResults[raceNo].odds[idx]) + " odds were not split properly"
                        except Exception:
                            print str(todaysResults[raceNo].odds[idx]) + " odds were not split properly but not ValueError"
                    
                if temp >= 2:
                    if sortHorse[0]==todaysResults[raceNo].horseNames[0]:
                        moneypot2=moneypot2+(temp*10)
                    else:
                        moneypot2=moneypot2-10;
                    if sortHorse[0]==todaysResults[raceNo].horseNames[1]:
                        temp=temp/2
                        moneypot2=moneypot2+(temp*10)
                    else:
                        moneypot2=moneypot2-10;
                else:
                    print "No bet for moneypot2"


            print "The moneypot so far is " + str(moneypot) + "kr"
            print "The moneypot2 so far is " + str(moneypot2) + "kr"
            for ii, hnwl in enumerate(horseNumberWinningsLocal):
                print "The winnings from races with " + str(ii) + " horses is " + str(hnwl) + " kr"
            
            if afterResult != "noResult":
                returnResults.append(todaysResults[raceNo])

            # print sortList
            #position.sort()
            f = open("results/"+str(date)+str(filenameAppend),'a')
            original = sys.stdout
            sys.stdout = Tee(sys.stdout, f)
            
            print str(raceNo) + ' ' + str(todaysRaceVenues[raceNo]) + ' ' + str(todaysRaceTimes[raceNo]) 
            for ii, pos in enumerate(sortList):
                #splitpos=re.split(r'(\d+)', pos)
                try:
                    if afterResult == "noResult":
                        print str(ii+1) + pos 
                    else:
                        print str(ii+1) + pos + '       ' + str(todaysResults[raceNo].horseNames[ii]) + ' ' + str(todaysResults[raceNo].odds[ii])
                except IndexError:
                    """if there are none finishers this will be the exception"""
            #use the original
            sys.stdout = original
            print "This won't appear on file"  # Only on stdout
            f.close()

    return returnSortHorse, returnResults, moneypot, moneypot2, horseNumberWinningsLocal, oddsWinnings

def runNeuralNet(date, databaseNames, number=1, horseLimit=20):
    """ date is the date to use.  Number is the number of times to train the neural net (different
    weightings each time may give varying results). HorseLimit is the number of past results to 
    include in the training"""

    """make a string that will be appended to the results filename"""
    horseLimitStr = "horseLimit"

    """ The noResult string means that the actual result of the race will not be included in 
    the output file or stdout (usually used when predicting a result before the race"""
    net, dataPrepStuffInst=neuralNetPrepTrain(databaseNames)

    #net=0
    #dataPrepStuffInst=0
    neuralNet(net, dataPrepStuffInst, horseLimitStr, "noResult", date)
    

def runTestDateRange(dateStart, dateEnd, databaseNames, hiddenExplore=1):
    """ run neuralNet for this daterange.  Get the actual results.  Compare them
    How many times did the winner win, second place win and third place win.  If 
    we add faveourite to the database then we can see how often the favorite wins
    and also use this as a parameter to the neuralNet"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    moneypot = 0.0
    moneypot2 = 0.0

    horseNumbers=[0]*50
    horseNumbersWins=[0]*50
    horseNumberWinnings=[0]*50
    oddsWinnings=[]

    predictedWinner=[]
    numberOfRacesArray=[]

    net, dataPrepStuffInst=neuralNetPrepTrain(databaseNames, dateStart)

    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):

        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
        print date
        winner=[0]*10
        predicteds, actuals, moneypot, moneypot2, horseNumberWinnings, oddsWinnings = neuralNet(net, dataPrepStuffInst, "testDate", "Result", date, moneystart=moneypot, moneystart2=moneypot2, horseNumberWinnings=horseNumberWinnings, oddsWinnings=oddsWinnings)
        numberOfRaces=len(predicteds)
        for idx, predicted in enumerate(predicteds):
            horseNumbers[len(predicted)]+=1
            if predicted[0]==actuals[idx].horseNames[0]:
                horseNumbersWins[len(predicted)]+=1

            for jdx, predict in enumerate(predicted):
                try:
                    if predict == actuals[idx].horseNames[0]:
                        #this means the predicted winner was the winner
                        winner[jdx]+=1

                except IndexError:
                    """ this will happen if there were not at least three horses"""
        
        for idx, win in enumerate(winner):
            print "predicted position " + str(idx+1) + " won " + str(win) + " times"
            print "numberOfRaces = " + str(numberOfRaces)
        
        predictedWinner.append(winner)
        numberOfRacesArray.append(numberOfRaces)


    print "final summary"
    ref=0
    for idx, single_date in enumerate(daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2])))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
        print date
        print "idx = " + str(idx)
        print "number of races = " + str(numberOfRacesArray[ref])
        for jdx, numWin in enumerate(predictedWinner[ref]):
            print "number of times predicted place " + str(jdx+1) + " won was " + str(numWin)

        ref+=1

    print "final final summary"
    for ii in range(0,len(horseNumbers)):
        print "There were " + str(horseNumbers[ii]) + "races with " + str(ii) + " horses, and we won " + str(horseNumbersWins[ii])

    oddsWinningAnalysis(oddsWinnings)

def runTestHistoryRange(historyStart, historyEnd, date):
    """ run neuralNet for this range of previous results.  Get the actual results.  Compare them
    How many times did the winner win, second place win and third place win.  If 
    we add faveourite to the database then we can see how often the favorite wins
    and also use this as a parameter to the neuralNet"""
  
    for historyNum in range(historyStart, historyEnd):
        print historyNum
        winnerWon=0
        secondWon=0
        thirdWon=0

        predicteds, actuals, pastperfs = neuralNet(str(historyNum),"testDate", "Result", date)
        numberOfRaces=len(predicteds)
        for idx, predicted in enumerate(predicteds):
            try:
                if predicted[0] == actuals[idx].horseNames[0]:
                    #this means the predicted winner was the winner
                    winnerWon+=1
                    
                if predicted[1] == actuals[idx].horseNames[0]:
                    #this means the predicted second place horse won
                    secondWon+=1

                if predicted[2] == actuals[idx].horseNames[0]:
                    #this means the predicted third place horse won
                    thirdWon+=1
            except IndexError:
                """ this will happen if there were not at least three horses"""
        print "winnerWon = " + str(winnerWon)
        print "secondWon = " + str(secondWon)
        print "thirdWon = " + str(thirdWon)
        print "numberOfRaces = " + str(numberOfRaces)

        winnerWon=0
        secondWon=0
        thirdWon=0

        for idx, pastperf in enumerate(pastperfs):
            try:
                if pastperf[0] == actuals[idx].horseNames[0]:
                    #this means the predicted winner was the winner
                    winnerWon+=1
                    
                if pastperf[1] == actuals[idx].horseNames[0]:
                    #this means the predicted second place horse won
                    secondWon+=1

                if pastperf[2] == actuals[idx].horseNames[0]:
                    #this means the predicted third place horse won
                    thirdWon+=1
            except IndexError:
                """ this will happen if there were not at least three horses"""
        print "pastperf winnerWon = " + str(winnerWon)
        print "pastperf secondWon = " + str(secondWon)
        print "pastperf thirdWon = " + str(thirdWon)
        print "numberOfRaces = " + str(numberOfRaces)
