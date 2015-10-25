import time
from commands import makeATestcard, makeAResult, makeATestcardFromResults
from neuralnetworks import NeuralNetwork
from pastperf import pastPerf
import sys
from common import Tee
from common import daterange
import datetime
from sqlstuff2 import SqlStuff2


def sortResult(decimalResult, horse, basedOn, error, sortList, sortDecimal, sortHorse):
    """ sort the results by date and return the most recent x"""
    if len(sortList)==0:
        sortList.append(str(horse) + '('+str(decimalResult)+')('+str(basedOn)+')('+str(error)+')')  # appemd the first horse
        sortDecimal.append(decimalResult)
        sortHorse.append(str(horse))
        return sortDecimal, sortList, sortHorse
    
    iterations = len(sortList)
    decimal1=decimalResult
    for idx in range(0, iterations):

        decimal0=sortDecimal[idx]

        if decimal1==0.0:
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.append(decimal1)
            sortHorse.append(str(horse))
            break
        elif decimal0==0.0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif decimal1 < decimal0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.insert(idx,decimal1)
            sortHorse.insert(idx,str(horse))
            break
        elif idx == (iterations-1):
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
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
            horses, jockeys, lengths, weights, goings, draws, todaysRaceTimes, todaysRaceVenues=makeATestcardFromResults(date)
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
            for ii in range(0, number):
                NeuralNetworkInst=NeuralNetwork()
                """train a network for this horse, based on horseLimit number of past performances"""
                bO, error = NeuralNetworkInst.NeuralNetwork(horse, int(horseLimit), date, lengths[raceNo])
                errors+=error
                if bO != 0:
                    """see how the trained neural network performs under this races 'test' conditions"""
                    yValues+=float(NeuralNetworkInst.testFunction(jockeys[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx], goings[raceNo], draws[raceNo][idx]))#, trainers[raceNo][idx]))
                else:
                    break
            if bO != 0:    
                yValuePos=yValues/number
                averageError=errors/number
                sortDecimal, sortList, sortHorse=sortResult(yValuePos, str(horse), str(bO), str(averageError), sortList, sortDecimal, sortHorse)
            else:
                skipFileWrite=1
                break;

        if skipFileWrite==0:
            pastPerfOrder=pastPerf(sortHorse)
            returnSortHorse.append(sortHorse)
            returnPastPerf.append(pastPerfOrder)
            if afterResult != "noResult":
                returnResults.append(todaysResults[raceNo])

            # print sortList
            #position.sort()
            f = open("results/"+str(date)+str(filenameAppend),'a')
            original = sys.stdout
            sys.stdout = Tee(sys.stdout, f)
            
            print str(raceNo) + ' ' + str(todaysRaceVenues[venueNumber]) + ' ' + str(todaysRaceTimes[venueNumber][venuesRaceNo]) 
            for ii, pos in enumerate(sortList):
                #splitpos=re.split(r'(\d+)', pos)
                try:
                    if afterResult == "noResult":
                        print str(ii+1) + pos + '         '  + str(pastPerfOrder[ii])
                    else:
                        print str(ii+1) + pos + '       ' + str(pastPerfOrder[ii]) + '           ' + str(todaysResults[raceNo].horseNames[ii])
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
        
       
    return returnSortHorse, returnResults, returnPastPerf

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
    pastperfWinner=[]
    numberOfRacesArray=[]
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
    
        print date
        winner=[0]*10
        predicteds, actuals, pastperfs = neuralNet("5","testDate", "Result", date, number)
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
        winner=[0]*10


        for idx, pastperf in enumerate(pastperfs):
            for jdx, predict in enumerate(pastperf):
                try:
                    if predict == actuals[idx].horseNames[0]:
                        #this means the predicted winner was the winner
                        winner[jdx]+=1

                except IndexError:
                    """ this will happen if there were not at least three horses"""
        
        for idx, win in enumerate(winner):
            print "predicted position " + str(idx) + " won " + str(win) + " times"
        print "numberOfRaces = " + str(numberOfRaces)

        pastperfWinner.append(winner)
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
        for jdx, numWin in enumerate(pastperfWinner[ref]):
            print "number of times pastperf place " + str(jdx) + " won was " + str(numWin)

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
