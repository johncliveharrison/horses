from itertools import chain 
from collections import Counter
import datetime
import re
import os
import sys
import pickle
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import SigmoidLayer
from pybrain.structure import TanhLayer
from pybrain.structure import LinearLayer
from pybrain.structure import SoftmaxLayer
from sqlstuff2 import SqlStuff2
from minmax import meansJockeyTrainer
from minmax import minMaxRaceLength
from minmax import normaliseFinish
from minmax import minMaxWeight
from minmax import minMaxJockeyTrainer
from minmax import minMaxRest
from minmax import normaliseRestDays

def getTraining(databaseNames, verbose = True):
    """ check that all criteria are met for this horse to be included in training
    and if they are finally check if there is a draw or not and save the horse in
    a database for use in the training"""

    
    # create a db for the previous results of races called previousResults
    #previousResultsSqlStuffInst=SqlStuff2()
    #previousResultsStuffInst.connectDatabase(previousResults)
    #previousResultsStuffInst.createResultTable()

    pastPerf = 0
    badDraw = 0
    badGoing = 0
    badRaceLength = 0
    badWeight = 0
    badJockey = 0
    badTrainer = 0
    badOdds = 0
    badOutput = 0
    badRest = 0

    raceVenue = ""
    raceDate = ""
    raceTime = ""
    anInput = [None] * 10
    DSDraw = SupervisedDataSet(len(anInput), 1)
    DsNoDraw = SupervisedDataSet(len(anInput), 1)
    rows = []
    previousResultsFilename = "previousResults.dict"
    previousResultsDict = {}
    databaseNamesList=map(str, databaseNames.strip('[]').split(','))
    SqlStuffInst=SqlStuff2()

    """unpickler = pickle.Unpickler(open(previousResultsFilename+"_tmp"))
    try:
        unpickler.load()
    except EOFError:
        pass
        
    picklestack = unpickler.stack
    del picklestack[-18:-1]

    previousResultsDict = picklestack[0]
    with open(previousResultsFilename+"_tmp", 'wb') as fp:
        pickle.dump(previousResultsDict, fp)
        fp.close()

    sys.exit()"""




    # check to see if there is a partial dict of previous results
    if os.path.exists(previousResultsFilename+"_tmp"):
        print "reading a partial previousResults file file %s " % (previousResultsFilename+"_tmp")
        with open (previousResultsFilename+"_tmp", 'rb') as fp:
            previousResultsDict= pickle.load(fp)
            fp.close()
        
    print "databaseNamesList is " + str(databaseNamesList)
    for databaseName in databaseNamesList:
        SqlStuffInst.connectDatabase(databaseName)
        # get all the rows in this database
        SqlStuffInst.getAllTable()
        rows = rows + SqlStuffInst.rows

    newHorse=False
    for idx, horseInfo in enumerate(rows):
        horseName=horseInfo[1]
        if idx%100==0 and newHorse==True:
            newHorse=False
            print "horse entry %d of %d" % (idx, len(rows))
            with open(previousResultsFilename+"_tmp", 'wb') as fp:
                pickle.dump(previousResultsDict, fp)

        if horseName in previousResultsDict:
            print "%d %s already in dict" % (idx, horseName)
            continue
        else:
            horseList=[]
            for row in rows:
                if horseName in row:
                    horseList.append(row)
            previousResultsDict[horseName] = horseList
            newHorse=True
    with open(previousResultsFilename, 'wb') as fp:
        pickle.dump(previousResultsDict, fp)

    # load or create the jockey and trainer dictionaries 
    jockeyDict=meansJockeyTrainer(rows, databaseNamesList,jockeyTrainer="jockey")
    trainerDict=meansJockeyTrainer(rows, databaseNamesList,jockeyTrainer="trainer")
    minMaxRaceLengthList = minMaxRaceLength(rows)


    for idx, horseInfo in enumerate(rows):
        date=horseInfo[9]
        horseName= horseInfo[1]
        horseList= []
        print "horse entry %d of %d" % (idx, len(rows))
        #check if horseName is already in the previousResultsDict
        if horseName not in previousResultsDict:
            sys.exit()
        else:
            print "horse is already in dict"
            horseList = previousResultsDict[horseName]
        #The horse should now be in previous results dict.  Check if 3 of them
        # were before the date of this race
        previousHorse = []
        for horse in horseList:
            if horse[9] < date:
                previousHorse.append(horse)
            else:
                break
        if len(previousHorse) < 3:
            print "horse did not have 3 previous races"
            continue

        try:
            anInput[0] = normaliseFinish(previousHorse[-1][4],previousHorse[-1][6])
            anInput[1] = normaliseFinish(previousHorse[-2][4],previousHorse[-2][6])
            anInput[2] = normaliseFinish(previousHorse[-3][4],previousHorse[-3][6])
            if verbose:
                #print str(previousHorse)
                print "horseName %s - dates %s   %s   %s" % (str(previousHorse[-1][1]), str(previousHorse[-1][9]), str(previousHorse[-2][9]), str(previousHorse[-3][9]))
        except Exception,e:
            print "skipping horse %d of %d  with bad form" % (idx, len(rows))
            print str(e)
            pastPerf = pastPerf + 1
            continue

        # in order to get the mixmax lists required for the other inputs the
        # race is required
        print "horseInfo[11] = %s and raceVenue = %s" % (str(horseInfo[11]), str(raceVenue))
        if horseInfo[11] != raceVenue or horseInfo[9] != raceDate or horseInfo[10] != raceTime:
            skipRace=False
            raceHorseList = []
            raceVenue=horseInfo[11]#re.sub('[\W_]+', '', horseInfo[11])
            raceDate=horseInfo[9]
            raceTime=horseInfo[10]

            for databaseName in databaseNamesList:
                SqlStuffInst.connectDatabase(databaseName)
                raceHorseList=raceHorseList + SqlStuffInst.getRace(raceVenue, raceDate, raceTime)

            # check that all the horses in this race have run at least 3 races
            # and that those races are in the dict.  If this is not the case
            # then miss this
            for raceHorse in raceHorseList:
                prevRaceFound=False
                horseList=previousResultsDict[raceHorse[1]]
                for horse in horseList:
                    if horse[9] < raceDate:
                        prevRaceFound=True
                        continue
                if not prevRaceFound:
                    skipRace=True
                    break

            if skipRace:
                print "aborting race as not all horse have 3 previous races"
                continue

            minMaxWeightList = minMaxWeight(raceHorseList)
            minMaxJockeyList = minMaxJockeyTrainer(jockeyDict, raceHorseList)
            minMaxTrainerList = minMaxJockeyTrainer(trainerDict, raceHorseList,jockeyTrainer="Trainer")
            minMaxRestList = minMaxRest(raceHorseList, previousResultsDict)

        if skipRace:
            print "aborting race AGAIN as not all horse have 3 previous races"
            continue

        # get the days since last race and normalize from -1 to 1
        try:
            nowDate=datetime.datetime.strptime(horseInfo[9], '%Y-%m-%d').date()
            prevDate= datetime.datetime.strptime(previousHorse[-1][9], '%Y-%m-%d').date()
            rest = (nowDate-prevDate).days
            anInput[3] = normaliseRestDays(rest, minMaxRestList)
        except Exception, e:
            print "problem in normalising rest days for %s" % (str(horseInfo[1]))
            print str(e)
            badRest = badRest + 1
            continue

        # get the race length
        try:
            anInput[5] = normaliseRaceLengthMinMax(horseInfo[5], minMaxRaceLengthList)
        except:
            print "skipping horse %d of %d  with no length" % (idx, len(winnerSqlStuffInst.rows))
            badRaceLength = badRaceLength + 1
            continue

        # normalise the weight relative to other horses in the race
        try:
            anInput[6] = normaliseWeightMinMax(horseInfo[3], minMaxWeightList)
        except Exception, e:
            print str(e)
            print "the weight is " + str(horseInfo[3])
            print "skipping horse %d of %d  with no weight" % (idx, len(winnerSqlStuffInst.rows))
            badWeight = badWeight + 1
            continue

        # normalise the jockey relative to the other jockeys in the race
        try:
            jockeyName=horseInfo[7]
            anInput[7] = normaliseJockeyTrainerMinMax(jockeyDict[jockeyName], minMaxJockeyList)
        except Exception,e:
            print "problem with the jockey normalise"
            print "jockey is %s, median is %s.  Min is %s, max is %s" % (str(jockeyName), str(jockeyDict[jockeyName]),str(minMaxJockeyList[0]), str(minMaxJockeyList[1])) 
            print str(e)
            badJockey = badJockey + 1
            continue

        # normalise the trainer relative to the other trainers in the race
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


        # get the output result (1 for a win 0 for all others)
        try:
            if horseInfo[4] == 1:
                output = 1.0
            else:
                output = 0.0
        except Exception, e:
            print "problem getting output"
            print str(e)
            badOutput = badOutput + 1
            continue


        # get the draw
        try:
            anInput[3] = normaliseDrawMinMax(horseInfo[12],minMaxDrawList)
            DSDraw.appendLinked(anInput, output) 
        except Exception,e:
            anInput[3] = 0.0
            DSNoDraw.appendLinked(anInput, output) 
            print "skipping horse %d of %d  with bad/no draw" % (idx, len(winnerSqlStuffInst.rows))   
            print str(e)
            badDraw = badDraw + 1
            continue


    print "bad past performance = %d" % pastPerf
    print "bad draw = %d" % badDraw
    print "bad going = %d" % badGoing
    print "bad race length = %d" % badRaceLength
    print "bad weight = %d" % badWeight
    print "bad jockey = %d" % badJockey
    print "bad trainer = %d" % badTrainer
    print "bad odds = %d" % badOdds
    print "bad Output = %d" % badOutput

    with open("DSDraw.pk", 'wb') as fp:
        pickle.dump(DSDraw, fp)
    with open("DSNoDraw.pk", 'wb') as fp:
        pickle.dump(DSNoDraw, fp)


    return DSDraw, DSNoDraw

  
def buildNet(hiddenLayers, trndata):

    if hiddenLayer1 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    elif hiddenLayer2 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    elif hiddenLayer3 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    elif hiddenLayer4 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    elif hiddenLayer5 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    elif hiddenLayer6 ==0:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, hiddenLayer5, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
    else:
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, hiddenLayer5, hiddenLayer6, 1, bias=True, outclass=LinearLayer, hiddenclass=TanhLayer)
        
    return net
