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

def neuralNet(horseLimit, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d"), number=1, quickTest = 0, moneystart = 0.0, moneystart2 = 0.0, numH0=2, numH1=0):
    horseName=[]
    jockeyName=[]
    lengths=[]
    draws=[]
    
    in_loop = True

    # The first thing that we need to do is get all winners from the database
    NeuralNetworkStuffInst=NeuralNetworkStuff()
    SqlStuffInst=SqlStuff2()

    horses=SqlStuffInst.getAllTable()#[0:1000]
    dataPrepStuffInst=dataPrepStuff(horses)
    # correlation checks
    # is there a correelation between the best jockey and the winner
    #dataPrepStuffInst.getHorsesInRaces()
    #dataPrepStuffInst.correlateJockey()
    #dataPrepStuffInst.correlateTrainer()
    #dataPrepStuffInst.correlateDraw()

    # next we need to get the inputs from the database
    netInputs=dataPrepStuffInst.subNormaliseInputs()
    netOutputs=dataPrepStuffInst.subNormaliseOutputs()

    print "create the DS"
    DS = SupervisedDataSet(len(netInputs[0]), 1)
    for resultNo, inputs in enumerate(netInputs):
        print str(resultNo)
        print str(inputs)
        print str(netOutputs[resultNo])
        DS.appendLinked(inputs, netOutputs[resultNo]) 

    tstdata, trndata = DS.splitWithProportion( 0.25 )
    net=buildNetwork(len(trndata['input'][0]), 10, 5, 1, bias=True, outclass=SigmoidLayer)#, hiddenclass=LinearLayer) 
    trainer=BackpropTrainer(net,trndata, momentum=0.1, verbose=True, learningrate=0.3)
    nonconvergence=0
    # number of attempts to get training to converge
    for jj in range(0, 100):
        if os.path.exists('filename.xml'):
            print "found network training file"
            net = NetworkReader.readFrom('filename.xml') 
            break

        trnresult = SumSquareError(net.activateOnDataset(dataset=trndata), trndata['target'])
        tstresult = SumSquareError(net.activateOnDataset(dataset=tstdata), tstdata['target'])
        print "training iteration " + str(jj*10)

        # number of iterations in the training        
        trained=False
        for ii in range(0, 10):
            aux=trainer.train() #UntilConvergence(dataset=DS)
            if trnresult < 0.001 and tstresult < 0.001:
                print net
                print net.params
                params = net.params
                print "training successful"
                trained=True
                break;
                
            if  jj > 15:
                print "skip race due to inablility to converge during training"
                skipFileWrite=1
                trained=True
                break
        if trained:
            break

    # save the net params
    NetworkWriter.writeToFile(net, 'filename.xml')

    try:
        horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
    except AttributeError:
        try:
            horses, jockeys, lengths, weights, goings, draws, trainers, todaysRaceTimes, todaysRaceVenues, odds=makeATestcardFromResults(date)
        except AttributeError:
            print "making a testcard from results failed"

    if afterResult != "noResult":
        todaysResults=makeAResult(date)
    print todaysRaceVenues
    

    moneypot=moneystart
    moneypot2=moneystart2
    returnSortHorse=[]
    returnPastPerf=[]
    returnResults=[]

    if quickTest == 1:
        horses=horses[0]

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

        for idx, horse in enumerate(race):
            sqlhorses=SqlStuffInst.getHorse(horse)
            if len(sqlhorses)==0:
                skipFileWrite=1
                print "horse has no form so skip race"
                break;

            #if len(sqlhorses)<6:
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
               
            testinput=dataPrepStuffInst.testFunction(jockeys[raceNo][idx],trainers[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx], goings[raceNo], draws[raceNo][idx], date)

            result=net.activate(testinput)
            #cummulativeResult = (cummulativeResult+result)
            #averageResult = cummulativeResult/kk
            #print "The average result for " + str(horse) + " is " + str(averageResult)

            sortDecimal, sortList, sortHorse=sortResult(result, str(horse), str(0), 0, sortList, sortDecimal, sortHorse)
            
        if skipFileWrite==0:
            
            returnSortHorse.append(sortHorse)
            if len(sortHorse) > 0 and afterResult !="noResult":

                if sortHorse[0]==todaysResults[raceNo].horseNames[0]:

                    odd_split=todaysResults[raceNo].odds[0].split("/")

                    try:

                        moneypot=moneypot+((float(odd_split[0])/float(odd_split[1]))*10)

                        #break
                    except ValueError:
                        print str(todaysResults[raceNo].odds[0]) + " odds were not split properly"
                    except Exception:
                        print str(todaysResults[raceNo].odds[0]) + " odds were not split properly but not ValueError"
                else:
                    moneypot=moneypot-10.0

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

    return returnSortHorse, returnResults, moneypot, moneypot2

def runNeuralNet(date, number=1, horseLimit=20):
    """ date is the date to use.  Number is the number of times to train the neural net (different
    weightings each time may give varying results). HorseLimit is the number of past results to 
    include in the training"""

    """make a string that will be appended to the results filename"""
    horseLimitStr = "horseLimit"

    """ The noResult string means that the actual result of the race will not be included in 
    the output file or stdout (usually used when predicting a result before the race"""
    neuralNet(horseLimit, horseLimitStr, "Result", date, number)



def runTestDateRange(dateStart, dateEnd, number=1, hiddenExplore=1):
    """ run neuralNet for this daterange.  Get the actual results.  Compare them
    How many times did the winner win, second place win and third place win.  If 
    we add faveourite to the database then we can see how often the favorite wins
    and also use this as a parameter to the neuralNet"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    moneypot = 0.0
    moneypot2 = 0.0

    predictedWinner=[]
    numberOfRacesArray=[]
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):

        for hiddenCount in range(1, hiddenExplore):
            # remove these when doing more than one date.
            predictedWinner=[]
            numberOfRacesArray=[]
            moneypot = 0.0
            moneypot2 = 0.0

            numH0 = hiddenCount%10
            if numH0 > 0:
                print "Hidden layer 0 = " + str(numH0)
                numH1 = int(hiddenCount/10)
                if numH1 > 0:
                    print "Hidden layer 1 = " + str(numH1)
                date=time.strftime("%Y-%m-%d", single_date.timetuple())       
    
                print date
                winner=[0]*10
                predicteds, actuals, moneypot, moneypot2 = neuralNet("20","testDate", "Result", date, number, moneystart=moneypot, moneystart2=moneypot2, numH0=numH0, numH1=numH1)
                numberOfRaces=len(predicteds)
                for idx, predicted in enumerate(predicteds):
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
            print "numH0 is " + str(numH0)
            print "numH1 is " + str(numH1)
            ref=0
            for idx, single_date in enumerate(daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2])))):
                date=time.strftime("%Y-%m-%d", single_date.timetuple())       
                print date
                print "idx = " + str(idx)
                print "number of races = " + str(numberOfRacesArray[ref])
                for jdx, numWin in enumerate(predictedWinner[ref]):
                    print "number of times predicted place " + str(jdx+1) + " won was " + str(numWin)

                ref+=1

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
