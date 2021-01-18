import pandas as pd
import copy
import matplotlib.pyplot as plt
from common import daterange
import time
from pybrain.optimization.populationbased.ga import GA
from pybrain.tools.customxml.networkwriter import NetworkWriter
from pybrain.tools.customxml.networkreader import NetworkReader
from collections import defaultdict
from statistics import mean
from statistics import median
import operator
import makea
import numpy as np
from pybrain.utilities import percentError
from itertools import chain 
from collections import Counter
import datetime
import re
import os
import sys
import pickle
from pybrain.datasets import ClassificationDataSet
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.structure import SigmoidLayer
from pybrain.structure import TanhLayer
from pybrain.structure import LinearLayer
from pybrain.structure import SoftmaxLayer
from pybrain.structure import ReluLayer
from sqlstuff2 import SqlStuff2
from minmax import getGoing
from minmax import meanStdGoing
from minmax import meansJockeyTrainer
from minmax import minMaxRaceLength
from minmax import normaliseFinish
from minmax import minMaxWeight
from minmax import minMaxJockeyTrainer
from minmax import minMaxRest
from minmax import minMaxDraw
from minmax import normaliseGoing
from minmax import normaliseRestDays
from minmax import normaliseRaceLengthMinMax
from minmax import normaliseWeightMinMax
from minmax import normaliseJockeyTrainerMinMax
from minmax import normaliseDrawMinMax
import minmax
import commands

def print_net_connections(n):
    for mod in n.modules:
        for conn in n.connections[mod]:
            print (conn)
            for cc in range(len(conn.params)):
                print (conn.whichBuffers(cc), conn.params[cc])


def getTraining(databaseNames, verbose = False):
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
    anInput = [None] * 12
    DSDraw = SupervisedDataSet(len(anInput), 1)
    DSNoDraw = SupervisedDataSet(len(anInput), 1)
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
    if os.path.exists(previousResultsFilename):
        print ("reading a partial previousResults file file %s " % (previousResultsFilename))
        with open (previousResultsFilename, 'rb') as fp:
            previousResultsDict= pickle.load(fp)
            fp.close()
        
                                               
    print ("databaseNamesList is " + str(databaseNamesList))
    for databaseName in databaseNamesList:
        SqlStuffInst.connectDatabase(databaseName)
        # get all the rows in this database
        SqlStuffInst.getAllTable()
        rows = rows + SqlStuffInst.rows

    newHorse=0
    saveFinalResult=False
    forceNumRows=len(rows)+1
    for idx, horseInfo in enumerate(rows):
        if idx == forceNumRows:
            break
        if idx == len(rows):
            saveFinalResult = True
        horseName=horseInfo[1]
        if newHorse==100:
            newHorse=0
            print ("horse entry %d of %d" % (idx, len(rows)))
            with open(previousResultsFilename+"_tmp", 'wb') as fp:
                pickle.dump(previousResultsDict, fp)

        if horseName in previousResultsDict:
            if verbose:
                print ("%d %s already in dict" % (idx, horseName))
            continue
        else:
            print ("%d %s not in dict" % (idx, horseName))
            horseList=[]
            for row in rows:
                if horseName in row:
                    horseList.append(row)
            previousResultsDict[horseName] = horseList
            newHorse=newHorse+1
    if saveFinalResult:
        with open(previousResultsFilename, 'wb') as fp:
            pickle.dump(previousResultsDict, fp)

    # load or create the jockey and trainer dictionaries 
    jockeyDict=meansJockeyTrainer(rows, databaseNamesList,jockeyTrainer="jockey")
    trainerDict=meansJockeyTrainer(rows, databaseNamesList,jockeyTrainer="trainer")
    minMaxRaceLengthList = minMaxRaceLength(rows)
    meanStdGoingList = meanStdGoing(rows)
    print ("min = %d" % minMaxRaceLengthList[0])
    print ("max = %d" % minMaxRaceLengthList[1])


    for idx, horseInfo in enumerate(rows):
        if idx % 100 == 0:
            print ("idx=%d, DSDraw=%d, DSNoDraw=%d" % (idx, len(DSDraw), len(DSNoDraw)))
        if idx == forceNumRows:
            break


        date=horseInfo[9]
        horseName= horseInfo[1]
        horseList= []
        if verbose:
            print ("horse entry %d of %d" % (idx, len(rows)))
        #check if horseName is already in the previousResultsDict
        if horseName not in previousResultsDict:
            print ("horse %d not in loaded dict - exiting" % idx)
            sys.exit()
        else:
            if verbose:
                print ("horse is already in dict")
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
            if verbose:
                print ("horse did not have 3 previous races")
            continue

        try:
            anInput[0] = normaliseFinish(previousHorse[-1][4],previousHorse[-1][6])
            anInput[1] = normaliseFinish(previousHorse[-2][4],previousHorse[-2][6])
            anInput[2] = normaliseFinish(previousHorse[-3][4],previousHorse[-3][6])
            if verbose:
                print ("horseName %s - dates %s   %s   %s" % (str(previousHorse[-1][1]), str(previousHorse[-1][9]), str(previousHorse[-2][9]), str(previousHorse[-3][9])))
        except Exception as e:
            print ("skipping horse %d of %d  with bad form" % (idx, len(rows)))
            print (str(e))
            pastPerf = pastPerf + 1
            continue

        if verbose:
            print ("horseInfo[11] = %s and raceVenue = %s" % (str(horseInfo[11]), str(raceVenue)))
        # in order to get the mixmax lists required for the other inputs the
        # race is required
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
                if verbose:
                    print ("aborting race as not all horse have 3 previous races")
                continue

            minMaxWeightList = minMaxWeight(raceHorseList)
            minMaxJockeyList = minMaxJockeyTrainer(jockeyDict, raceHorseList)
            minMaxTrainerList = minMaxJockeyTrainer(trainerDict, raceHorseList,jockeyTrainer="Trainer")
            minMaxRestList = minMaxRest(raceHorseList, previousResultsDict)
            minMaxDrawList = minMaxDraw(raceHorseList)

        if skipRace:
            if verbose:
                print ("aborting race AGAIN as not all horse have 3 previous races")
            continue

        # get the days since last race and normalize from -1 to 1
        try:
            nowDate=datetime.datetime.strptime(horseInfo[9], '%Y-%m-%d').date()
            prevDate= datetime.datetime.strptime(previousHorse[-1][9], '%Y-%m-%d').date()
            rest = (nowDate-prevDate).days
            anInput[3] = normaliseRestDays(rest, minMaxRestList)
        except Exception as e:
            print ("problem in normalising rest days for %s" % (str(horseInfo[1])))
            print (str(e))
            badRest = badRest + 1
            continue

        # get the race length
        try:
            if verbose:
                print ("length = %s" % str(horseInfo[5]))
                print ("min = %d" % minMaxRaceLengthList[0])
                print ("max = %d" % minMaxRaceLengthList[1])
            anInput[5] = normaliseRaceLengthMinMax(horseInfo[5], minMaxRaceLengthList)
        except Exception as e:
            print (str(e))
            print (str(horseInfo))
            print ("skipping horse %d of %d  with no length" % (idx, len(rows)))
            badRaceLength = badRaceLength + 1
            continue

        # normalise the weight relative to other horses in the race
        try:
            anInput[6] = normaliseWeightMinMax(horseInfo[3], minMaxWeightList)
        except Exception as e:
            print (str(e))
            print ("the weight is " + str(horseInfo[3]))
            print ("skipping horse %d of %d  with no weight" % (idx, len(rows)))
            badWeight = badWeight + 1
            continue

        # normalise the jockey relative to the other jockeys in the race
        try:
            jockeyName=horseInfo[7]
            anInput[7] = normaliseJockeyTrainerMinMax(jockeyDict[jockeyName], minMaxJockeyList)
        except Exception as e:
            print ("problem with the jockey normalise")
            print ("jockey is %s, median is %s.  Min is %s, max is %s" % (str(jockeyName), str(jockeyDict[jockeyName]),str(minMaxJockeyList[0]), str(minMaxJockeyList[1])) )
            print (str(e))
            badJockey = badJockey + 1
            continue

        # normalise the trainer relative to the other trainers in the race
        try:
            trainerName=horseInfo[13]
            anInput[8] = normaliseJockeyTrainerMinMax(trainerDict[trainerName], minMaxTrainerList)
        except Exception as e:
            print ("problem with the trainer normalise")
            print ("trainer is %s, median is %s.  Min is %s, max is %s" % (str(trainerName), str(trainerDict[trainerName]),str(minMaxTrainerList[0]), str(minMaxTrainerList[1])) )
            print (str(e))
            badTrainer = badTrainer + 1
            continue


        try:
            odds=horseInfo[15]
            anInput[9] = float(odds.split("/")[0])/float(odds.split("/")[1])
        except Exception as e:
            print ("problem with the odds %s" % str(odds))
            print (str(odds.split("/")))
            badOdds = badOdds + 1
            continue


        # the number of horses where the max number of horses where we stop
        # differentiating number of horses is 30
        try:
            anInput[10] = min(1.0, float(horseInfo[6]/30.0))
        except Exception as e:
            print ("problem finding the number of horses in training")
            print (str(e))
            continue

        # get the going
        try:
            anInput[11] = normaliseGoing(getGoing(horseInfo[8]), meanStdGoingList)
        except Exception as e:
            print ("skipping horse %s with no going" % (horseName))
            print (str(e))
            continue



        # get the output result (1 for a win 0 for all others)
        try:
            if horseInfo[4] == 1:
                output = 1.0
            else:
                output = 0.0
        except Exception as e:
            print ("problem getting output")
            print (str(e))
            badOutput = badOutput + 1
            continue


        # get the draw
        try:
            anInput[3], hasDraw = normaliseDrawMinMax(horseInfo[12],minMaxDrawList)
        except Exception as e:
            print ("skipping horse %d of %d  with bad/no draw" % (idx, len(rows))   )
            print (str(e))
            badDraw = badDraw + 1
            continue

        if hasDraw:
            DSDraw.appendLinked(anInput, output)
            print ("normalised draw is %f from draw %s min/max %s/%s" % (anInput[3], str(horseInfo[12]), str(minMaxDrawList[0]), str(minMaxDrawList[1])))
        else:
            DSNoDraw.appendLinked(anInput, output) 
            
    print ("bad past performance = %d" % pastPerf)
    print ("bad draw = %d" % badDraw)
    print ("bad going = %d" % badGoing)
    print ("bad race length = %d" % badRaceLength)
    print ("bad weight = %d" % badWeight)
    print ("bad jockey = %d" % badJockey)
    print ("bad trainer = %d" % badTrainer)
    print ("bad odds = %d" % badOdds)
    print ("bad Output = %d" % badOutput)

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

