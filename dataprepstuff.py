import datetime, re
import sys
import random
from numpy import mean, std, array
from sqlstuff2 import SqlStuff2

class dataPrepStuff:
      
    def __init__(self, horses):
        """initialise the class object"""
        self.horses=horses

    def convertRaceLengthMetres(self, distance):
        """convert the mixed letters and numbers of the distance to meters"""
        ss=re.findall('\d+|\D+', distance)
        meters=0
        skip=0
        number=0        
        for idx, s in enumerate(ss):            
            if s=="f":
                meters=meters+(number*201)
                number=0
            elif s=="m":
                meters=meters+(number*(201*8))
                number=0
            elif s==".":
                number=number+(float(ss[idx+1])/10)
                skip=1
            elif s=="m.":
                skip=1
                meters=meters+(number*(201*8))
                number=(float(ss[idx+1])/10)          
            elif s=="y" or s=="yds":
                meters=meters+number
                number=0
            elif skip==0:
                number=number+float(s)
            else:
                skip=0                   
        return meters
        
    def meanStdRaceLength(self, horses):
        """normalise the race length"""
        print "meanStfRaceLength"
        self.raceLengths=[]
        for horse in horses:            
            self.raceLengths.append(self.convertRaceLengthMetres(horse[5]))
        """normalise with x = (x - mean(x))/std(x)"""
        self.raceLengthMean=array(self.raceLengths).mean()
        self.raceLengthStd=array(self.raceLengths).std()

    def normaliseRaceLengthStd(self, idx):
        """normalise the race length"""

        if self.raceLengthStd==0.0:
            return 0.0
        raceLengthn=(self.raceLengths[idx] - self.raceLengthMean)/self.raceLengthStd
        return raceLengthn
   

    def minMaxRaceLength(self,horses):
        print "minMaxRaceLength"
        self.minRaceLength=100000
        self.maxRaceLength=0
        for horse in horses:            
            lengthm=self.convertRaceLengthMetres(horse[5])
            if lengthm < self.minRaceLength:
                self.minRaceLength=lengthm
            if lengthm > self.maxRaceLength:
                self.maxRaceLength=lengthm


    def normaliseRaceLengthMinMax(self, horse):
        """normalise the race length by mapping input to range 0 to 1"""
        oldRange = (self.maxRaceLength - self.minRaceLength)
        newMin=-1.0
        newMax=1.0
        oldValue=self.convertRaceLengthMetres(horse[5])
        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)  
            newValue = (((float(oldValue) - float(self.minRaceLength)) * newRange) / float(oldRange)) + newMin
        return newValue

   
    def normaliseTestRaceLength(self, testRaceLength):
        """normalise the test race length using precalculated mean and std"""
        if self.raceLengthStd==0.0:
            return 0.0
        return (self.convertRaceLengthMetres(testRaceLength)-self.raceLengthMean)/self.raceLengthStd

    def meanStdNumberOfHorses(self,horses):
        self.numberOfHorses=[]
        for horse in horses:
            self.numberOfHorses.append(float(horse[6]))
        self.numberOfHorsesMean=array(self.numberOfHorses).mean()
        self.numberOfHorsesStd=array(self.numberOfHorses).std()


    def normaliseNumberOfHorses(self, idx):
        """normalise the number of horses"""
        if self.numberOfHorsesStd==0.0:
            return 0.0
        numberOfHorsesn=(self.numberOfHorses[idx]-self.numberOfHorsesMean)/self.numberOfHorsesStd
        return numberOfHorsesn

    def normaliseTestNumberOfHorses(self, testNumberOfHorses):
        """normalise the number of horses using the precalculated mean and std"""
        if self.numberOfHorsesStd==0.0:
            return 0.0
        return (float(testNumberOfHorses)-self.numberOfHorsesMean)/self.numberOfHorsesStd

    def meanStdPosition(self, horses):
        """ calculate mean and std dev over all positions in horses"""
        pastPositions=[]
        for horse in horses:
            for pastpos in horse:
                pastPositions.append(float(pastpos[4]))
        self.pastPositionMean=array(pastPositions).mean()
        self.pastPositionStd=array(pastPositions).std()
        

    def normalisePastPosition(self, horses, idx):
        """normalise the position that the horse came"""
        if self.pastPositionStd<0.001:
            return 0.0
        else:
            pastPositionn=(float(horses[idx][4])-self.pastPositionMean)/self.pastPositionStd
        return pastPositionn

    def normaliseTestPastPosition(self, testPosition):
        """normalise the testPosition using precalulate mean and std"""
        print "previous finish pos = " + str(testPosition)
        if self.pastPositionStd==0.0:
            return 0.0
        return (float(testPosition)-self.pastPositionMean)/self.pastPositionStd

    def subJockeyPercentWins(self,jockeys):
        jockeyWins=[]
        SqlStuffInst=SqlStuff2()
        for ii, jockey in enumerate(jockeys):
            if ii!=0:
                if jockey==jockeys[ii-1]:
                    rides=previousRides
                else:
                    rides=SqlStuffInst.getJockey(jockey)
                    previousRides=rides
            else:
                rides=SqlStuffInst.getJockey(jockey)
                previousRides=rides
            wins=0
            for ride in rides:
                if ride[4]==1:
                    wins+=1
            if len(rides)==0:
                jockeyWins.append(float(0.0))
            else:
                jockeyWins.append(float(float(wins)/float(len(rides))))
        return jockeyWins


    def jockeyPercentWins(self, horses):
        jockeys=[]
        for horse in horses:
            jockeys.append(horse[7])
        jockeyWins=self.subJockeyPercentWins(jockeys)
        return jockeyWins
    
    def minMaxJockey(self):
        jockeys=[]
        self.jockeyPerf=[]
        # first create a list where each jockey in the DS appears once
        for horse in self.horses:
            foundJockey=False
            for jockey in jockeys:
                if jockey==horse[7]:
                    foundJockey=True
                    break
            if not foundJockey:
                jockeys.append(horse[7])

        self.minJockey=100000
        self.maxJockey=0
        for ii, jockey in enumerate(jockeys):
            rides=self.getJockey(jockey)
            finish=0.0
            for ride in rides:
                OldRange = (ride[6] - 1)
                if (OldRange == 0):
                    NewValue = 0.0
                else:
                    NewRange = (1.0 - 0.0)  
                    NewValue = (((float(ride[4]) - 1.0) * NewRange) / float(OldRange)) #+ 0
                # the 1.0- here makes it so a better jockey has a bigger value
                finish=finish+float(1.0-NewValue)            
            meanFinishes=(finish/len(rides))
            self.jockeyPerf.append([jockey, meanFinishes])
            if meanFinishes > self.maxJockey:
                self.maxJockey=meanFinishes
            if meanFinishes < self.minJockey:
                self.minJockey=meanFinishes

    def normaliseJockeyMinMax(self, horse=-1, jockeyTest=-1):
        """ normalise the jockey performance based on min (worse)
        max(best) values"""
        if horse != -1:
            for jockey in self.jockeyPerf:
                if jockey[0]==horse[7]:
                    meanFinishes=jockey[1]
                    break
        elif jockeyTest != -1:
            for jockey in self.jockeyPerf:
                if jockey[0]==jockeyTest:
                    meanFinishes=jockey[1]
                    break

        # Now normalise this jockeys performance next to the max and min
        oldRange = (self.maxJockey - self.minJockey)
        newMin=-1.0
        newMax=1.0
        try:
            oldValue=meanFinishes
        except Exception, e:
            print "the jockey being tested was not found in the test data"
            print str(e)
            raise Exception(str(e))

        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)  
            newValue = (((oldValue - self.minJockey) * newRange) / oldRange) + newMin
        return newValue


    
    def minMaxTrainer(self):
        trainers=[]
        self.trainerPerf=[]
        # first create a list where each trainer in the DS appears once
        for horse in self.horses:
            foundTrainer=False
            for trainer in trainers:
                if trainer==horse[13]:
                    foundTrainer=True
                    break
            if not foundTrainer:
                trainers.append(horse[13])

        self.minTrainer=100000
        self.maxTrainer=0
        for ii, trainer in enumerate(trainers):
            rides=self.getTrainer(trainer)
            finish=0.0
            for ride in rides:
                OldRange = (ride[6] - 1)
                if (OldRange == 0):
                    NewValue = 0.0
                else:
                    NewRange = (1.0 - 0.0)  
                    NewValue = (((float(ride[4]) - 1.0) * NewRange) / float(OldRange)) #+ 0
                # the 1.0- here makes it so a better trainer has a bigger value
                finish=finish+float(1.0-NewValue)            
            meanFinishes=(finish/len(rides))
            self.trainerPerf.append([trainer, meanFinishes])
            if meanFinishes > self.maxTrainer:
                self.maxTrainer=meanFinishes
            if meanFinishes < self.minTrainer:
                self.minTrainer=meanFinishes

    def normaliseTrainerMinMax(self, horse=-1, trainerTest=-1):
        """ normalise the trainer performance based on min (worse)
        max(best) values"""
        if horse != -1:
            for trainer in self.trainerPerf:
                if trainer[0]==horse[13]:
                    meanFinishes=trainer[1]
                    break
        elif trainerTest != -1:
            for trainer in self.trainerPerf:
                if trainer[0]==trainerTest:
                    meanFinishes=trainer[1]
                    break

        # Now normalise this trainers performance next to the max and min
        oldRange = (self.maxTrainer - self.minTrainer)
        newMin=-1.0
        newMax=1.0
        oldValue=meanFinishes
        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)  
            newValue = (((oldValue - self.minTrainer) * newRange) / oldRange) + newMin
        return newValue


    def minMaxDraw(self):
        self.draws=[]
        self.minDraw=100000
        self.maxDraw=0
        for ii, horse in enumerate(self.horses):
            self.draws.append(horse[12])
            try:
                tmp=horse[12]+1
            except Exception, e:
                continue
            if horse[12] > self.maxDraw:
                print "set the maxDraw to " + str(horse[12])
                self.maxDraw=horse[12]
            if horse[12] < self.minDraw:
                self.minDraw=horse[12]

    def normaliseDrawMinMax(self, horse=-1, drawTest=-1):
        """ normalise the jockey performance based on min (worse)
        max(best) values"""
        if horse != -1:
            try:
                tmp=horse+1
            except Exception, e:
                return 0.0
            oldValue=horse[12]
        elif drawTest != -1:
            try:
                tmp=drawTest+1
            except Exception, e:
                return 0.0
            oldValue=drawTest
        # Now normalise this trainers performance next to the max and min
        oldRange = (self.maxDraw - self.minDraw)
        newMin=-1.0
        newMax=1.0

        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)
            newValue = (((oldValue - self.minDraw) * newRange) / oldRange) + newMin
        return newValue


    def minMaxWeight(self):
        self.weights=[]
        self.minWeight=100000
        self.maxWeight=0
        for ii, horse in enumerate(self.horses):
            kg=self.convertWeightKilos(horse[3])
            self.weights.append(kg)
            if kg > self.maxWeight:
                print "set the maxWeight to " + str(kg)
                self.maxWeight=kg
            if kg < self.minWeight:
                self.minWeight=kg


    def normaliseWeightMinMax(self, horse=-1, weightTest=-1):
        """ normalise the weight based on min (worse)
        max(best) values"""
        if horse != -1:
            oldValue=self.convertWeightKilos(horse[3])
        elif weightTest != -1:
            oldValue=self.convertWeightKilos(weightTest)
        # Now normalise this trainers performance next to the max and min
        oldRange = (self.maxWeight - self.minWeight)
        newMin=-1.0
        newMax=1.0

        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)
            newValue = (((oldValue - self.minWeight) * newRange) / oldRange) + newMin
        return newValue
        

    def meanStdJockey(self, horses):
        jockeys=[]
        self.meanFinishes=[]
        SqlStuffInst=SqlStuff2()
        # first create a list where each jockey in the DS appears once
        for horse in horses:
            foundJockey=False
            for jockey in jockeys:
                if jockey==horse[7]:
                    foundJockey=True
                    break
            if not foundJockey:
                jockeys.append(horse[7])

        for ii, jockey in enumerate(jockeys):
            rides=SqlStuffInst.getJockey(jockey)
            previousRides=rides
            finish=0.0
            for ride in rides:
                OldRange = (ride[6] - 1)
                if (OldRange == 0):
                    NewValue = 0.0
                else:
                    NewRange = (1 - 0)  
                    NewValue = (((ride[4] - 1) * NewRange) / OldRange) #+ 0
                finish=finish+float(1.0-NewValue)            
                
            self.meanFinishes.append(finish/len(rides))
        self.jockeyMean=array(self.meanFinishes).mean()
        self.jockeyStd=array(self.meanFinishes).std()
    
    def getNormalizedJockeys(self, horses):
        jockeys=[]
        dates=[]
        returnJockeys=[0.0]*len(horses)            

        for horse in horses:
            jockeys.append(horse[7])
            dates.append(datetime.datetime.strptime(str(horse[9]), "%Y-%m-%d"))
        for ii, jockey in enumerate(jockeys):
            if ii!=0:
                if jockey==jockeys[ii-1]:
                    rides=previousRides
                else:
                    rides=self.getJockey(jockey)
                    previousRides=rides
            else:
                rides=self.getJockey(jockey)
                previousRides=rides
            

            sortRide=[]
            sortRide.append(rides[0])
            for jj, ride in enumerate(rides[1:len(rides)]):
                iterations = len(sortRide)
                date1=datetime.datetime.strptime(str(ride[9]), "%Y-%m-%d")
                """if the list date is the same as, or after, the input date then this
                race should  not be included in the training"""
                if date1 < dates[ii]:
                    for idx in range(0, iterations):
                        date0=datetime.datetime.strptime(str(sortRide[idx][9]), "%Y-%m-%d")
                        if date1 > date0:
                            sortRide.insert(idx, ride)
                            break
                        elif idx == (iterations-1):
                            sortRide.append(ride)
            for yy in range(0, len(sortRide)):
                if sortRide[yy][6] == 1:
                    returnJockeys[ii]=returnJockeys[ii]+0.5
                else:
                    returnJockeys[ii]=returnJockeys[ii]+(((float(sortRide[yy][4])-1)/(float(sortRide[yy][6])-1))*(1-0)+0)
            returnJockeys[ii]=returnJockeys[ii]/len(sortRide)
        return returnJockeys

    def getNormalizedJockey(self, jockey, datestr):

        returnJockeys=0.0
        date=datetime.datetime.strptime(str(datestr), "%Y-%m-%d")
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getJockey(jockey)
        if len(rides) == 0:
            return returnJockeys
        sortRide=[]
        sortRide.append(rides[0])
        for jj, ride in enumerate(rides[1:len(rides)]):
            iterations = len(sortRide)
            date1=datetime.datetime.strptime(str(ride[9]), "%Y-%m-%d")
            """if the list date is the same as, or after, the input date then this
            race should  not be included in the training"""
            if date1 < date:
                for idx in range(0, iterations):
                    date0=datetime.datetime.strptime(str(sortRide[idx][9]), "%Y-%m-%d")
                    if date1 > date0:
                        sortRide.insert(idx, ride)
                        break
                    elif idx == (iterations-1):
                        sortRide.append(ride)
        for yy in range(0, len(sortRide)):
            if sortRide[yy][6] == 1:
                returnJockeys=returnJockeys+0.5
            else:                
                returnJockeys=returnJockeys+(((float(sortRide[yy][4])-1)/(float(sortRide[yy][6])-1))*(1-0)+0)
        returnJockeys=returnJockeys/len(sortRide)
        return returnJockeys

    def getNormalizedTrainers(self, horses):
        trainers=[]
        dates=[]
        returnTrainers=[0.0]*len(horses)            

        SqlStuffInst=SqlStuff2()
        for horse in horses:
            trainers.append(horse[13])
            dates.append(datetime.datetime.strptime(str(horse[9]), "%Y-%m-%d"))
        for ii, trainer in enumerate(trainers):
            if ii!=0:
                if trainer==trainers[ii-1]:
                    rides=previousRides
                else:
                    rides=SqlStuffInst.getTrainer(trainer)
                    previousRides=rides
            else:
                rides=SqlStuffInst.getTrainer(trainer)
                previousRides=rides
            

            sortRide=[]
            sortRide.append(rides[0])
            for jj, ride in enumerate(rides[1:len(rides)]):
                iterations = len(sortRide)
                date1=datetime.datetime.strptime(str(ride[9]), "%Y-%m-%d")
                """if the list date is the same as, or after, the input date then this
                race should  not be included in the training"""
                if date1 < dates[ii]:
                    for idx in range(0, iterations):
                        date0=datetime.datetime.strptime(str(sortRide[idx][9]), "%Y-%m-%d")
                        if date1 > date0:
                            sortRide.insert(idx, ride)
                            break
                        elif idx == (iterations-1):
                            sortRide.append(ride)
            for yy in range(0, len(sortRide)):
                if sortRide[yy][6] == 1:
                    returnTrainers[ii] = 0.5
                else:
                    returnTrainers[ii]=returnTrainers[ii]+(((float(sortRide[yy][4])-1)/(float(sortRide[yy][6])-1))*(1-0)+0)
            returnTrainers[ii]=returnTrainers[ii]/len(sortRide)
        return returnTrainers

    def getNormalizedTrainer(self, trainer, datestr):

        returnTrainers=0.0
        date=datetime.datetime.strptime(str(datestr), "%Y-%m-%d")
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getTrainer(trainer)
        if len(rides) == 0:
            return returnTrainers
        sortRide=[]
        sortRide.append(rides[0])
        for jj, ride in enumerate(rides[1:len(rides)]):
            iterations = len(sortRide)
            date1=datetime.datetime.strptime(str(ride[9]), "%Y-%m-%d")
            """if the list date is the same as, or after, the input date then this
            race should  not be included in the training"""
            if date1 < date:
                for idx in range(0, iterations):
                    date0=datetime.datetime.strptime(str(sortRide[idx][9]), "%Y-%m-%d")
                    if date1 > date0:
                        sortRide.insert(idx, ride)
                        break
                    elif idx == (iterations-1):
                        sortRide.append(ride)
        for yy in range(0, len(sortRide)):
            if sortRide[yy][6] == 1:
                returnTrainers = 0.5
            else:
