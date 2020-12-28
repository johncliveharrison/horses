import pandas as pd
import matplotlib.pyplot as plt



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


def get_predicted_result(horseName_rows, databases, date): # train_net(databases): #
    result = []
    dates = []
    horses = []
    errors = []
    
    for horseName_row in horseName_rows:
        try:
            DS, days_list_max, days_list_min, max_length, min_length = makeTraining(horseName_row, databases)
        except Exception as e:
            print (e)
            continue
        tstdata, trndata = DS.splitWithProportion( 0.25 )
        hiddenLayer0 = 8
        hiddenLayer1 = 7
        hiddenLayer2 = 6
        hiddenLayer3 = 5
        hiddenLayer4 = 4
        hiddenLayer5 = 3
        hiddenLayer6 = 2
        net=buildNetwork(len(trndata['input'][0]), hiddenLayer0, hiddenLayer1, hiddenLayer2, hiddenLayer3, hiddenLayer4, hiddenLayer5, hiddenLayer6, 4, bias=True, hiddenclass=ReluLayer, outclass=SoftmaxLayer)
        trainer=BackpropTrainer(net,DS, momentum=0.1, verbose=True, learningrate=0.01)
        aux=trainer.trainUntilConvergence(dataset=trndata, maxEpochs=3000, verbose=True, continueEpochs=5)
        try:
            mse=trainer.testOnData(dataset=tstdata)
        except AssertionError as e:
            print (e)
            continue
        errors.append(mse)
        print ("net Mean Squared Error = " + str(mse))
        #result = []
        #dates = []
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

def makeTestFromDatabase(databases, horseName, date, days_list_max, days_list_min, max_length, min_length):
    """ make a net input for the given horseName on the
    given date"""
    
    # get the horse info for the given date
    rows = commands.viewMultiple(databases,horseName=horseName, raceDate=date)
    row = rows[0]
    print (row)
    rows = commands.viewMultiple(databases,horseName=horseName)
    for jj, entry in enumerate(rows):
        if entry[9] == date:
            ii=jj
            break
    print("ii = " + str(ii))
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
    print("current race data %s, previous race data %s" % (rows[ii][9], rows[ii-1][9]))
    length = minmax.convertRaceLengthMetres(rows[ii-1][5])
    normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
    ds_input.append(float(normalized_length)) 

    # input 3 will be the days since last race.  This 
    # is normalized against the longest and shortest time
    # between races for this horse and scaled to 0.1 - 0.9
    dateStartSplit=rows[ii][9].split('-')
    dateEndSplit=rows[ii-1][9].split('-')
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

    return ds_input
    

def makeTraining(rows, databases):
    """ make training data set from previous
    races"""

    # the result will be the average odds for finishing
    # in the postition the horse finished.  Average odds deterined using
    # commands.get_average_odds("results_2019_2.db", "2019")
    result_worth_list=[1.94728004624699, 3.5579910677018116, 6.181855955678669, 10.464066852367688, 13.421282798833818, 21.144615384615385, 29.11577181208054, 36.80988593155894, 43.513333333333335, 48.82702702702703, 59.49673202614379, 60.8, 65.10752688172043, 72.30263157894737, 73.32, 74.91666666666667, 69.3913043478261, 55.21052631578947, 51.42857142857143, 53.083333333333336, 63.083333333333336, 65.66666666666667, 66.75, 74.875, 85.57142857142857, 76.5, 79.0, 122.0, 58.0, 66.0, 83.0, 83.0, 83.0, 83.0, 83.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    days_list = []
    length_list = []

    for ii, row in enumerate(rows):
        length = minmax.convertRaceLengthMetres(row[5])
        length_list.append(length)
        
        if ii > 0:
            dateStartSplit=rows[ii][9].split('-')
            dateEndSplit=rows[ii-1][9].split('-')
            dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
            dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
            days = dateStart - dateEnd
            days_list.append(days.days)

    days_list_max = max(days_list)
    days_list_min = min(days_list)
    days_list_range = days_list_max - days_list_min

    max_length = max(length_list)
    min_length = min(length_list)
    length_range = max_length - min_length

    for ii, row in enumerate(rows):
        ds_input = []
        ds_result = 4*[0.0]
        if row[4] == 1:
            ds_result[0] = 1.0
        if row[4] == 2:
            ds_result[1] = 1.0
        if row[4] == 3:
            ds_result[2] = 1.0
        if row[4] > 3:
            ds_result[3] = 1.0
        #float(row[4])/float(row[6]) #result_worth_list[row[4]-1] #
        #if row[4] > 9:
        #    ds_result = float(0.9)

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

        odds_split = row[15].split("/")
        try:
            odds = float(odds_split[0])/float(odds_split[1])
        except ValueError as e:
            print (e)
            continue
        normalized_odds = ((float(odds - min_odds)/float(odds_range))*0.8)+0.1
        ds_input.append(float(normalized_odds)) 


        # input 1 will be the race length in meters, normalized
        # against the other races run by this horse.  This
        # should then be scaled to be 0.1 to 0.9
        print("date is %s" % str(row[9]))
        length = minmax.convertRaceLengthMetres(row[5])
        normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
        ds_input.append(float(normalized_length)) 


        # input 2 will be the last race length in meters,
        # normalized and scaled in the same manner as the
        # race length
        print("prev_date is %s" % str(rows[ii-1][9]))
        length = minmax.convertRaceLengthMetres(rows[ii-1][5])
        normalized_length = ((float(length - min_length)/float(length_range))*0.8) + 0.1
        ds_input.append(float(normalized_length)) 

        # input 3 will be the days since last race.  This 
        # is normalized against the longest and shortest time
        # between races for this horse and scaled to 0.1 - 0.9
        dateStartSplit=rows[ii][9].split('-')
        dateEndSplit=rows[ii-1][9].split('-')
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

        try:
            DS
        except NameError:
            DS = SupervisedDataSet(len(ds_input), len(ds_result))
        if ii > 0:
            DS.appendLinked(ds_input, ds_result)

    return DS, days_list_max, days_list_min, max_length, min_length

#def makeTestRace():

#def makeRealRace():