def get_going_conversion(database="results_2019_2.db" ,year="2019"):
    possibleSurfaces=["Hard", "Firm", "Soft", "Heavy", "Frozen", "Standard", "Fast", "Slow"]
    # Creating an empty dictionary 
    myDict = defaultdict(list)
    myResultDict = defaultdict(list)
  
    date_start = "2019-01-01"
    date_end = "2019-12-31"
    dateStartSplit=date_start.split('-')
    dateEndSplit=date_end.split('-')

    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       
        print (dateIn)
        rows = commands.viewMultiple(database, raceDate=dateIn)
        for row in rows:
            horseName = row[1]
            horseName_rows = commands.viewMultiple(database, horseName=horseName)
            for horseName_row in horseName_rows:
                position = int(horseName_row[4])
                if position == 1:
                    going = horseName_row[8]
                    length = float(minmax.convertRaceLengthMetres(horseName_row[5]))
                    finishTime = float(horseName_row[14])
                    try:
                        speed = length/finishTime
                    except ZeroDivisionError as e:
                        print(e)
                        continue
                    if going == "Good":
                        for compare_horseName_row in horseName_rows:
                            compare_position = int(compare_horseName_row[4])
                            if compare_position == 1:
                                compare_going = compare_horseName_row[8]
                                compare_length = float(minmax.convertRaceLengthMetres(compare_horseName_row[5]))
                                compare_finishTime = float(compare_horseName_row[14])
                                try:
                                    compare_speed = compare_length/compare_finishTime
                                except ZeroDivisionError as e:
                                    print(e)
                                    continue
                                if compare_going != "Good" and compare_length == length:
                                    speed_ratio = speed/compare_speed
                                    myDict[compare_going].append(speed_ratio)
        for key, value in myDict.items():
            print("convert %s to Good, multiply by %f" % (str(key), mean(value)))
            myResultDict[key] = mean(value)

    print (myResultDict)


def get_length_conversion(database="results_2019_2.db" ,year="2019"):

    length_string = "1m"
    # Creating an empty dictionary 
    myDict = defaultdict(list)
    myResultDict = defaultdict(list)
  
    date_start = "2019-01-01"
    date_end = "2019-12-31"
    dateStartSplit=date_start.split('-')
    dateEndSplit=date_end.split('-')

    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       
        print (dateIn)
        rows = commands.viewMultiple(database, raceDate=dateIn)
        for row in rows:
            horseName = row[1]
            horseName_rows = commands.viewMultiple(database, horseName=horseName)
            for horseName_row in horseName_rows:
                position = int(horseName_row[4])
                if position == 1:
                    going = horseName_row[8]
                    length = float(minmax.convertRaceLengthMetres(horseName_row[5]))
                    finishTime = float(horseName_row[14])
                    if horseName_row[5] == length_string:
                        for compare_horseName_row in horseName_rows:
                            compare_position = int(compare_horseName_row[4])
                            if compare_position == 1:
                                compare_going = compare_horseName_row[8]
                                compare_length = float(minmax.convertRaceLengthMetres(compare_horseName_row[5]))
                                compare_finishTime = float(compare_horseName_row[14])
                                if compare_going == going and compare_horseName_row[5] != length_string:
                                    finishTime_ratio = finishTime/compare_finishTime
                                    myDict[compare_horseName_row[5]].append(finishTime_ratio)
        for key, value in myDict.items():
            length_ratio = minmax.convertRaceLengthMetres(length_string)/minmax.convertRaceLengthMetres(str(key))
            print("ratio %s to %s (%f), multiply by %f" % (str(key), length_string, length_ratio, mean(value)))
            myResultDict[key] = mean(value)

    print (myResultDict)


def get_going_as_good(horseName_going, speed, going):
    #possibleSurfaces=["Hard", "Firm", "Good", "Soft", "Heavy", "Frozen"]
    #possibleASurfaces=["Fast","filler1", "Standard", "filler2", "Slow"]
    #conversionDict = {'Firm': 0.9860456670784374, 'Standard': 0.9899727145520246, 'Very Soft': 1.0367803183512474, 'Muddy': 0.9887823908305395, 'Good To Yielding': 1.007845752005393, 'Heavy': 1.0899448658398128, 'Good To Soft': 1.018842175755865, 'Fast': 1.0175608209256009, 'Standard To Slow': 1.0088504842372001, 'Soft': 1.051796772455461, 'Yielding': 1.027244057307293, 'Yielding To Soft': 1.0500816506523503, 'Soft To Heavy': 1.0839054029369386, 'Slow': 0.9960459442589452, 'Good To Firm': 0.9932963535957762}



    conversionDict = {'Good To Soft': 1.0057710403676217, 'Firm': 0.9766454354584337, 'Soft': 1.0425408181809093, 'Yielding To Soft': 1.044244483414795, 'Slow': 0.9904789033077347, 'Soft To Heavy': 1.0380114076967661, 'Fast': 1.019479996780166, 'Good To Yielding': 1.011220705726505, 'Heavy': 1.0670030456915105, 'Standard To Slow': 1.0036460981517916, 'Yielding': 1.026115150891359, 'Good To Firm': 0.9966939235663401, 'Very Soft': 1.0383151041647665, 'Standard': 1.0023521746405304}


    if going == horseName_going:
        return speed

    good = speed / conversionDict[horseName_going]
    good_going = good * conversionDict[going]
    return good_going

def get_time_for_known_length(time, horseName_length_str, length_str):
    
    myDict_1m = {'7f127yds': 1.039300689862624, '6f110yds': 1.2778934838214382, '7f': 1.160534476635255, '7f1yds': 1.1552992577293395, '1m55yds': 0.9560918178321173, '7f25yds': 1.080823568064834, '7f36yds': 1.1351284638089973, '1m3yds': 1.0509669739548815, '6f195yds': 1.1509368494101317, '6f': 1.381713838153811, '1m37yds': 1.03412937194434, '1m110yds': 0.9287922191566025, '1m68yds': 0.9520107495920914, '1m4f': 0.6484799143744504, '1m1yds': 1.0200177087859543, '6f1yds': 1.3728850761888192, '1m73yds': 0.9453662842012357, '1m13yds': 0.9765120597845394, '7f213yds': 1.0037597781478536, '1m1f104yds': 0.8227074320470756, '7f110yds': 1.086270584838055, '7f50yds': 1.1289994622702058, '1m98yds': 0.9350587789154342, '1m2f44yds': 0.7506576325229175, '7f96yds': 1.062616210515089, '7f80yds': 1.0468949383241175, '2m': 0.4083508182962652, '1m177yds': 0.9121273463378725, '1m142yds': 0.9071224711427319, '7f219yds': 1.0331215498385586, '1m3f': 0.713171167561319, '1m5yds': 0.962555421765461, '1m6yds': 0.9706713436616975, '1m2f37yds': 0.7763605442176871, '1m2f': 0.7853853552356109, '1m3f50yds': 0.6943210873368322, '7f37yds': 1.0572569906790945, '1m75yds': 0.9392071320182095, '1m2f150yds': 0.7313169677635554, '7f89yds': 1.0869251392039596, '7f218yds': 0.9846871514045228, '7f30yds': 1.1003467561562905, '5f110yds': 1.544723294723295, '7f6yds': 1.2034754021369027, '7f173yds': 1.0182658637373467, '1m53yds': 0.9857278782112274, '7f14yds': 1.1794171738160335, '1m2f43yds': 0.7157072307805705, '1m2f110yds': 0.7211943441636582, '2m165yds': 0.41834232832464036, '1m113yds': 0.986760899860641, '1m2f70yds': 0.7072009376602446, '1m1f110yds': 0.8226403688870402, '7f33yds': 1.1635476919587162, '1m1f': 0.8852396133513273, '5f193yds': 1.3300053248136314, '1m2yds': 0.9945625308947107}

    myDict_2m = {'2m4f62yds': 0.7379968203497616, '2m3f188yds': 0.8225569314209168, '1m4f110yds': 1.2859827090598925, '1m7f216yds': 0.9528546712802769, '2m5f135yds': 0.7364341085271318, '2m160yds': 0.9491119843080927, '1m7f168yds': 0.9626779158618217, '2m4f': 0.7651143659851141, '2m2f': 0.9160802153975158, '2m178yds': 0.9928033267980557, '2m100yds': 0.9807493577791373, '1m1f162yds': 1.70100022906009, '2m3f154yds': 0.7687128092702786, '1m4f': 1.3663350368769362, '2m1f162yds': 0.839303219968328, '2m53yds': 0.9162105263157895, '1m7f212yds': 1.0120533792509685, '1m': 2.4488747302435514, '1m7f': 1.1025720233373537, '1m1f110yds': 1.8087810007887126, '1m7f169yds': 1.0340738613220963, '2m1f110yds': 0.9794452346689052, '2m3f100yds': 0.8380651945320714, '2m1f46yds': 0.9004674794718175, '1m7f65yds': 1.0903342366757, '2m3f88yds': 0.8199085473091804, '2m3f166yds': 0.7674338715218137, '2m3f86yds': 0.7795071335927368, '1m7f171yds': 1.009727758763379, '1m7f182yds': 1.0384220315726354, '1m3f70yds': 1.5630550621669625, '2m5f55yds': 0.7414021164021164, '1m4f132yds': 1.2979957141056346, '2m75yds': 0.9482470784641068, '2m1f43yds': 0.8806965542793628, '2m1f14yds': 0.9128244866330878, '2m4f50yds': 0.818594135622846, '1m7f153yds': 0.9214131041687864, '2m150yds': 0.9811397445683463, '2m4f118yds': 0.8359824146094014, '2m54yds': 0.953219537149399, '2m3f34yds': 0.7879190175904414, '2m213yds': 0.9355215076376007, '2m1f': 0.9461100694553817, '2m1f164yds': 0.8973756365060712, '1m7f144yds': 1.0192066805845512, '1m6f44yds': 1.1451595219822388, '2m90yds': 1.0191109264644787, '1m5f110yds': 1.0964725881852952, '2m3f150yds': 0.8378822755672476, '2m3f110yds': 0.805684050440403, '2m69yds': 0.9669156883671292, '2m56yds': 0.9895553987297105, '2m50yds': 0.9980415197806503, '1m7f209yds': 0.9772653458915231, '2m70yds': 0.9689979266265701, '2m110yds': 1.0115658362989324, '2m47yds': 1.0705705705705706, '2m120yds': 0.9301391862955032, '2m3f83yds': 0.7828025477707007, '2m78yds': 0.9823625922887612, '2m148yds': 0.9237455551165548, '2m167yds': 0.9258902087345382, '2m40yds': 0.9815396700706992}

    """
    try:
        conversion_ratio = myDict_2m[horseName_length_str]
        time_2m = conversion_ratio*time
        conversion_ratio = myDict_1m["2m"]
        time_1m = conversion_ratio * time_2m
        return time_1m
    except Exception as e:
        pass

    try:
        conversion_ratio = myDict_1m[horseName_length_str]
        time_1m = conversion_ratio * time
        return time_1m
    except Exception as e:
        pass
    """    
    # try and find the nearest distance in the dicts to the horseName_length
    min_diff = 1000000.0
    horseName_length = minmax.convertRaceLengthMetres(horseName_length_str)
    for key,value in myDict_2m.items():
        key_length = minmax.convertRaceLengthMetres(str(key))
        length_diff = abs(horseName_length-key_length)
        if length_diff < min_diff:
            key_rem = key
            min_diff = length_diff
            dict_rem = "2m"

    for key,value in myDict_1m.items():
        key_length = minmax.convertRaceLengthMetres(str(key))
        length_diff = abs(horseName_length-key_length)
        if length_diff < min_diff:
            key_rem = key
            min_diff = length_diff
            dict_rem = "1m"

    # try and find the nearest distance in the dicts to the length
    min_diff = 1000000.0
    length = minmax.convertRaceLengthMetres(length_str)
    for key,value in myDict_2m.items():
        key_length = minmax.convertRaceLengthMetres(str(key))
        length_diff = abs(length-key_length)
        if length_diff < min_diff:
            key_race_rem = key
            min_diff = length_diff
            dict_race_rem = "2m"

    for key,value in myDict_1m.items():
        key_length = minmax.convertRaceLengthMetres(str(key))
        length_diff = abs(length-key_length)
        if length_diff < min_diff:
            key_race_rem = key
            min_diff = length_diff
            dict_race_rem = "1m"
            

    if dict_rem == "2m":
        conversion_ratio = myDict_2m[key_rem]
        time_2m = conversion_ratio*time
        if dict_race_rem == "2m":
            conversion_ratio = myDict_2m[key_race_rem]
            time_return = time_2m / conversion_ratio
        else:
            conversion_ratio = myDict_1m["2m"]
            time_1m = time_2m * conversion_ratio
            conversion_ratio = myDict_1m[key_race_rem]
            time_return = time_1m / conversion_ratio
        return time_return
    else:
        conversion_ratio = myDict_1m[key_rem]
        time_1m = conversion_ratio * time
        if dict_race_rem == "2m":
            conversion_ratio = myDict_2m["1m"]
            time_2m = time_1m * conversion_ratio
            conversion_ratio = myDict_2m[key_race_rem]
            time_return = time_2m / conversion_ratio
        else:
            conversion_ratio = myDict_1m[key_race_rem]
            time_return = time_1m / conversion_ratio
        return time_return

    return "Nope"

