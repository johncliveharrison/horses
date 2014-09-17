import time
from commands import makeATestcard, makeAResult
from neuralnetworks import NeuralNetwork
from pastperf import pastPerf
import sys
from common import Tee
from common import daterange
import datetime

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



def neuralNet(horseLimit, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d"), number=1):
    horseName=[]
    jockeyName=[]
    lengths=[]
    
    in_loop = True
    #while in_loop == True:
    #    horseName.append(raw_input("Horse name?"))
    #    jockeyName.append(raw_input("Jockey name?"))
    #    again = raw_input("exit loop y/n?")
    #    if again == 'y':
    #        in_loop=False
    horses, jockeys, lengths, weights, goings, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
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
    for raceNo, race in enumerate(horses):
        
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        #basedOn=[]
        sortList=[]
        sortDecimal=[]
        sortHorse=[]
        skipFileWrite=0
        for idx, horse in enumerate(race):
            errors=0
            yValues=0
            bO=0
            if len(race) > 9:
                skipFileWrite=1
                break;
            
            for ii in range(0, number):
                NeuralNetworkInst=NeuralNetwork()
                bO, error = NeuralNetworkInst.NeuralNetwork(horse, int(horseLimit))
                errors+=error
                if bO != 0:
                    yValues+=float(NeuralNetworkInst.testFunction(jockeys[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx], goings[raceNo]))
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
#    for idx in range (0, number):
    horseLimitStr = "horseLimit"#+str(idx)
    neuralNet(horseLimit, horseLimitStr, "noResult", date, number)



def runTestDateRange(dateStart, dateEnd):
    """ run neuralNet for this daterange.  Get the actual results.  Compare them
    How many times did the winner win, second place win and third place win.  If 
    we add faveourite to the database then we can see how often the favorite wins
    and also use this as a parameter to the neuralNet"""
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')

    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
    
        print date
        winnerWon=0
        secondWon=0
        thirdWon=0

        predicteds, actuals, pastperfs = neuralNet("20","testDate", "Result", date)
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
