import time
from commands import makeATestcard, makeAResult
from neuralnetworks import NeuralNetwork
from pastperf import pastPerf
import sys
from common import Tee

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



def neuralNet(horseLimit, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d")):
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
    for raceNo, race in enumerate(horses):
        
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        basedOn=[]
        sortList=[]
        sortDecimal=[]
        sortHorse=[]
        for idx, horse in enumerate(race):
            NeuralNetworkInst=NeuralNetwork()
            bO, error = NeuralNetworkInst.NeuralNetwork(horse, int(horseLimit))
            basedOn.append(bO)
            if basedOn[idx] != 0:
                sortDecimal, sortList, sortHorse=sortResult(float(NeuralNetworkInst.testFunction(jockeys[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx], goings[raceNo])), str(horse), str(basedOn[idx]), str(error), sortList, sortDecimal, sortHorse)
            else:
                sortDecimal, sortList, sortHorse=sortResult(float(0.0), str(horse), str(basedOn[idx]), str(error), sortList, sortDecimal, sortHorse);

        pastPerfOrder=pastPerf(sortHorse)
        
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
        venuesRaceNo+=1
        if venuesRaceNo==len(todaysRaceTimes[venueNumber]):
            venuesRaceNo=0
            venueNumber+=1
            #todaysRaceVenues.pop(0)
#' ' + str(splitpos[4]) + ' (' + str(splitpos[1]) + str(splitpos[2]) + str(splitpos[3]) + ')('+str(splitpos[5])+')('+str(splitpos[6])+str(splitpos[7])+')'

        
        #use the original
        sys.stdout = original
        print "This won't appear on file"  # Only on stdout
        f.close()