def get_fastest_horse(rows, databases):
    fastest_list = []
    myDict=defaultdict(list)
    myDict_return=defaultdict(list)
    myDict_error=defaultdict(list)
    for row in rows:
        # need to extract the distance to see if the horses have times at this distance
        length = minmax.convertRaceLengthMetres(row[5])

        # need to extract the going so that this can be taken into account somehow
        going = row[8]

        # need to get the history for this horse
        horseName = row[1]
        horseName_rows = commands.viewMultiple(databases,horseName=horseName)

        # loop through the history from before this race and find a matching distance
        # where the horse came first.  Work out it's speed

        for horseName_row in horseName_rows:
            date = horseName_row[9]
            position = int(horseName_row[4])
            #print (horseName)
            #print (date)
            #print (position)
            if date == row[9]:
                break
            horseName_row_length = minmax.convertRaceLengthMetres(horseName_row[5])
            horseName_row_time = float(horseName_row[14])
            horseName_row_going = horseName_row[8].lstrip()
            #print (horseName_row_length)
            #print(length)

            if position == 1:
                #if horseName_row_length == length:
                #print(horseName_row_length)
                #print(horseName_row_time)
                try:
                    speed = float(horseName_row_length)/float(horseName_row_time)
                except ZeroDivisionError as e:
                    print(e)
                    continue
                #print(speed)
                try:
                    good_speed = get_going_as_good(horseName_row_going, speed, going)
                except KeyError as e:
                    print(e)
                    continue
                #print(good_speed)
                good_time = float(horseName_row_length)/good_speed
                #print(good_time)
                good_time = get_time_for_known_length(good_time, horseName_row[5], row[5])
                #print(good_time)
                # add the horse and the speed and the distance and the date and  going to a list
                if good_time != "Nope":
                    myDict[horseName].append(good_time)
                    good_error = abs(horseName_row_length - length)
                    myDict_error[horseName].append(good_error)
        #if horseName == "Irish Prophecy":
        #    return
    #print (myDict)

    #fastest_list.sort(key = lambda x: x[1])
    for key, value in myDict.items():
        #print ("%s average for %s %s is %f with average length error %f" % (key, row[5], going, mean(value), mean(myDict_error[key])))
        myDict_return[key] = mean(value) 
    return myDict_return

def get_predicted_result(rows, databases, myDict_net, DSDraw_norm_dict, DSNoDraw_norm_dict):

    myDict_predicted = defaultdict(list)
    norm_errors = 0
    for row in rows:
        horseName = row[1]
        horseName_row = commands.viewMultiple(databases,horseName=str(row[1]))

        try:
            #ds_input, draw = makeTestFromDatabase(databases, horseName_row, row)
            ds_input, draw = makeTestFromDatabase_without_normalization(databases, horseName_row, row, DSDraw_norm_dict, DSNoDraw_norm_dict)
        except Exception as e:
            print("error in normalizations")
            print(e)
            norm_errors = norm_errors + 1
            continue
        for key, value in myDict_net.items():
            if not draw:
                if "DSNoDraw" in key:
                    result = value.activate(ds_input)
            else:
                if "DSDraw" in key:
                    result = value.activate(ds_input)
        #print (result)
        #print(result)
        myDict_predicted[horseName].append(result[0])

    print("The number of norm errors were %d" % norm_errors)
    if norm_errors > 1:
        print("DO NOT BET IN THIS RACE!!!!!!!!!!!!!!!!!!")
    return myDict_predicted


def get_predicted_result_DS(rows, DS_list, myDict_net, verbose = False):

    myDict_predicted = defaultdict(list)
    
    for row in rows:
        horseName = row[1]
        draw = row[12]
        if draw:
            DS = DS_list[0]
            draw_add = 1
        else:
            DS = DS_list[1]
            draw_add = 0

        for entry in DS:
            if entry[11+draw_add:] == list(row):
                ds_input = entry[0:11+draw_add]
        try:
            ds_input
        except Exception as e:
            #print("didn't find the row in the DS")
            #print(e)
            #raise Exception
            continue
        for key, value in myDict_net.items():
            if not draw:
                if "DSNoDraw" in key:
                    try:
                        result = value.activate(ds_input)
                    except Exception as e:
                        print("draw is %s" % str(draw))
                        print(ds_input)
                        print(e)
            else:
                if "DSDraw" in key:
                    try:
                        result = value.activate(ds_input)
                    except Exception as e:
                        print("draw is %s" % str(draw))
                        print(ds_input)
                        print(e)
        #print (result)
        del ds_input
        if verbose:
            print(result)
        myDict_predicted[horseName].append(result[0])

    
    return myDict_predicted