#                print "position = " + str(sortRide[yy][4]) + " out of " + str(sortRide[yy][6]) + "horses"
#                print "trainer value is " + str((((float(sortRide[yy][4])-1)/(float(sortRide[yy][6])-1))*(1-0)+0))
                returnTrainers=returnTrainers+(((float(sortRide[yy][4])-1)/(float(sortRide[yy][6])-1))*(1-0)+0)
#                print "cumulative trainer is " + str(returnTrainers)
        returnTrainers=returnTrainers/len(sortRide)
#        print "the number of trainer is " + str(len(sortRide)) + "so returning " + str(returnTrainers)
        return returnTrainers

    
    def meanStdTrainer(self, horses):
        """ normalise the trainers"""
        #since the trainer reamains the same for the horse it contains no informaion
        #If the trainer is given a value for average placing and this is then compared
        #to the other trainers that have horses in the race then it contains some
        #useful data (perhaps)
        #getAllTrainersInRace(horses


        trainers=[]
        self.meanTrainerFinishes=[]
        SqlStuffInst=SqlStuff2()
        # first get a list where each trainer in the DS features only once
        for horse in horses:
            foundTrainer=False
            for trainer in trainers:
                if trainer==horse[13]:
                    foundTrainer=True
                    break
            if not foundTrainer:
                trainers.append(horse[13])

        for ii, trainer in enumerate(trainers):
            rides=SqlStuffInst.getTrainer(trainer)
            previousRides=rides
            finish=0.0
            for ride in rides:
                OldRange = (ride[6] - 1)
                if (OldRange == 0):
                    NewValue = 0.0
                else:
                    NewRange = (1 - 0)  
                    NewValue = (((ride[4] - 1) * NewRange) / OldRange) #+ 0
                finish=finish+float(1.0-NewValue)            
            # calculate the mean for just this trainer
            self.meanTrainerFinishes.append(finish/len(rides))
        # calculate the mean and std dev for all the trainers in the DS
        self.trainerMean=array(self.meanTrainerFinishes).mean()
        self.trainerStd=array(self.meanTrainerFinishes).std()

    def normaliseTrainer(self, trainer):
        """ normalise the trainer for the idx horse"""
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getTrainer(trainer)
        previousRides=rides
        finish=0.0
        for ride in rides:
            OldRange = (ride[6] - 1)
            if (OldRange == 0):
                NewValue = 0.0
            else:
                NewRange = (1 - 0)  
                NewValue = (((ride[4] - 1) * NewRange) / OldRange) #+ 0
            finish=finish+float(1.0-NewValue)            

        # calculate the mean for just this trainer
        meanTrainerFinishes=(finish/len(rides))
        if self.trainerStd<0.001:
            return 0.0
        else:
            return (meanTrainerFinishes-self.trainerMean)/self.trainerStd
        
    def normaliseTestTrainer(self, testTrainer):
        """ normalise the trainer for the horse under test"""
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getTrainer(testTrainer)
        if len(rides)==0:
            print "no trainer called " + str(testTrainer) + " in the database"
            return 0.0
        finish=0.0
        for ride in rides:
            OldRange = (ride[6] - 1)
            if (OldRange == 0):
                NewValue = 0.0
            else:
                NewRange = (1 - 0)  
                NewValue = (((ride[4] - 1) * NewRange) / OldRange) #+ 0
            finish=finish+float(1.0-NewValue)            

        meanFinish=(finish/len(rides))
        if self.trainerStd<0.001:
            return 0.0
            #(meanFinish-self.jockeyMean)
        else:
            #print "returning norm test jockey = " + str((meanFinish-self.jockeyMean)/self.jockeyStd)
            return (meanFinish-self.trainerMean)/self.trainerStd
       

    def normaliseJockey(self, jockey):
        """normalise the jockey"""
        """the jockey will be represented by their average finish position"""
        # calculate the mean for just this Jockey
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getJockey(jockey)
        previousRides=rides
        finish=0.0
        
        # for each result translate the result range to 0 to 1
        for ride in rides:
            OldRange = (ride[6] - 1)
            if (OldRange == 0):
                NewValue = 0.0
            else:
                NewRange = (1 - 0)  
                NewValue = (((ride[4] - 1) * NewRange) / OldRange) #+ 0
            finish=finish+float(1.0-NewValue)            

        meanFinishes=(finish/len(rides))

        if self.jockeyStd<0.001:
            return 0.0
        else:
            return (meanFinishes-self.jockeyMean)/self.jockeyStd
            
    def normaliseTestJockey(self, testJockey):
        """normalise the test jockeys performance with the precalulated mean and std"""
        
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getJockey(testJockey)
        if len(rides)==0:
            print "no jockey called " + str(testJockey) + " in the database"
            return 0.0
        finish=0.0
        for ride in rides:
            finish=finish+float(ride[4])/float(ride[6])            
        meanFinish=(finish/len(rides))
        if self.jockeyStd<0.001:
            return 0.0
            #(meanFinish-self.jockeyMean)
        else:
            #print "returning norm test jockey = " + str((meanFinish-self.jockeyMean)/self.jockeyStd)
            return (meanFinish-self.jockeyMean)/self.jockeyStd

    def convertWeightKilos(self, weight):
        """convert the stone, pounds weight to kilos"""
        ss=re.findall('\d+|\D+', weight)
        if len(ss) < 3:
            return 60.0
        else:
            return (float(ss[0])*6.35+float(ss[2])*0.45)
        #for idx, s in enumerate(ss):          
        
    def meanStdWeight(self, horses):
        self.weights=[]        
        for horse in horses:
            if horse[3] != ' ':
                self.weights.append(self.convertWeightKilos(horse[3]))
            else:
                self.weights.append(60.0)
        self.weightMean=array(self.weights).mean()
        self.weightStd=array(self.weights).std()

        
    def normaliseWeight(self, idx):
        """normalise the weight carried by the horse"""
        if self.weightStd < 0.001:
            weightn=0.0
        else:
            weightn=(self.weights[idx]-self.weightMean)/self.weightStd
       
        return weightn

    def normaliseTestWeight(self, testWeight):
        """normalise the test weight using the precalculated mean and std"""
        if testWeight == ' ':
            weight=self.weightMean
        else:
            weight=self.convertWeightKilos(testWeight)
        if self.weightStd < 0.001:
            return 0.0
        else:
            return (weight-self.weightMean)/self.weightStd

    def meanStdGoing(self, horses, verbose=0):
        self.goings=[]
        """ the possible goings for UK and Ireland surfaces are...
        hard, firm, good to firm, good, good to soft (aka yielding), soft, heavy
        the artificial surfaces are...        
        fast,  standard to fast, standard, standard to slow, slow
        The U.S. goings are different so avoid betting on US races!!!"""

        """ The artificial surfaces are padded so that they create a similar scale to
        the non-artificial surface (not sure that's a good idea??).  All values in the
        tables are doubles allowing 'Very' to have an effect by adding or decrememnting 1"""

        self.possibleSurfaces=["Hard", "Firm", "Good", "Soft", "Heavy"]
        self.possibleASurfaces=["Fast","filler1", "Standard", "filler2", "Slow"]
        for jj, horse in enumerate(horses):
            numberOfTerms=0
            going=0.0
            for ii, possibleGoing in enumerate(self.possibleSurfaces):
                for kk in horse[8].split():
                    if possibleGoing==kk.strip():
                        going+=2.0*ii
                        numberOfTerms+=1
                    elif kk.strip()=="Very":
                        if ii < 2:
                            going-=1.0
                        elif ii > 2:
                            going+=1.0
                    elif kk.strip()=="Yielding":
                        going+=2.0*(2.0+3.0)
                        numberOfTerms+=2                
               
            for ii, possibleGoing in enumerate(self.possibleASurfaces):
                for kk in horse[8].split():
                    if possibleGoing==kk.strip():
                        going+=2.0*ii
                        numberOfTerms+=1
           
            if numberOfTerms==0:
                print "unrecognised going " + horse[8]
                self.goings.append(float(4.0))                    
            else:
                self.goings.append(float(going/numberOfTerms))                    
        self.goingMean=array(self.goings).mean()
        self.goingStd=array(self.goings).std()
        if verbose != 0:
            print self.possibleSurfaces
            print self.possibleASurfaces
            print self.goings
            print self.goingMean
            print self.goingStd

    def gatherGoing(self):
        """gather all of the going terms that have been used in previous races"""
        wordList=[]
        SqlStuffInst=SqlStuff2()
        allGoing=SqlStuffInst.getAllGoing()
        # sort the going into a list
        for idx, going in enumerate(allGoing):
            goingstr=str(going).replace('(u\'','').replace('\',)','')
            if idx==0:
                wordList.append(goingstr)
            else:
                for idz, word in enumerate(wordList):
                    #if goingstr=="Very":
                    #    break
                    if word==goingstr:
                        break;

                    if idz==len(wordList)-1:
                        if word!=goingstr:
                            wordList.append(goingstr)
