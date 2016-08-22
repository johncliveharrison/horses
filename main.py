import time
from commands import makeATestcard, makeAResult, makeATestcardFromResults
from neuralnetworks import NeuralNetwork
from pastperf import pastPerf
import sys
from common import Tee
from common import daterange
import datetime
from sqlstuff2 import SqlStuff2

from pybrain.utilities import percentError
from neuralnetworkstuff import NeuralNetworkStuff
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import SigmoidLayer

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
        elif decimal1 < decimal0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif idx == (iterations-1):
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))

    return sortDecimal, sortList, sortHorse



def neuralNet(horseLimit, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d"), number=1, quickTest = 0):
    horseName=[]
    jockeyName=[]
    lengths=[]
    draws=[]
    
    in_loop = True
    #while in_loop == True:
    #    horseName.append(raw_input("Horse name?"))
    #    jockeyName.append(raw_input("Jockey name?"))
    #    again = raw_input("exit loop y/n?")
    #    if again == 'y':
    #        in_loop=False
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
    #numberHorses=raw_input("Number of Horses?")
    #raceLength=raw_input("race length?")
    #for ii in range(0,startRace):
    #    horses.pop(ii)
    #    jockeys.pop(ii)
    #    lengths.pop(ii)
    #    print "remove race" + str(ii) + "from list"
  

    moneypot=0.0
    venuesRaceNo=0
    venueNumber=0
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
                break;
        for idx, horse in enumerate(race):
            errors=0
            yValues=0
            bO=0
            if skipFileWrite==1:
                break;
            if len(race) > 9:
                skipFileWrite=1
                break;
            sqlhorses=SqlStuffInst.getHorse(horse)
            NeuralNetworkStuffInst=NeuralNetworkStuff()
            sortedHorses=NeuralNetworkStuffInst.subSortReduce(sqlhorses, int(horseLimit), date, lengths[raceNo])
            #print str(sortedHorses)
            allInputs=NeuralNetworkStuffInst.subNormaliseInputs(sortedHorses, date)
            usefulInputs, usefulHorses=NeuralNetworkStuffInst.subUsefuliseInputs(allInputs, sortedHorses)

            if usefulInputs != 0:
                usefulInputs=NeuralNetworkStuffInst.subNormaliseInputs(usefulHorses, date)

                DS = SupervisedDataSet(6, 1)
                # go around the loop of useful races to find the finish times and distances
                # need to find the fastest and the slowest for the normalisation
                minpace=1000.00
                maxpace=0.00
                racepace=[0.0]*len(usefulHorses)
                for resultNo, inputs in enumerate(usefulHorses):
                    racepace[resultNo] = (NeuralNetworkStuffInst.convertRaceLengthMetres(inputs[5])/(inputs[15]+(inputs[4]*0.1)))
                    maxpace=max(racepace[resultNo], maxpace)
                    minpace=min(racepace[resultNo], minpace)
                
                for resultNo, inputs in enumerate(usefulInputs):
                    #normalisedOutput = ((float(usefulHorses[resultNo][4])-1)/(float(usefulHorses[resultNo][6])-1))*(1-0)+0
                    # Try calculating the average speed in each race and use that as the output after normalisation
                    #normalisedOutput = ((racepace[resultNo]-minpace)/(maxpace-minpace))*(1-0)+0
                    #print str(usefulHorses[resultNo])
                    #print str(inputs)
                    DS.appendLinked(inputs, racepace[resultNo]) #normalisedOutput) #usefulHorses[resultNo][4]) #
        
                    #tstdata, trndata = DS.splitWithProportion( 0.25 )

                net=buildNetwork(6,8,1, bias=True) #, outclass=SigmoidLayer)

                trainer=BackpropTrainer(net,DS, momentum=0.3, learningrate=0.3)
                mintesterr=0
                for jj in range(0, 100):
                    prevtesterr=mintesterr
                    mintesterr=0
                    for ii in range(0, 500):
                        aux=trainer.train() #UntilConvergence(dataset=DS)

                    # test to see how the trained net performs on some of the training data
                    for testrace in range(0, len(DS)-1):
                        result=net.activate(DS['input'][testrace])
                        testerr = abs(result-DS['target'][testrace])
                        mintesterr = testerr**2 +  mintesterr
                    mintesterr = mintesterr**0.5
                    if mintesterr==prevtesterr:
                        if mintesterr > 0.01:
                            print "randomzing weights"
                            net.randomize()
                   
                    if mintesterr <= 0.01:
                        break;
                # print out the weight from the NN
                #for mod in net.modules:
                #    for conn in net.connections[mod]:
                #        print conn
                #        for cc in range(len(conn.params)):
                #            if abs(conn.params[cc]) < 0.1:
                #                print conn.whichBuffers(cc), conn.params[cc]


                testinput=NeuralNetworkStuffInst.testFunction(jockeys[raceNo][idx],trainers[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx], goings[raceNo], draws[raceNo][idx], date)

                result=net.activate(testinput)
                result = NeuralNetworkStuffInst.convertRaceLengthMetres(lengths[raceNo])/float(result)
                #result=(((result-0)/(1-0))*(maxpace-minpace))+minpace
                sortDecimal, sortList, sortHorse=sortResult(result, str(horse), str(len(DS)), 0, sortList, sortDecimal, sortHorse)
            else:
                skipFileWrite=1

        if skipFileWrite==0:
            
            returnSortHorse.append(sortHorse)

            if sortHorse[0]==todaysResults[raceNo].horseNames[0]:
                odd_split=todaysResults[raceNo].odds[0].split("/")
                moneypot=moneypot+((float(odd_split[0])/float(odd_split[1]))*10)
            else:
                moneypot=moneypot-10.0

            print "The moneypot so far is " + str(moneypot) + "kr"
            
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

        venuesRaceNo+=1
        if venuesRaceNo==len(todaysRaceTimes[venueNumber]):
            venuesRaceNo=0
            venueNumber+=1
        
       
    return returnSortHorse, returnResults

def runNeuralNet(date, number=1, horseLimit=20):
    """ date is the date to use.  Number is the number of times to train the neural net (different
    weightings each time may give varying results). HorseLimit is the number of past results to 
    include in the training"""

    """make a string that will be appended to the results filename"""
    horseLimitStr = "horseLimit"

    """ The noResult string means that the actual result of the race will not be included in 
    the output file or stdout (usually used when predicting a result before the race"""
    neuralNet(horseLimit, horseLimitStr, "noResult", date, number)



def runTestDateRange(dateStart, dateEnd, number=1):
    """ run neuralNet for this daterange.  Get the actual results.  Compare them
    How many times did the winner win, second place win and third place win.  If 
    we add faveourite to the database then we can see how often the favorite wins
    and also use this as a parameter to the neuralNet"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')


    predictedWinner=[]
    numberOfRacesArray=[]
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
    
        print date
        winner=[0]*10
        predicteds, actuals = neuralNet("10","testDate", "Result", date, number)
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
            print "predicted position " + str(idx) + " won " + str(win) + " times"
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
            print "number of times predicted place " + str(jdx) + " won was " + str(numWin)

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