def train_net(databases): #
    result = []
    dates = []
    horses = []
    errors = []
    
    # for now specify the dates between which to
    # get the data
    date_start = "2019-01-01"
    date_end = "2019-06-01"
    dateStartSplit=date_start.split('-')
    dateEndSplit=date_end.split('-')

    if os.path.exists("DSDraw.pk") and os.path.exists("DSNoDraw.pk"):
        print ("reading DSDraw from file DSDraw.pk ")
        with open ("DSDraw.pk", 'rb') as fp:
            DSDraw = pickle.load(fp)
        print ("reading DSNoDraw from file DSNoDraw.pk ")
        with open ("DSNoDraw.pk", 'rb') as fp:
            DSNoDraw = pickle.load(fp)

    else:
        rows = []
        start_time = time.time()
        for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):

            dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       
            print (dateIn)

            rows = rows + commands.viewMultiple(databases, raceDate=dateIn)

        prev_raceVenue = 0
        prev_raceTime = 0
        prev_raceDate = 0

        for ii, row in enumerate(rows):
            if not ii%10:
                now_time = time.time()
                time_taken = now_time - start_time
                time_taken_per_ii = time_taken/(ii+1)
                eta = time_taken_per_ii * (len(rows)-ii)
                print("row %d of %d on date %s.  Time left %s" % (ii, len(rows), row[9], str(eta)))
            horseName_row = commands.viewMultiple(databases, horseName=row[1])

            """ for each row need to get the race info and then
            get a list of the odds and find the min max for normalizing"""
            """
            raceVenue = row[11]
            raceTime = row[10]
            raceDate = row[9]
            if prev_raceVenue != raceVenue or prev_raceTime != raceTime or prev_raceDate != raceDate:
                race_rows = commands.viewMultiple(databases,raceVenue=raceVenue, raceTime=raceTime, raceDate=raceDate)
                race_odds_list = []
                race_weight_list = []
                for race_row in race_rows:
                    race_odds_split = race_row[15].split("/")
                    try:
                        race_weight_kg = minmax.convertWeightKilos(race_row[3])
                        race_weight_list.append(race_weight_kg)
                        print (str(race_weight_kg))
                    except Exception as e:
                        pass

                    try:
                        race_odds = float(race_odds_split[0])/float(race_odds_split[1])
                    except ValueError as e:
                        print ("error getting odds for normalization")
                        print (e)
                        continue
                    race_odds_list.append(race_odds)

                try:
                    max_odds = max(race_odds_list)
                    min_odds = min(race_odds_list)
                except ValueError as e:
                    print ("error getting the min and max odds for normalization")
                    print (e)
                    continue
                odds_range = max_odds - min_odds
                try:
                    max_weight = max(race_weight_list)
                    min_weight = min(race_weight_list)
                except ValueError as e:
                    print ("error getting the min and max weight for normalization")
                    print (e)
                    continue
                weight_range = max_weight - min_weight
                prev_raceVenue = raceVenue
                prev_raceTime = raceTime
                prev_raceDate = raceDate
            """
            try:
                #ds_input, ds_result, draw = makeTraining(horseName_row, row, databases, odds_range, min_odds, weight_range, min_weight)
                ds_input, ds_result, draw = makeTraining_without_normalization(horseName_row, row, databases)
            except Exception as e:
                print (e)
                continue
            if draw:
                try:
                    DSDraw
                except NameError:
                    DSDraw = SupervisedDataSet(len(ds_input), len(ds_result))
        
                DSDraw.appendLinked(ds_input, ds_result)

            if not draw:
                try:
                    DSNoDraw
                except NameError:
                    DSNoDraw = SupervisedDataSet(len(ds_input), len(ds_result))
        
                DSNoDraw.appendLinked(ds_input, ds_result)
                

        with open("DSDraw.pk", 'wb') as fp:
            pickle.dump(DSDraw, fp)

        with open("DSNoDraw.pk", 'wb') as fp:
            pickle.dump(DSNoDraw, fp)

    # temporary position for the normalization stuff.  Should normally happen before the DS is saved
    DSDraw, DSNoDraw = makeNormalization([DSDraw, DSNoDraw])
    with open("DSDraw_norm.pk", 'wb') as fp:
        pickle.dump(DSDraw, fp)

    with open("DSNoDraw_norm.pk", 'wb') as fp:
        pickle.dump(DSNoDraw, fp)


    print ("The DSDraw is %d input and %d output" % (len(DSDraw['input']), len(DSDraw['target'])))
    print (DSDraw)
    print ("The DSNoDraw is %d input and %d output" % (len(DSNoDraw['input']), len(DSNoDraw['target'])))
    print (DSNoDraw)
    """
    new_DS = SupervisedDataSet(5, 2)
    for entry in DS:
        new_ds_input = entry[0].tolist()
        new_ds_result = entry[1].tolist()
        if new_ds_result[0] == 1.0:
            new_ds_result = [1,0]
        else:
            new_ds_result = [0,1]
        #new_ds_input.pop(0)
        new_DS.appendLinked(new_ds_input, new_ds_result)
    DS = new_DS
    print (DS)
    """
    DS_list = [["DSDraw", DSDraw], ["DSNoDraw", DSNoDraw]]
    myDict_net = {} 
    for DS_entry in DS_list:
        DS = DS_entry[1]
        DS_name = DS_entry[0]
        tstdata, trndata = DS.splitWithProportion( 0.25 )
        print("The DS being converted is %s" % (DS_name))
        print ("The training_data is %d input and %d output" % (len(trndata['input']), len(trndata['target'])))
        #print (trndata)


        test_data = ClassificationDataSet(len(tstdata['input'][0]), 1, nb_classes=2)
        for ii in range(0, tstdata.getLength()):
            if tstdata.getSample(ii)[1].tolist() == [1.0]:
                result_class = 0
            else:
                result_class = 1
            input_data = tstdata.getSample(ii)[0].tolist()
            test_data.addSample(input_data, result_class)

        training_data = ClassificationDataSet(len(trndata['input'][0]), 1, nb_classes=2)
        for ii in range(0, trndata.getLength()):
            if trndata.getSample(ii)[1].tolist() == [1.0]:
                result_class = 0
            else:
                result_class = 1
            input_data = trndata.getSample(ii)[0].tolist()
            training_data.addSample(input_data, result_class)


        print ("The training_data is %d input and %d output" % (len(training_data['input']), len(training_data['target'])))
        #print (training_data)
        test_data._convertToOneOfMany()

        training_data._convertToOneOfMany()
        print ("The training_data is %d input and %d output" % (len(training_data['input']), len(training_data['target'])))
        #print(training_data)
        #sys.exit()
        """
        # Now undersample the training and test data
        training_data_win, training_data_lose = training_data.splitByClass(0)
        print ("the size of win data is %d and the size of lose data is %d" % (len(training_data_win), len(training_data_lose)))
        training_data = SupervisedDataSet(len(training_data_win['input'][0]), 1)
        for ii in range(0, training_data_win.getLength()):
            result = 1.0
            input_data = training_data_win.getSample(ii)[0]
            training_data.appendLinked(input_data, result)
            result = 0.0
            input_data = training_data_lose.getSample(ii)[0]
            training_data.appendLinked(input_data, result)

        test_data_win, test_data_lose = test_data.splitByClass(0)
        print ("the size of win data is %d and the size of lose data is %d" % (len(test_data_win), len(test_data_lose)))
        test_data = SupervisedDataSet(len(test_data_win['input'][0]), 1)
        for ii in range(0, test_data_win.getLength()):
            result = 1.0 
            input_data = test_data_win.getSample(ii)[0]
            test_data.appendLinked(input_data, result)
            result = 0.0 
            input_data = test_data_lose.getSample(ii)[0]
            test_data.appendLinked(input_data, result)
        """

        # Now oversample the training and test data
        training_data_win, training_data_lose = training_data.splitByClass(0)
        print ("the size of win data is %d and the size of lose data is %d" % (len(training_data_win), len(training_data_lose)))
        training_data = SupervisedDataSet(len(training_data_win['input'][0]), 1)
        for ii in range(0, training_data_lose.getLength()):
            result = 1.0
            input_data = training_data_win.getSample(ii%training_data_win.getLength())[0]
            training_data.appendLinked(input_data, result)
            result = 0.0
            input_data = training_data_lose.getSample(ii)[0]
            training_data.appendLinked(input_data, result)

        test_data_win, test_data_lose = test_data.splitByClass(0)
        print ("the size of win data is %d and the size of lose data is %d" % (len(test_data_win), len(test_data_lose)))
        test_data = SupervisedDataSet(len(test_data_win['input'][0]), 1)
        for ii in range(0, test_data_lose.getLength()):
            result = 1.0 
            input_data = test_data_win.getSample(ii%test_data_win.getLength())[0]
            training_data.appendLinked(input_data, result)
            result = 0.0 
            input_data = test_data_lose.getSample(ii)[0]
            training_data.appendLinked(input_data, result)
        

        #print (training_data)
        print ("training_data dimensions are %d in and %d out" % (training_data.indim, training_data.outdim))

        iteration = 0
        saved_error = 200.0
        saved_win = 0
        saved_loss = 0
        saved_filename = ""
        learningRate = 0.0
        momentum = 0.1
        if True:
            if (iteration % 10) == 0:
                learningRate = learningRate + 0.04

            hiddenLayer0 = 10 #int((len(training_data)/100)/(training_data.indim + training_data.outdim))
            #if hiddenLayer0 == 48:
            #    hiddenLayer0 = 49
            #if hiddenLayer0 == 35 or hiddenLayer0 == 36:
            #    hiddenLayer0 = 37
            hiddenLayer1 = 0#hiddenLayer0
            print("hidden layer neurons = %d" % (hiddenLayer0))
            #hiddenLayer1 = 4
            #hiddenLayer2 = 4
            #hiddenLayer3 = 4
            #hiddenLayer4 = 4
            #hiddenLayer5 = 4
            #hiddenLayer6 = 4
            iteration = iteration + 1
            netFilename = str(iteration) + "sigmoidnet_" + str(learningRate) + "_" + str(momentum) + "_" + DS_name
            netFilename = netFilename + "_" + str(hiddenLayer0) + ".xml" #+ "_" + str(hiddenLayer1) + "_" + str(hiddenLayer2) + "_" + str(hiddenLayer3) + "_" + str(hiddenLayer4) + "_" + str(hiddenLayer5) + "_" + str(hiddenLayer6) 

            if os.path.exists(netFilename): # and not useDaysTestInputs:
                print ("found network training file")
                net = NetworkReader.readFrom(netFilename) 
                
                #trainer=BackpropTrainer(net, learningrate = learningRate, momentum = momentum, weightdecay = 0.00001, verbose=True)  
                #print (net)
                #print_net_connections(net)
                #sys.exit()
                win_correct = 0
                win_sample = 0
                lose_correct = 0
                lose_sample = 0

                """
                for ii in range(0, test_data.getLength()):
                    result = net.activate(test_data['input'][ii])
                    if test_data['target'][ii] == 1.0:
                        win_sample = win_sample + 1
                        if result > 0.5:
                            win_correct = win_correct + 1

                    else:
                        lose_sample = lose_sample + 1
                        if result < 0.5:
                            lose_correct = lose_correct +1
                win_error = ((win_sample - win_correct)/win_sample)*100
                lose_error = ((lose_sample - lose_correct)/lose_sample)*100
                print('Percent Error on testData - win %f lose %f:' % (win_error, lose_error))
                """
                myDict_net[netFilename] = net
                #wins = runTestDates(databases, "2020-01-01", "2020-02-01", myDict_net, DS_name)
                #wins = runTestDates(databases, "2020-02-01", "2020-03-01", myDict_net, DS_name)


            else:
                net=buildNetwork(training_data.indim, hiddenLayer0, training_data.outdim, bias=True, hiddenclass=TanhLayer, outclass=SigmoidLayer) 
                net.randomize()
                #hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, hiddenLayer5, hiddenLayer6,
                prev_wins = 0
                for jj in range(10):
                    kk = 0
                    """
                    for kk in range (0, int(training_data.getLength()/1000)):
                        tmp_DS = SupervisedDataSet(len(training_data['input'][0]), 1)
                        for mm in range(0, 1000):
                            result = training_data.getSample(((kk*1000)+mm)%training_data.getLength())[1]
                            input_data = training_data.getSample(((kk*1000)+mm)%training_data.getLength())[0]
                            tmp_DS.appendLinked(input_data, result)

                        trainer=BackpropTrainer(net, dataset=tmp_DS, learningrate = learningRate, momentum = momentum, weightdecay = 0.00001, verbose=True)
                        #trnerr, valerr=trainer.trainUntilConvergence(dataset=training_data, maxEpochs=20, verbose=True, continueEpochs=10)
                    """

                    trainer=BackpropTrainer(net, dataset=training_data, learningrate = learningRate, momentum = momentum, weightdecay = 0.00001, verbose=True)
                    if True:
                        trainer.train()
                        win_correct = 0
                        win_sample = 0
                        lose_correct = 0
                        lose_sample = 0
                        """
                        for ii in range(0, test_data.getLength()):
                            result = net.activate(test_data['input'][ii])
                            if test_data['target'][ii] == 1.0:
                                win_sample = win_sample + 1
                                if result > 0.5:
                                    win_correct = win_correct + 1

                            else:
                                lose_sample = lose_sample + 1
                                if result < 0.5:
                                    lose_correct = lose_correct +1
                        win_error = ((win_sample - win_correct)/win_sample)*100
                        lose_error = ((lose_sample - lose_correct)/lose_sample)*100
                        print('Percent Error on testData - win %f lose %f:' % (win_error, lose_error))
                        """
                        print("This was for learning_rate %f and epoch-sub iteration %d-%d" % (learningRate, jj, kk))
                        myDict_net[netFilename] = net

                        wins = runTestDates(databases, "2020-01-01", "2020-02-01", myDict_net, DS_name)
                        if wins > prev_wins:
                            prev_net = copy.deepcopy(net)
                            prev_wins = wins

                    if jj > 2:
                        learningRate = learningRate/2

                try:
                    """
                    mse=trainer.testOnData(dataset=test_data)
                    win_correct = 0
                    win_sample = 0
                    lose_correct = 0
                    lose_sample = 0
                    for ii in range(0, test_data.getLength()):
                        result = net.activate(test_data['input'][ii])
                        if test_data['target'][ii] == 1.0:
                            win_sample = win_sample + 1
                            if result > 0.5:
                                win_correct = win_correct + 1

                        else:
                            lose_sample = lose_sample + 1
                            if result < 0.5:
                                lose_correct = lose_correct +1
                    win_error = ((win_sample - win_correct)/win_sample)*100
                    lose_error = ((lose_sample - lose_correct)/lose_sample)*100
                    print('Percent Error on testData - win %f lose %f:' % (win_error, lose_error))
                    """
                    print("This was for learning_rate %f and iteration %d" % (learningRate, iteration))
                    #if (win_error + lose_error) < saved_error:
                    NetworkWriter.writeToFile(prev_net, netFilename)
                    #    saved_error = win_error + lose_error
                    #    saved_loss = lose_error
                    #    saved_win = win_error
                    saved_filename = netFilename
                    print("current best is %s with win error %f and lose error %f" % (saved_filename, saved_win, saved_loss))

                except AssertionError as e:
                    print (e)
                    raise Exception
                #errors.append(mse)
                #print ("net Mean Squared Error = " + str(mse))


        myDict_net[netFilename] = net
    
    return myDict_net

    """
    horseName = horseName_row[0][1]
        try:
            ds_input = makeTestFromDatabase(databases, horseName, date, days_list_max, days_list_min, max_length, min_length)
        except Exception as e:
            continue
        result.append(net.activate(ds_input))
        horses.append(horseName)
        dates.append(date)
        continue        
        date_time_list = []
        position = []
        legend_list = []
        for ii, date in enumerate(dates):
            date_time_list.append(str(date))
            date_time = pd.to_datetime(date_time_list)
            position.append(float(result[ii]))
    
        DF = pd.DataFrame()
        DF['position'] = position
        DF = DF.set_index(date_time)
        fig, ax = plt.subplots()
        fig.subplots_adjust(bottom=0.3)
        plt.xticks(rotation=90)
        plt.xlabel("date")
        plt.ylabel("position")
        plt.plot(DF)
        legend_list.append(str(horseName_row[0][1]))
        plt.legend(legend_list, loc='upper left')
    print (str(result))
    print (str(horses))
    print (str(errors))
    plt.show(block=False)
    """