#        for idx, word in enumerate(wordList):
#            print str(word)
        return wordList

    def meanStdResult(self, horses):
        self.results=[]
        for ii, horse in enumerate(horses):
            # calculate the mean for just this trainer
            self.results.append(self.convertRaceLengthMetres(horse[5])/horse[14])

        # calculate the mean and std dev for all the trainers in the DS
        self.resultMean=array(self.results).mean()
        self.resultStd=array(self.results).std()

    
    def normaliseResult(self, idx):
        """normalise the result"""
        if self.resultStd < 0.001:
            return 0.0
        resultn=(self.results[idx]-self.resultMean)/self.resultStd
        return resultn


    def normaliseGoing(self, horses, idx):
        """normalise going"""
        if self.goingStd < 0.001:
            return 0.0
        goingn=(self.goings[idx]-self.goingMean)/self.goingStd
        return goingn

    def normaliseTestGoing(self, testGoing):
        """normalise the testGoing using the precalculated mean and std"""
        goings=[]
        numberOfTerms=0
        going=0.0
        for ii, possibleGoing in enumerate(self.possibleSurfaces):
            for kk in testGoing.split():
                if possibleGoing==kk.strip():
                    going+=2.0*ii
                    numberOfTerms+=1
                elif kk.strip()=="Very":
                    if ii < 2:
                        going-=1.0
                    elif ii > 2:
                        going+=1.0
                elif kk.strip()=="Yielding":
                    going+=2.0*(2.0+3.0)
                    numberOfTerms+=2                
                            
        for ii, possibleGoing in enumerate(self.possibleASurfaces):
            for kk in testGoing.split():
                if possibleGoing==kk.strip():
                    going+=2.0*ii
                    numberOfTerms+=1
           
        goings.append(float(going/numberOfTerms))                    
        if len(goings)!=1:
            print "unrecognised going " + testGoing
            return 0.0
        if self.goingStd < 0.001:
            return 0.0
        return (goings[0]-self.goingMean)/self.goingStd
        
    def subSortReduceJockey(self, inputJockey, x, datestr):
        """ sort the jockeys by date and return the x most recent after datastr"""
        rides=inputJockey #sortDistance
        sortRide=[]
        sortRide.append(rides[0])
        for ii in rides[1:len(rides)]:
            iterations = len(sortRide)
            date1=datetime.datetime.strptime(str(ii[9]), "%Y-%m-%d")
            """if the list date is the same as, or after, the input date then this
            race should  not be included in the training"""
            if date1 < date:
                for idx in range(0, iterations):
                    date0=datetime.datetime.strptime(str(sortHorse[idx][9]), "%Y-%m-%d")
                    if date1 > date0:
                        sortRide.insert(idx, ii)
                        break
                    elif idx == (iterations-1):
                        sortRide.append(ii)
        return sortRide[0:min(x,len(sortRide))]

    def subSortReduce(self, inputHorses, x, datestr=-1, distance=-1, position=-1, verbose=0):
        """ sort the results by date.  If input date is present in sorted list,
        the remove it.  Return the most recent x"""
        #horse[9] is the date
        horses=inputHorses
        if len(horses) == 1:
            return horses
            
        if position != -1:
            sortPosition=[]
            for horse in inputHorses:
                if horse[4]==position:
                    sortPosition.append(horse)
            if distance==-1 and datestr==-1:
                return sortPosition[0:min(x,len(sortPosition))]
            horses=sortPosition

        if distance != -1:
            distancem=self.convertRaceLengthMetres(distance)
            sortDistance=[]
            sortDistance.append(horses[0])
            for ii in horses[1:len(horses)]:
                iterations = len(sortDistance)
                distance1=self.convertRaceLengthMetres(ii[5])
                distanceDiff=abs(distancem-distance1)
                for idx in range(0, iterations):
                    distanceDiff1=abs(distancem-self.convertRaceLengthMetres(sortDistance[idx][5]))
                    if distanceDiff1 > distanceDiff:
                        sortDistance.insert(idx,ii)
                        break
                    elif idx == (iterations-1):
                        sortDistance.append(ii)
            if datestr==-1:
                return sortDistance[0:min(x,len(sortDistance))]
            horses=sortDistance
        if datestr==-1:
            raise Exception("No sort argument was not -1")
        date=datetime.datetime.strptime(str(datestr), "%Y-%m-%d")
        sortHorse=[]
        try:
            sortHorse.append(horses[0])
        except Exception, e:
            print "A previous sort has removed all entries so cannot sort date"
            raise Exception(str(e))

        for ii in horses[1:len(horses)]:
            iterations = len(sortHorse)
            date1=datetime.datetime.strptime(str(ii[9]), "%Y-%m-%d")
            """if the list date is the same as, or after, the input date then this should 
            race should  not be included in the training"""
            if date1 < date:
                for idx in range(0, iterations):
                    date0=datetime.datetime.strptime(str(sortHorse[idx][9]), "%Y-%m-%d")
                    if date1 > date0:
                        sortHorse.insert(idx, ii)
                        break
                    elif idx == (iterations-1):
                        sortHorse.append(ii)
            elif verbose != 0:
                print "removing " + str(date1) + " from the training list"
        if verbose == 2:
            print "date under test is " + str(date)
            print "races sorted by date for training are..."
            print sortHorse[0:min(x,len(sortHorse))]
        return sortHorse[0:min(x,len(sortHorse))]

        
    def subReduce(self, inputHorses, history, date):
        """ reduce the list by removing all horses that dont't have
        at least "history" wins"""
        reduceHorse=[]
        historyHorses=[]
        print "subReduce"
        #print inputHorses
        for idx, horse in enumerate(inputHorses):
            if idx%100==0:
                print "subReduce " + str(idx) + " of " + str(len(inputHorses))
            # This means that the database entry had no time assosciated with it
            if horse[14]==0:
                continue
            sqlhorses=self.getHorse(horse[1])
            historyHorse=self.subSortReduce(sqlhorses, history, date, distance=-1, position=-1) #horse[5])
            if len(historyHorse)>=history:
                reduceHorse.append(horse)
                historyHorses.append(historyHorse)

        return historyHorses, reduceHorse

    def subReduceDraw(self):
        """ remove all horses that have no draw"""
        drawHorses=[]
        noDrawHorses=[]
        for horse in self.horses:
            try:
                tmp=horse[12]+1
                drawHorses.append(horse)
            except Exception, e:
                noDrawHorses.append(horse)
                continue

        self.horses=noDrawHorses
        
              

    def subUsefuliseInputs(self, allInputs, horses, verbose=0):
        """ identify input sets that are more than 2stds away from the mean.
        remove them from the horses and allInputs and return the modified data
        sets"""
        allInputsReturn=allInputs
        horsesReturn=horses
        indexToRemove=[]
        for idx, horse in enumerate(horses):
            if abs(self.convertRaceLengthMetres(horse[5])-self.raceLengthMean) > (2*self.raceLengthStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.raceLengthStd)
                    print "input is " + str(self.convertRaceLengthMetres(horses[idx][5]))
                    print "mean is " + str(self.raceLengthMean)
                    print "string value was " + str(horses[idx][5])
                    print "removing abnormal running length from dataset"
                continue

            if abs(float(horses[idx][6])-self.numberOfHorsesMean) > (2*self.numberOfHorsesStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.numberOfHorsesStd)
                    print "input is " + str(horse[6])
                    print "mean is " + str(self.numberOfHorsesMean)
                    print "removing abnormal number of horses from dataset"
                continue

            """if abs(self.meanFinishes[idx]-self.jockeyMean) > (2*self.jockeyStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.jockeyStd)
                    print "input is " + str(self.meanFinishes[idx])
                    print "jockey name is " + str(horse[7])
                    print "mean is " + str(self.jockeyMean)
                    print "removing abnormal jockey from dataset"
                continue
            """
            if abs(self.convertWeightKilos(horse[3])-self.weightMean) > (2*self.weightStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.weightStd)
                    print "input is " + str(self.convertWeightKilos(horse[3]))
                    print "mean is " + str(self.weightMean)
                    print "removing abnormal weight from dataset"
                continue
                
            if abs(self.goings[idx]-self.goingMean) > (2*self.goingStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.goingStd)
                    print "input is " + str(horse[8])
                    print "mean is " + str(self.goingMean)
                    print "removing abnormal going from dataset"
                continue

        allInputsReturn=allInputs
        horsesReturn=horses
        indexToRemove=[]
        for idx, horse in enumerate(horses):
            if (horse[4] > 4):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "horse name is " + str(horse[1])
                    print "finishing position is " + str(horses[idx][4])
                    print "removing non-first place from useful inputs"
                continue
        

        for idx in reversed(indexToRemove):
            allInputsReturn.pop(idx)
            horsesReturn.pop(idx)

        return allInputsReturn, horsesReturn



    def getHorsesInRaces(self):
        """ put the horses in groups which is a race"""

        # first create a list of all the race name/time/date
        races=[]
        horseNameTimeDate= [self.horses[0][9], self.horses[0][10], self.horses[0][11]]
        races.append(horseNameTimeDate)
        for horse in self.horses:
            horseNameTimeDate= [horse[9], horse[10], horse[11]]
            foundRace=False
            for race in races:
                if horseNameTimeDate == race:
                    foundRace=True
                    break
            if foundRace == False:
                races.append(horseNameTimeDate)
                    
        raceHorses=[]
        for race in races:
            raceHorse=[]
            for horse in self.horses:
                horseNameTimeDate= [horse[9], horse[10], horse[11]]
                if horseNameTimeDate == race:
                    raceHorse.append(horse)
                
            raceHorses.append(raceHorse)

        self.raceHorses=raceHorses
        return raceHorses



    def correlateJockey(self):
        """ loop through the races and check to see if the 
        best jockey won"""
        
        # first need to find how good each jockey is and put the result in
        # an array that is in the same order as the horse in the races.
        self.minMaxJockey()
        tallyBest=0
        tallySecond=0
        tallyOther=0
        for raceHorse in self.raceHorses:
            bestJockey=0
            bestJockeyPos=0
            for horse in raceHorse:
                if bestJockey < self.normaliseJockeyMinMax(horse=horse):
                    bestJockey=self.normaliseJockeyMinMax(horse=horse)
                    bestJockeyPos=horse[4]
            print "At " + str(horse[9]) + str(horse[10]) + str(horse[11]) + "best Jockey came " + str(bestJockeyPos)
            
            if bestJockeyPos == 1:
                tallyBest=tallyBest+1
            if bestJockeyPos == 2:
                tallySecond=tallySecond+1
            if bestJockeyPos > 2:
                tallyOther=tallyOther+1

        print "from " + str(len(self.raceHorses)) + " races, the best jockey won " + str(tallyBest) + " times"
        print "from " + str(len(self.raceHorses)) + " races, the best jockey came second " + str(tallySecond) + " times"
        print "from " + str(len(self.raceHorses)) + " races, the best jockey was third or worse " + str(tallyOther) + " times"
        print "the average number of horses per race was " + str(len(self.horses)/len(self.raceHorses))



    def correlateTrainer(self):
        """ loop through the races and check to see if the 
        best trainer won"""
        
        # first need to find how good each trainer is and put the result in
        # an array that is in the same order as the horse in the races.
        self.minMaxTrainer()
        tallyBest=0
        tallySecond=0
        tallyOther=0
        for raceHorse in self.raceHorses:
            bestTrainer=0
            bestTrainerPos=0
            for horse in raceHorse:
                if bestTrainer < self.normaliseTrainerMinMax(horse=horse):
                    bestTrainer=self.normaliseTrainerMinMax(horse=horse)
                    bestTrainerPos=horse[4]
            print "At " + str(horse[9]) + str(horse[10]) + str(horse[11]) + "best Trainer came " + str(bestTrainerPos)
            
            if bestTrainerPos == 1:
                tallyBest=tallyBest+1
            if bestTrainerPos == 2:
                tallySecond=tallySecond+1
            if bestTrainerPos > 2:
                tallyOther=tallyOther+1

        print "from " + str(len(self.raceHorses)) + " races, the best trainer won " + str(tallyBest) + " times"
        print "from " + str(len(self.raceHorses)) + " races, the best trainer came second " + str(tallySecond) + " times"
        print "from " + str(len(self.raceHorses)) + " races, the best trainer was third or worse " + str(tallyOther) + " times"
        print "the average number of horses per race was " + str(len(self.horses)/len(self.raceHorses))


    def correlateDraw(self):
        """ analyse how the draw correlates with winning"""
        self.minMaxDraw()
        print "the min draw was " + str(self.minDraw)
        print "the max draw was " + str(self.maxDraw)
        draws=[0]*(self.maxDraw+1)
        drawsWins=[0]*(self.maxDraw+1)
        print "the length of draws is " + str(len(draws))
        for horse in self.horses:
            try:
                tmp=horse[12]+1
            except Exception, e:
                continue
            draws[horse[12]]+=1
            if horse[4]==1:
                drawsWins[horse[12]]+=1

        for ii, draw in enumerate(draws):
            if draw == 0:
                drawpc = 0
            else:
                drawpc = (float(drawsWins[ii])/float(draw))*100
            print "There were " + str(drawsWins[ii]) + " wins at draw " + str(ii) + " of " + str(draw) + " races = " + str(drawpc)

    def correlateWeight(self):
        """ normalise each wgt with respect to the min and max weights of
        all horses.  Then count how many horses fall into each weight range
        and how many winners are in each weight range"""
        self.minMaxWeight()
        print "the min weight was " + str(self.minWeight)
        print "the max weight was " + str(self.maxWeight)
        weights=[0]*11
        weightsWins=[0]*11
        print "the length of weights is " + str(len(self.weights))
        for horse in self.horses:
            nweight=round(self.normaliseWeightMinMax(horse=horse),1)*10
            weights[int(nweight)]+=1
            if horse[4]==1:
                weightsWins[int(nweight)]+=1

        for ii, weight in enumerate(weights):
            #if draw == 0:
            #    drawpc = 0
            #else:
            #    drawpc = (float(drawsWins[ii])/float(draw))*100
            print "There were " + str(weightsWins[ii]) + " wins at weight " + str(ii) + " of " + str(weight) + " horses at this weight"

    def getHorse(self, horseName):
        """ return a list of entries from the loaded database for 
        this horse """
        returnHorse = []
        for horse in self.horses:
            if horse[1]==horseName:
                returnHorse.append(horse)
        return returnHorse

    def getJockey(self, jockeyName):
        """ return a list of entries from the loaded database for 
        this horse """
        returnJockey = []
        for horse in self.horses:
            if horse[7]==jockeyName:
                returnJockey.append(horse)
        return returnJockey

    def getTrainer(self, trainerName):
        """ return a list of entries from the loaded database for 
        this horse """
        returnTrainer = []
        for horse in self.horses:
            if horse[13]==trainerName:
                returnTrainer.append(horse)
        return returnTrainer



    def subNormaliseInputs(self):
        """normalise the inputs.  horses is a list of all of the races that the
        horse under analysis has been in.  The function called for normalising
        take all of these races into consideration in comparison to a particular
        race idx.  This way each race gets normalised in turn"""        
        horsesn=[[0 for x in xrange(3)] for x in xrange(len(self.horses))]
        print "subNormaliseInputs calculating means and std devs"
        #self.minMaxRaceLength(horses)
        self.minMaxJockey()
        #self.meanStdNumberOfHorses(horses)
        #self.meanStdWeight(horses)
        self.minMaxTrainer()
        #self.minMaxDraw()
        self.minMaxWeight()
        #self.meanStdGoing(horses)
        #self.meanStdPosition(historyHorses)
                  
        for idx, horse in enumerate(self.horses):
            #if idx%100==0:
            #    print "subNormaliseInputs calculating inputs " + str(idx) + " of " + str(len(self.horses))
            #horsesn[idx][0]=self.normaliseRaceLengthMinMax(horse)
            #horsesn[idx][1]=self.normaliseNumberOfHorses(idx)
            #horsesn[idx][1]=self.normalisePastPosition(historyHorses[idx], 0)
            #horsesn[idx][3]=self.normalisePastPosition(historyHorses[idx], 1)
            #horsesn[idx][4]=self.normalisePastPosition(historyHorses[idx], 2)
            #horsesn[idx][5]=self.normalisePastPosition(historyHorses[idx], 3)
            #horsesn[idx][6]=self.normalisePastPosition(historyHorses[idx], 4)
            horsesn[idx][0]=self.normaliseJockeyMinMax(horse=horse)
            #horsesn[idx][2]=self.normaliseWeight(idx)
            horsesn[idx][1]=self.normaliseTrainerMinMax(horse=horse)
            #horsesn[idx][2]=self.normaliseDrawMinMax(horse=horse)
            horsesn[idx][2]=self.normaliseWeightMinMax(horse=horse)
            
       
        return horsesn

    def subNormaliseOutputs(self):
        """normalise the outputs.  horses is a list of all of the races that the
        horse under analysis has been in.  The function called for normalising
        take all of these races into consideration in comparison to a particular
        race idx.  This way each race gets normalised in turn"""        
        horsesn=[[0 for x in xrange(1)] for x in xrange(len(self.horses))]
        print "subNormaliseOutputs calculating means and std devs"
                          
        for idx, horse in enumerate(self.horses):
            """if idx%100==0:
                print "subNormaliseInputs calculating outputs " + str(idx) + " of " + str(len(self.horses))

            if horse[4]==1:
                horsesn[idx][0]=1.0
            else:
                horsesn[idx][0]=0.0"""
            
            horsesn[idx][0]=1.0 - float(horse[4])/float(horse[6])

        return horsesn

        

    def testFunction(self, jockeyName, trainerName, numberHorses, raceLength, weight, going, draw, date, verbose=0):#, trainerName):
        """blah"""
        #jockeyNames=self.getNormalizedJockey(jockeyName, date)
        #trainerNames=self.getNormalizedTrainer(trainerName, date)

        testn=[None]*3
        #testn[0]=self.normaliseTestRaceLength(raceLength)
        #testn[1]=self.normaliseTestNumberOfHorses(numberHorses)
        #testn[2]=self.normaliseTestPastPosition(horses[len(horses)-1][4])
        try:
            testn[0]=self.normaliseJockeyMinMax(jockeyTest=jockeyName)
        except Exception, e:
            raise Exception(str(e))
        #testn[1]=self.normaliseTestWeight(weight)
        #testn[4]=self.NeuralNetworkStuffInst.subJockeyPercentWins(jockeyNames)[0]
        testn[1]=self.normaliseTrainerMinMax(trainerTest=trainerName)
        #testn[2]=self.normaliseDrawMinMax(drawTest=draw)
        testn[2]=self.normaliseWeightMinMax(weightTest=weight)
        #testn[5]=self.normaliseTestTrainer(trainerName)
        #testn[3]=jockeyNames
        #print "testFunction trainerName value is " + str(trainerNames)
        #testn[5]=trainerNames
        
        #testn[4]=self.NeuralNetworkStuffInst.normaliseTestDraw(draw, numberHorses)
        #testn[5]=1.0
        return testn