def makeTestFromDatabase(databases, horseName_rows, row):
    """ make a net input for the given horseName on the
    given date"""
    

    days_list = []
    length_list = []

    for ii, horseName_row in enumerate(horseName_rows):
        length = minmax.convertRaceLengthMetres(horseName_row[5])
        length_list.append(length)
    

        if ii == 0:
            if horseName_rows[ii][9] == row[9]:
                raise Exception
            continue
    
        dateStartSplit=horseName_rows[ii][9].split('-')
        dateEndSplit=horseName_rows[ii-1][9].split('-')
        dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
        dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
        days = dateStart - dateEnd
        days_list.append(days.days)
        # only use races before the date in row
        if horseName_rows[ii][9] == row[9]:
            prev_row = horseName_rows[ii-1]
            break


    days_list_max = max(days_list)
    days_list_min = min(days_list)
    days_list_range = days_list_max - days_list_min

    max_length = max(length_list)
    min_length = min(length_list)
    length_range = max_length - min_length


    ds_input = []

    # input 0 will be the odds, normalized against the
    # odds of the other horses in the particular race.
    # These should then be translated to the scale
    # 0.1 - 0.9
    """ for each row need to get the race info and then
    get a list of the odds and find the min max for normalizing"""
    raceVenue = row[11]
    raceTime = row[10]
    raceDate = row[9]
    race_rows = commands.viewMultiple(databases,raceVenue=raceVenue, raceTime=raceTime, raceDate=raceDate)
    race_odds_list = []
    for race_row in race_rows:
        race_odds_split = race_row[15].split("/")
        try:
            race_odds = float(race_odds_split[0])/float(race_odds_split[1])
        except ValueError as e:
            print (race_row[15])
            print (race_odds_split)
            print (e)
            continue
        race_odds_list.append(race_odds)
    max_odds = max(race_odds_list)
    min_odds = min(race_odds_list)
    odds_range = max_odds - min_odds

    odds_split = row[15].split("/")
    try:
        odds = float(odds_split[0])/float(odds_split[1])
    except ValueError as e:
        print (e)
        raise Exception
    normalized_odds = ((float(odds - min_odds)/float(odds_range))*0.8)+0.1
    ds_input.append(float(normalized_odds)) 


    # input 1 will be the race length in meters, normalized
    # against the other races run by this horse.  This
    # should then be scaled to be 0.1 to 0.9
    length = minmax.convertRaceLengthMetres(row[5])
    length_range = max_length - min_length
    normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
    ds_input.append(float(normalized_length)) 


    # input 2 will be the last race length in meters,
    # normalized and scaled in the same manner as the
    # race length
    #print("current race data %s, previous race data %s" % (row[9], prev_row[9]))
    length = minmax.convertRaceLengthMetres(prev_row[5])
    normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
    ds_input.append(float(normalized_length)) 

    # input 3 will be the days since last race.  This 
    # is normalized against the longest and shortest time
    # between races for this horse and scaled to 0.1 - 0.9
    dateStartSplit=row[9].split('-')
    dateEndSplit=prev_row[9].split('-')
    dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
    dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
    days = dateStart - dateEnd
    days_list_range = days_list_max - days_list_min
    if days_list_range == 0:
        if days_list_min == 0:
            raise Exception
        days_normalized = ((days.days/days_list_min)*0.8)+0.1
    else:
        days_normalized = ((float(days.days - days_list_min)/float(days_list_range))*0.8)+0.1
    ds_input.append(1.0-days_normalized)

    # input 4 will be the 1-the number of horses in the
    # race scaled to be 0.1-0.9
    ds_input.append(float(1.0)/float(row[6]))

    # input 5,6,7,8 will be the result from the previous race in the same format
    # as the target result
    if prev_row[4] == 1:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 2:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] > 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    draw = row[12]
    if draw:
        normalized_draw = float(draw)/float(row[6])
        ds_input.append(normalized_draw)

    # the weight
    race_weight_list = []
    for race_row in race_rows:
        try:
            race_weight_kg = minmax.convertWeightKilos(race_row[3])
        except Exception as e:
            print("problem getting the weight in kg for the normalization")
            print(e)
            continue
        race_weight_list.append(race_weight_kg)
    max_weight = max(race_weight_list)
    min_weight = min(race_weight_list)
    weight_range = max_weight - min_weight

    try:
        race_weight_kg = minmax.convertWeightKilos(row[3])
    except Exception as e:
        print(e)
        raise Exception
    normalized_weight = ((float(race_weight_kg - min_weight)/float(weight_range))*0.8)+0.1
    ds_input.append(float(normalized_weight)) 

    # the age
    age = float(row[2])/15.0
    if age > 1.0:
        raise Exception
    ds_input.append(age)


    return ds_input, draw


def makeTestFromDatabase_without_normalization(databases, horseName_rows, row, DSDraw_norm_dict, DSNoDraw_norm_dict):
    """ make a net input for the given horseName on the
    given date"""
    verbose = True
    draw = row[12]
    if draw:
        DS_norm_dict = DSDraw_norm_dict
    else:
        DS_norm_dict = DSNoDraw_norm_dict
    
    # This should only happen if it is a real result as the horse was not in the database
    if len(horseName_rows) == 0:
        if verbose:
            print("horse was not found in any database")
        raise Exception


    for ii, horseName_row in enumerate(horseName_rows):
        if ii == 0:
            if horseName_rows[ii][9] == row[9]:
                if verbose:
                    print("This horse %s has no previous form" % str(row[1]))
                raise Exception
            continue
    
        # only use races before the date in row
        if horseName_rows[ii][9] == row[9]:
            prev_row = horseName_rows[ii-1]
            break
    try:
        prev_row
    except Exception:
        prev_row = horseName_rows[-1]
        if verbose:
            print("the previous race was %s" % str(prev_row))

    ds_input = []

    # input 0 will be the odds, normalized against the
    # odds of the other horses in the particular race.
    # These should then be translated to the scale
    # 0.1 - 0.9
    """ for each row need to get the race info and then
    get a list of the odds and find the min max for normalizing"""
    odds_split = row[15].split("/")
    try:
        odds = float(odds_split[0])/float(odds_split[1])
    except ValueError as e:
        if verbose:
            print (e)
        raise Exception
    odds_norm = (float(odds) - float(DS_norm_dict['odds'][0]))/(float(DS_norm_dict['odds'][1])-float(DS_norm_dict['odds'][2]))
    ds_input.append(float(odds_norm)) 

    # input 1 will be the race length in meters
    length = minmax.convertRaceLengthMetres(row[5])
    length_norm = (float(length) - float(DS_norm_dict['length'][0]))/(float(DS_norm_dict['length'][1])-float(DS_norm_dict['length'][2]))
    ds_input.append(float(length_norm)) 


    # input 2 will be the last race length in meters,
    length = minmax.convertRaceLengthMetres(prev_row[5])
    length_norm = (float(length) - float(DS_norm_dict['prev_length'][0]))/(float(DS_norm_dict['prev_length'][1])-float(DS_norm_dict['prev_length'][2]))
    ds_input.append(float(length_norm)) 

    # input 3 will be the days since last race.
    dateStartSplit=row[9].split('-')
    dateEndSplit=prev_row[9].split('-')
    dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
    dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
    days = dateStart - dateEnd
    days_norm = (float(days.days) - float(DS_norm_dict['days'][0]))/(float(DS_norm_dict['days'][1])-float(DS_norm_dict['days'][2]))
    ds_input.append(float(days_norm))

    # input 4 will be the  number of horses in the race
    num_norm = (float(row[6]) - float(DS_norm_dict['num'][0]))/(float(DS_norm_dict['num'][1])-float(DS_norm_dict['num'][2]))
    ds_input.append(float(num_norm))

    # input 5,6,7,8 will be the result from the previous race in the same format
    # as the target result
    if prev_row[4] == 1:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 2:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] > 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    draw = row[12]
    if draw:
        draw_norm = (float(draw) - float(DS_norm_dict['draw'][0]))/(float(DS_norm_dict['draw'][1])-float(DS_norm_dict['draw'][2]))
        ds_input.append(draw_norm)

    # the weight
    try:
        race_weight_kg = minmax.convertWeightKilos(row[3])
    except Exception as e:
        if verbose:
            print("problem getting the weight")
        print(e)
        raise Exception
    weight_norm = (float(race_weight_kg) - float(DS_norm_dict['weight'][0]))/(float(DS_norm_dict['weight'][1])-float(DS_norm_dict['weight'][2]))
    ds_input.append(float(weight_norm)) 

    # the age
    age = float(row[2])
    age_norm = (float(age) - float(DS_norm_dict['age'][0]))/(float(DS_norm_dict['age'][1])-float(DS_norm_dict['age'][2]))
    ds_input.append(age_norm)


    return ds_input, draw



def makeTraining(horseName_rows, row, databases, odds_range, min_odds, weight_range, min_weight):
    """ make training data set from previous
    races"""

    # the result will be the average odds for finishing
    # in the postition the horse finished.  Average odds deterined using
    # commands.get_average_odds("results_2019_2.db", "2019")
    days_list = []
    length_list = []

    for ii, horseName_row in enumerate(horseName_rows):
        length = minmax.convertRaceLengthMetres(horseName_row[5])
        length_list.append(length)
    

        if ii == 0:
            if horseName_rows[ii][9] == row[9]:
                raise Exception
            continue
    
        dateStartSplit=horseName_rows[ii][9].split('-')
        dateEndSplit=horseName_rows[ii-1][9].split('-')
        dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
        dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
        days = dateStart - dateEnd
        days_list.append(days.days)
        # only use races before the date in row
        if horseName_rows[ii][9] == row[9]:
            prev_row = horseName_rows[ii-1]
            break


    days_list_max = max(days_list)
    days_list_min = min(days_list)
    days_list_range = days_list_max - days_list_min

    max_length = max(length_list)
    min_length = min(length_list)
    length_range = max_length - min_length


    ds_input = []
    ds_result = 1*[0.0]
    if row[4] == 1:
        ds_result[0] = 1.0
    else:
        ds_result[0] = 0.0

    
    # input 0 will be the odds, normalized against the
    # odds of the other horses in the particular race.
    # These should then be translated to the scale
    # 0.1 - 0.9

    odds_split = row[15].split("/")
    try:
        odds = float(odds_split[0])/float(odds_split[1])
    except ValueError as e:
        print (e)
        raise Exception
    normalized_odds = ((float(odds - min_odds)/float(odds_range))*0.8)+0.1
    ds_input.append(float(normalized_odds)) 


    # input 1 will be the race length in meters, normalized
    # against the other races run by this horse.  This
    # should then be scaled to be 0.1 to 0.9
    #print("date is %s" % str(row[9]))
    length = minmax.convertRaceLengthMetres(row[5])
    normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
    ds_input.append(float(normalized_length)) 


    # input 2 will be the last race length in meters,
    # normalized and scaled in the same manner as the
    # race length
    #print("prev_date is %s" % str(prev_row[9]))
    length = minmax.convertRaceLengthMetres(prev_row[5])
    normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
    ds_input.append(float(normalized_length)) 

    # input 3 will be the days since last race.  This 
    # is normalized against the longest and shortest time
    # between races for this horse and scaled to 0.1 - 0.9
    dateStartSplit=row[9].split('-')
    dateEndSplit=prev_row[9].split('-')
    dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
    dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
    days = dateStart - dateEnd

    if days_list_range == 0:
        if days_list_min == 0:
            raise Exception
        days_normalized = ((days.days/days_list_min)*0.8)+0.1
    else:
        days_normalized = ((float(days.days - days_list_min)/float(days_list_range))*0.8)+0.1

    ds_input.append(1.0-days_normalized)

    # input 4 will be the 1-the number of horses in the
    # race scaled to be 0.1-0.9
    ds_input.append(float(1.0)/float(row[6]))

    # input 5,6,7,8 will be the result from the previous race in the same format
    # as the target result
    if prev_row[4] == 1:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 
    
    if prev_row[4] == 2:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] > 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 
    
    # input 9 will be the normalized draw if there was a draw
    draw = row[12]
    if draw:
        normalized_draw = float(draw)/float(row[6])
        ds_input.append(normalized_draw)

    #input 10 will be the weight normalized against all horses in the race
    try:
        weight = minmax.convertWeightKilos(row[3])
    except Exception as e:
        print (e)
        raise Exception
    normalized_weight = ((float(weight - min_weight)/float(weight_range))*0.8)+0.1
    ds_input.append(float(normalized_weight)) 

    #input 11 wil be the age relative to a 15 year old (assumed to be about the oldest)
    age = float(row[2])/15.0
    if age > 1.0:
        print("age of horse was %d, i.e > 15" % (row[2]))
        raise Exception
    ds_input.append(age)

    return ds_input, ds_result, draw

def makeNormalize_median_75_25(DS_list):
    
    DSDraw_norm_dict = {}
    DSNoDraw_norm_dict = {}
    for jj, DS in enumerate(DS_list):
        odds_list = []
        length_list = []
        prev_length_list = []
        days_list = []
        num_list = []
        draw_list = []
        weight_list = []
        age_list = []

        # before finding the inputs, find the median and also the 75th and 25th quantile
        for ii in range(0, DS.getLength()):
            result= DS.getSample(ii)[1].tolist()
            input_data = DS.getSample(ii)[0].tolist()
            # odds
            odds_list.append(input_data[0])
            # race length 
            length_list.append(input_data[1])
            #previous race length 
            prev_length_list.append(input_data[2])
            # days since last race
            days_list.append(input_data[3])
            # number of horses in the race
            num_list.append(input_data[4])
            if jj == 0:
                # draw
                draw_list.append(input_data[9])
            # weight
            weight_list.append(input_data[10-jj])
            # age
            age_list.append(input_data[11-jj])
            
        num_entries = DS.getLength()
        per_quantile = float(num_entries)/100.0
        quantile_75 = int(per_quantile*75.0)
        quantile_25 = int(per_quantile*25.0)
        odds_list.sort()
        odds_median = median(odds_list)
        odds_75 = odds_list[quantile_75]
        odds_25 = odds_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['odds'] = [odds_median, odds_75, odds_25]
        else:
            DSNoDraw_norm_dict['odds'] = [odds_median, odds_75, odds_25]

        length_list.sort()
        length_median = median(length_list)
        length_75 = length_list[quantile_75]
        length_25 = length_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['length'] = [length_median, length_75, length_25]
        else:
            DSNoDraw_norm_dict['length'] = [length_median, length_75, length_25]

        prev_length_list.sort()
        prev_length_median = median(prev_length_list)
        prev_length_75 = prev_length_list[quantile_75]
        prev_length_25 = prev_length_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['prev_length'] = [prev_length_median, prev_length_75, prev_length_25]
        else:
            DSNoDraw_norm_dict['prev_length'] = [prev_length_median, prev_length_75, prev_length_25]

        days_list.sort()
        days_median = median(days_list)
        days_75 = days_list[quantile_75]
        days_25 = days_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['days'] = [days_median, days_75, days_25]
        else:
            DSNoDraw_norm_dict['days'] = [days_median, days_75, days_25]

        num_list.sort()
        num_median = median(num_list)
        num_75 = num_list[quantile_75]
        num_25 = num_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['num'] = [num_median, num_75, num_25]
        else:
            DSNoDraw_norm_dict['num'] = [num_median, num_75, num_25]

        if jj == 0:
            draw_list.sort()
            draw_median = median(draw_list)
            draw_75 = draw_list[quantile_75]
            draw_25 = draw_list[quantile_25]
            DSDraw_norm_dict['draw'] = [draw_median, draw_75, draw_25]

        weight_list.sort()
        weight_median = median(weight_list)
        weight_75 = weight_list[quantile_75]
        weight_25 = weight_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['weight'] = [weight_median, weight_75, weight_25]
        else:
            DSNoDraw_norm_dict['weight'] = [weight_median, weight_75, weight_25]

        age_list.sort()
        age_median = median(age_list)
        age_75 = age_list[quantile_75]
        age_25 = age_list[quantile_25]
        if jj == 0:
            DSDraw_norm_dict['age'] = [age_median, age_75, age_25]
        else:
            DSNoDraw_norm_dict['age'] = [age_median, age_75, age_25]

    return DSDraw_norm_dict, DSNoDraw_norm_dict



def makeNormalization(DS_list):
    """ in DS_list, DSDraw must be entry 0 and DSNODraw must be entry 1"""
    output_DS_list = []
    for jj, DS in enumerate(DS_list):
        odds_list = []
        length_list = []
        prev_length_list = []
        days_list = []
        num_list = []
        draw_list = []
        weight_list = []
        age_list = []

        # before finding the inputs, find the median and also the 75th and 25th quantile
        for ii in range(0, DS.getLength()):
            result= DS.getSample(ii)[1].tolist()
            input_data = DS.getSample(ii)[0].tolist()
            # odds
            odds_list.append(input_data[0])
            # race length 
            length_list.append(input_data[1])
            #previous race length 
            prev_length_list.append(input_data[2])
            # days since last race
            days_list.append(input_data[3])
            # number of horses in the race
            num_list.append(input_data[4])
            if jj == 0:
                # draw
                draw_list.append(input_data[9])
            # weight
            weight_list.append(input_data[10-jj])
            # age
            age_list.append(input_data[11-jj])
            
        num_entries = DS.getLength()
        per_quantile = float(num_entries)/100.0
        quantile_75 = int(per_quantile*75.0)
        quantile_25 = int(per_quantile*25.0)
        odds_list.sort()
        odds_median = median(odds_list)
        odds_75 = odds_list[quantile_75]
        odds_25 = odds_list[quantile_25]

        length_list.sort()
        length_median = median(length_list)
        length_75 = length_list[quantile_75]
        length_25 = length_list[quantile_25]

        prev_length_list.sort()
        prev_length_median = median(prev_length_list)
        prev_length_75 = prev_length_list[quantile_75]
        prev_length_25 = prev_length_list[quantile_25]

        days_list.sort()
        days_median = median(days_list)
        days_75 = days_list[quantile_75]
        days_25 = days_list[quantile_25]

        num_list.sort()
        num_median = median(num_list)
        num_75 = num_list[quantile_75]
        num_25 = num_list[quantile_25]

        if jj == 0:
            draw_list.sort()
            draw_median = median(draw_list)
            draw_75 = draw_list[quantile_75]
            draw_25 = draw_list[quantile_25]

        weight_list.sort()
        weight_median = median(weight_list)
        weight_75 = weight_list[quantile_75]
        weight_25 = weight_list[quantile_25]

        age_list.sort()
        age_median = median(age_list)
        age_75 = age_list[quantile_75]
        age_25 = age_list[quantile_25]

        output_DS = SupervisedDataSet(len(DS.getSample(0)[0].tolist()), len(DS.getSample(0)[1].tolist()))
        for ii in range(0, DS.getLength()):
            output_data = []
            result= DS.getSample(ii)[1].tolist()
            input_data = DS.getSample(ii)[0].tolist()
            output_odds = (float(input_data[0]) - float(odds_median))/(float(odds_75)-float(odds_25))
            output_data.append(output_odds)

            output_length = (float(input_data[1]) - float(length_median))/(float(length_75)-float(length_25))
            output_data.append(output_length)

            output_prev_length = (float(input_data[2]) - float(prev_length_median))/(float(prev_length_75)-float(prev_length_25))
            output_data.append(output_prev_length)

            output_days = (float(input_data[3]) - float(days_median))/(float(days_75) - float(days_25))
            output_data.append(output_days)
        
            output_num = (float(input_data[4])-float(num_median))/(float(num_75)-float(num_25))
            output_data.append(output_num)

            output_data.append(input_data[5])
            output_data.append(input_data[6])
            output_data.append(input_data[7])
            output_data.append(input_data[8])

            if jj == 0:
                output_draw = (float(input_data[9])-float(draw_median))/(float(draw_75)-float(draw_25))
                output_data.append(output_draw)

            output_weight = (float(input_data[10-jj])-float(weight_median))/(float(weight_75)-float(weight_25))
            output_data.append(output_weight)

            output_age = (float(input_data[11-jj])-float(age_median))/(float(age_75)-float(age_25))
            output_data.append(output_age)

            output_DS.addSample(output_data, result)
        output_DS_list.append(output_DS)
    return output_DS_list

def makeTraining_without_normalization(horseName_rows, row, databases):
    """ make training data set from previous
    races"""
    # the result will be the average odds for finishing
    # in the postition the horse finished.  Average odds deterined using
    # commands.get_average_odds("results_2019_2.db", "2019")
    for ii, horseName_row in enumerate(horseName_rows):
        if ii == 0:
            if horseName_rows[ii][9] == row[9]:
                raise Exception
            continue
         
        # only use races before the date in row
        if horseName_rows[ii][9] == row[9]:
            prev_row = horseName_rows[ii-1]
            break

    ds_input = []
    ds_result = 1*[0.0]
    if row[4] == 1:
        ds_result[0] = 1.0
    else:
        ds_result[0] = 0.0

    
    # input 0 will be the odds

    odds_split = row[15].split("/")
    try:
        odds = float(odds_split[0])/float(odds_split[1])
    except ValueError as e:
        print (e)
        raise Exception

    ds_input.append(float(odds)) 


    # input 1 will be the race length in meters
    length = minmax.convertRaceLengthMetres(row[5])
    ds_input.append(float(length)) 


    # input 2 will be the last race length in meters,
    length = minmax.convertRaceLengthMetres(prev_row[5])
    ds_input.append(float(length)) 

    # input 3 will be the days since last race.
    dateStartSplit=row[9].split('-')
    dateEndSplit=prev_row[9].split('-')
    dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
    dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
    days = dateStart - dateEnd

    ds_input.append(float(days.days))

    # input 4 will be the 1-the number of horses in the race
    ds_input.append(float(row[6]))

    # input 5,6,7,8 will be the result from the previous race in the same format
    # as the target result
    if prev_row[4] == 1:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 
    
    if prev_row[4] == 2:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] == 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 

    if prev_row[4] > 3:
        ds_input.append(float(1.0))
    else:
        ds_input.append(float(0.0)) 
    
    # input 9 will be the draw if there was a draw
    draw = row[12]
    if draw:
        ds_input.append(draw)

    #input 10 will be the weight 
    try:
        weight = minmax.convertWeightKilos(row[3])
    except Exception as e:
        print (e)
        raise Exception
    ds_input.append(float(weight)) 

    #input 11 wil be the age 
    age = float(row[2])
    ds_input.append(age)

    return ds_input, ds_result, draw




#def makeTestRace():

#def makeRealRace():
def runTestDates(databases, dateStart, dateEnd, myDict_net, DS_name = "both", verbose = False):

    # check date to see if this date is in a DS or 
    # whether the database should be used
    # checkDateDSDatebase(dateStart, dateEnd)
    useDS = False
    useDatabase = True

    if dateStart == "2020-01-01" and dateEnd == "2020-02-01":
        draw_save_list_name = "DSDraw_save_list_01.pk"
        noDraw_save_list_name = "DSNoDraw_save_list_01.pk"
        useDS = True
        useDatabase = False
    if dateStart == "2020-02-01" and dateEnd == "2020-03-01":
        draw_save_list_name = "DSDraw_save_list_02.pk"
        noDraw_save_list_name = "DSNoDraw_save_list_02.pk"
        useDS = True
        useDatabase = False
        
    #makeTest_DS(databases)
    #sys.exit()


    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')

    fastest_win_list = []
    fastest_winnings = 0
    fastest_loss = 0
    fastest_wins = 0
    fastest = []
    badOdds = 0
    predicted_win_list = []
    predicted_winnings = 0
    predicted_secondings = 0
    predicted_thirdings = 0
    predicted_wins = 0
    predicted_second = 0
    predicted_third = 0
    predicted_loss = 0
    topHorse_win_list = []
    topHorse_winnings = 0
    topHorse_wins = 0
    topHorse_loss = 0

    if useDatabase == True:
        print ("reading DSDraw from file DSDraw.pk ")
        with open ("DSDraw.pk", 'rb') as fp:
            DSDraw = pickle.load(fp)
        print ("reading DSNoDraw from file DSNoDraw.pk ")
        with open ("DSNoDraw.pk", 'rb') as fp:
            DSNoDraw = pickle.load(fp)

    
        DSDraw_norm_dict, DSNoDraw_norm_dict = makeNormalize_median_75_25([DSDraw, DSNoDraw])
    else:
        # open the DS for the dateIn
        DS_list = []
        print ("reading DSDraw from file %s " % draw_save_list_name)
        with open (draw_save_list_name, 'rb') as fp:
            DS_list.append(pickle.load(fp))
        print ("reading DSNoDraw from file %s" % noDraw_save_list_name)
        with open (noDraw_save_list_name, 'rb') as fp:
            DS_list.append(pickle.load(fp))


    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       

        myDict_testcard = makea.makeATestcardFromDatabase(dateIn, databases)

        for key,value in myDict_testcard.items():
            #myDict_fastest = get_fastest_horse(value, databases)
            if not value[0][12]:
                if DS_name == "DSDraw":
                    continue
            if value[0][12]:
                if DS_name == "DSNoDraw":
                    continue
            if useDatabase == True:
                myDict_predicted = get_predicted_result(value, databases, myDict_net, DSDraw_norm_dict, DSNoDraw_norm_dict)
            else:
                try:
                    myDict_predicted = get_predicted_result_DS(value, DS_list, myDict_net)
                except Exception as e:
                    #skip race
                    continue

            #fastest = sorted(myDict_fastest.items(), key=operator.itemgetter(1))
            predicted = sorted(myDict_predicted.items(), key=operator.itemgetter(1))
            actual = value.sort(key = lambda x: x[4]) 

            #print("fastest horse")
            #for entry in fastest:
            #    print(entry)
            if verbose:
                print ("predicted result")
                for entry in predicted:
                    print(entry)
            #print ("actual result")
            #for entry in value:
            #    print(entry)
            try:
                winnings = 0
                secondings = 0
                thirdings = 0
                if int(value[0][4]) != 1:
                    print("first place not where expected to get odds")
                odds=value[0][15]
                winnings = float(odds.split("/")[0])/float(odds.split("/")[1])
                odds=value[1][15]
                secondings = float(odds.split("/")[0])/float(odds.split("/")[1])
                if len(value) > 2:
                    odds=value[2][15]
                    thirdings = float(odds.split("/")[0])/float(odds.split("/")[1])
            except Exception as e:
                #print ("problem with the odds %s" % str(odds))
                #print (str(odds.split("/")))
                badOdds = badOdds + 1
                continue

            if len(fastest) > 0:
                if fastest[-1][0] == value[0][1]:
                    fastest_wins = fastest_wins + 1
                    if winnings >= 0:
                        fastest_winnings = fastest_winnings + winnings
                        fastest_win_list.append(value[0])

                else:
                    fastest_loss = fastest_loss + 1
                    if winnings >= 0:
                        fastest_winnings = fastest_winnings -1

            if len(predicted) > 0:
                # take all horses that were winners
                #numberOfHorsesToTake = min(3, len(predicted))
                #for entry in predicted[-1:(0-numberOfHorsesToTake)]:
                predictedTopHorses_list = []
                fastestTopHorses_list = []
                for entry in predicted:
                    if float(entry[1][0]) > 0.5:
                        predictedTopHorses_list.append(entry)
                if len(fastest) > 0 and len(predictedTopHorses_list) > 0:
                    use_predicted = False
                    for kk, topHorse in enumerate(predictedTopHorses_list):
                        found=False
                        for entry in fastest:
                            if entry[0] == topHorse[0]:
                                fastestTopHorses_list.append(entry)
                                found=True
                        if not found:
                            use_predicted = True
                            break
                    if not use_predicted:
                        fastestTopHorses_list.sort(key = lambda x: x[1])
                        if fastestTopHorses_list[-1][0] == value[0][1]:
                            topHorse_wins = topHorse_wins + 1
                            if winnings >= 0:
                                topHorse_winnings = topHorse_winnings + winnings
                                topHorse_win_list.append(value[0])
                        else:
                            topHorse_loss = topHorse_loss + 1
                            if winnings >= 0:
                                topHorse_winnings = topHorse_winnings - 1

                        #print (fastestTopHorses_list)
                        #print (predictedTopHorses_list)
                        #print (value)
                        #sys.exit()

                if predicted[-1][0] == value[0][1]:
                    predicted_wins = predicted_wins + 1
                    if winnings >= 0:
                        predicted_winnings = predicted_winnings + winnings
                        predicted_win_list.append(value[0])
                    if len(predicted) > 1:
                        predicted_secondings = predicted_secondings -1
                    if len(predicted) > 2:
                        predicted_thirdings = predicted_thirdings - 1
                else:
                    if len(predicted) > 1:
                        if predicted[-2][0] == value[0][1]:
                            predicted_second = predicted_second + 1
                            predicted_secondings = predicted_secondings + secondings
                        else:
                            predicted_secondings = predicted_secondings -1
                    if len(predicted) > 2:
                        if predicted[-3][0] == value[0][1]:
                            predicted_third = predicted_third + 1
                            predicted_thirdings = predicted_thirdings + thirdings
                        else:
                            predicted_thirdings = predicted_thirdings -1

                    predicted_loss = predicted_loss + 1
                    if winnings >= 0:
                        predicted_winnings = predicted_winnings - 1

                print(str(dateIn))
                print("predicted_wins = %d" % predicted_wins)
                print("predicted_second = %d" % predicted_second)
                print("predicted_third = %d" % predicted_third)
                print("predicted_winnings = %f" % predicted_winnings)
                print("predicted_secondings = %f" % predicted_secondings)
                print("predicted_thirdings = %f" % predicted_thirdings)
                print("predicted_loss = %d" % predicted_loss)

            if verbose:
                print("fastest_wins = %d" % fastest_wins)
                print("fastest_winnings = %f" % fastest_winnings)
                print("fastest_loss = %d" % fastest_loss)
                for fastest_win in fastest_win_list:
                    print (fastest_win)
                print("predicted_wins = %d" % predicted_wins)
                print("predicted_second = %d" % predicted_second)
                print("predicted_winnings = %f" % predicted_winnings)
                print("predicted_loss = %d" % predicted_loss)
                #for predicted_win in predicted_win_list:
                #    print (predicted_win)
                print("topHorse_wins = %d" % topHorse_wins)
                print("topHorse_winnings = %f" % topHorse_winnings)
                print("topHorse_loss = %d" % topHorse_loss)
                for topHorse_win in topHorse_win_list:
                    print (topHorse_win)

                #print(actual)
    if verbose:
        for predicted_win in predicted_win_list:
            print (predicted_win)
    print("predicted_wins = %d" % predicted_wins)
    print("predicted_second = %d" % predicted_second)
    print("predicted_third = %d" % predicted_third)
    print("predicted_winnings = %f" % predicted_winnings)
    print("predicted_secondings = %f" % predicted_secondings)
    print("predicted_thirdings = %f" % predicted_thirdings)
    print("predicted_loss = %d" % predicted_loss)

    return predicted_wins


def runToday(databases, myDict_net):
    """ get todays test card and predict the result"""
    todays_date = str(datetime.datetime.today().strftime('%Y-%m-%d'))
    print ("todays date is %s" % todays_date) 

    try:
        horses, jockeys, lengths, ages, weights, goings, draws, trainers, odds, todaysRaceTimes, todaysRaceVenues=makea.makeATestcard(todays_date)
    except Exception as e:
        print ("soething went wrong trying to get todays testcard")
        print(e)
        raise Exception

    # The inputs for todays races will need to be normalized.  At the moment this will be done
    # using the values from the first 6 months of 2019 in DSDraw and DSNoDraw
    print ("reading DSDraw from file DSDraw.pk ")
    with open ("DSDraw.pk", 'rb') as fp:
        DSDraw = pickle.load(fp)
    print ("reading DSNoDraw from file DSNoDraw.pk ")
    with open ("DSNoDraw.pk", 'rb') as fp:
        DSNoDraw = pickle.load(fp)

    DSDraw_norm_dict, DSNoDraw_norm_dict = makeNormalize_median_75_25([DSDraw, DSNoDraw])
    return_list = []
    for raceNo, race in enumerate(horses):
        rows= []
        for idx, horse in enumerate(race):
            row = ["", horse, ages[raceNo][idx], weights[raceNo][idx], "", lengths[raceNo], len(race), jockeys[raceNo][idx], goings[raceNo], todays_date, todaysRaceTimes[raceNo], todaysRaceVenues[raceNo], draws[raceNo][idx], trainers[raceNo][idx], "", odds[raceNo][idx]]
            rows.append(row)
        myDict_predicted = get_predicted_result(rows, databases, myDict_net, DSDraw_norm_dict, DSNoDraw_norm_dict)
        predicted = sorted(myDict_predicted.items(), key=operator.itemgetter(1))
        for ii, entry in enumerate(predicted):
            for row in rows:
                if row[1] == entry[0]:
                    row[4] = len(predicted)-ii
                    return_list.append(row)
        # append an empty row between races
        return_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
    return return_list

def makeTest_DS(databases): #
    result = []
    dates = []
    horses = []
    errors = []
    
    # for now specify the dates between which to
    # get the data
    date_start = "2020-02-01"
    date_end = "2020-03-01"
    dateStartSplit=date_start.split('-')
    dateEndSplit=date_end.split('-')

    if True:
        rows = []
        start_time = time.time()
        for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):

            dateIn=time.strftime("%Y-%m-%d", single_date.timetuple())       
            print (dateIn)

            rows = rows + commands.viewMultiple(databases, raceDate=dateIn)

        prev_raceVenue = 0
        prev_raceTime = 0
        prev_raceDate = 0

        for ii, row in enumerate(rows):
            if not ii%10:
                now_time = time.time()
                time_taken = now_time - start_time
                time_taken_per_ii = time_taken/(ii+1)
                eta = time_taken_per_ii * (len(rows)-ii)
                print("row %d of %d on date %s.  Time left %s" % (ii, len(rows), row[9], str(eta)))
            horseName_row = commands.viewMultiple(databases, horseName=row[1])
            try:
                ds_input, ds_result, draw = makeTraining_without_normalization(horseName_row, row, databases)
            except Exception as e:
                print (e)
                continue
            if draw:
                try:
                    DSDraw
                except NameError:
                    DSDraw = SupervisedDataSet(len(ds_input), len(ds_result))
                    DSDraw_list = []
                DSDraw.appendLinked(ds_input, ds_result)
                DSDraw_list.append(row)

            if not draw:
                try:
                    DSNoDraw
                except NameError:
                    DSNoDraw = SupervisedDataSet(len(ds_input), len(ds_result))
                    DSNoDraw_list = []
                DSNoDraw.appendLinked(ds_input, ds_result)
                DSNoDraw_list.append(row)

    DSDraw, DSNoDraw = makeNormalization([DSDraw, DSNoDraw])
    if len(DSDraw_list) != DSDraw.getLength():
        print("len(DSDraw_list) != DSDraw.getLength()")
        sys.exit()
    else:
        DSDraw_save_list = []
        for ii in range(0, DSDraw.getLength()):
            ds_input = DSDraw.getSample(ii)[0].tolist() + list(DSDraw_list[ii])
            DSDraw_save_list.append(ds_input)
    with open("DSDraw_save_list.pk", 'wb') as fp:
        pickle.dump(DSDraw_save_list, fp)

    if len(DSNoDraw_list) != DSNoDraw.getLength():
        print("len(DSNoDraw_list) != DSNoDraw.getLength()")
        sys.exit()
    else:
        DSNoDraw_save_list = []
        for ii in range(0, DSNoDraw.getLength()):
            ds_input = DSNoDraw.getSample(ii)[0].tolist() + list(DSNoDraw_list[ii])
            DSNoDraw_save_list.append(ds_input)

    with open("DSNoDraw_save_list.pk", 'wb') as fp:
        pickle.dump(DSNoDraw_save_list, fp)
