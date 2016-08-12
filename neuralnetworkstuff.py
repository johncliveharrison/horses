import datetime, re
from numpy import mean, std, array
from sqlstuff2 import SqlStuff2

class NeuralNetworkStuff:
      
    def __init__(self):
        """initialise the class object"""
        self.x1=[None]*4        
        self.x2=[None]*13
        self.wh=[[0 for x in xrange(4)] for x in xrange(13)]
        self.wo=[None]*13
        self.mu=0.7
        
    def subLoadX1(self, horse):
        """load the input variables into the X1 layer of the network"""
        """ResultStuff.horseNames[idx].replace("'", "''"),\
        ResultStuff.horseAges[idx], ResultStuff.horseWeights[idx], idx+1, \
        ResultStuff.raceLength, ResultStuff.numberOfHorses, ResultStuff.jockeys[idx].replace("'", "''"), \
        ResultStuff.going, ResultStuff.raceDate) 
        self.x1[0]=horse.raceLength
        self.x1[1]=horse."""

    def subFindHorseError(self, trainingHorseResult):
        """find the error for this horses set of inputs"""
        for hh in range(0, len(self.wo)):
            acc=0.0
            for ii in range(0, len(self.x1)):                
                acc=acc+(float(self.x1[ii])*float(self.wh[hh][ii]))
                
            self.x2[hh]=1/(1+exp(-acc))
      #      print "acc = " + str(acc)
      #  print "x1 = " + str(self.x1)
      #  print "x2 = " + str(self.x2)
        acc=0.0
        for hh in range(0, len(self.wo)):
            acc=acc+self.x2[hh]*self.wo[hh]

        self.x3=1/(1+exp(-acc))
        self.elet=(trainingHorseResult-self.x3)
        #if trainingHorseResult == 1:
        #    self.elet=self.elet*5
    #    print "wanted " + str(trainingHorseResult) + " got " + str(self.x3)
    #    print "error was " + str(self.elet)
        return self.elet                       
            

    def subFindNewWeights(self):
        """calculate the new weights for hidden and output layers"""
        for hh in range(0, len(self.wo)):
            for ii in range(0, len(self.x1)):
                slopeo=self.x3*(1-self.x3)
                slopeh=self.x2[hh]*(1-self.x2[hh])
                dx3dw=self.x1[ii]*slopeh*self.wo[hh]*slopeo
                self.wh[hh][ii]=self.wh[hh][ii]+dx3dw*self.elet*self.mu

            slopeo=self.x3*(1-self.x3)
            dx3dw=self.x2[hh]*slopeo
            self.wo[hh]=self.wo[hh]+dx3dw*self.elet*self.mu
            

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
            elif s=="y":
                meters=meters+number
                number=0
            elif skip==0:
                number=number+float(s)
            else:
                skip=0                   
        return meters
        
    def meanStdRaceLength(self, horses):
        """normalise the race length"""
        self.raceLengths=[]
        for horse in horses:            
            self.raceLengths.append(self.convertRaceLengthMetres(horse[5]))
        """normalise with x = (x - mean(x))/std(x)"""
        self.raceLengthMean=array(self.raceLengths).mean()
        self.raceLengthStd=array(self.raceLengths).std()
    

    def normaliseRaceLength(self, idx):
        """normalise the race length"""

        if self.raceLengthStd==0.0:
            return 0.0
        raceLengthn=(self.raceLengths[idx] - self.raceLengthMean)/self.raceLengthStd
        return raceLengthn

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

    def normalisePastPosition(self, horses, idx):
        """normalise the position that the horse came"""
        pastPositions=[]
        for horse in horses:
            pastPositions.append(float(horse[4]))
        self.pastPositionMean=array(pastPositions).mean()
        self.pastPositionStd=array(pastPositions).std()
        if idx==0:
            pastPositionn=0.0
        else:
            pastPositionn=(pastPositions[idx-1]-self.pastPositionMean)/self.pastPositionStd
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
    


    def meanStdJockey(self, horses):
        jockeys=[]
        self.meanFinishes=[]
        SqlStuffInst=SqlStuff2()
        for horse in horses:
            jockeys.append(horse[7])
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
            finish=0.0
            for ride in rides:
                finish=finish+float(ride[4])/float(ride[6])            
            self.meanFinishes.append(finish/len(rides))
        self.jockeyMean=array(self.meanFinishes).mean()
        self.jockeyStd=array(self.meanFinishes).std()
        
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
        for horse in horses:
            trainers.append(horse[13])
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
            finish=0.0
            for ride in rides:
                finish=finish+float(ride[4])/float(ride[6])
            self.meanTrainerFinishes.append(finish/len(rides))
        self.trainerMean=array(self.meanTrainerFinishes).mean()
        self.trainerStd=array(self.meanTrainerFinishes).std()

    def normaliseTrainer(self, idx):
        """ normalise the trainer for the idx horse"""
        if self.trainerStd<0.001:
            return 0.0
        else:
            return (self.meanTrainerFinishes[idx]-self.trainerMean)/self.trainerStd
        
    def normaliseTestTrainer(self, testTrainer):
        """ normalise the trainer for the horse under test"""
        SqlStuffInst=SqlStuff2()
        rides=SqlStuffInst.getTrainer(testTrainer)
        if len(rides)==0:
            print "no trainer called " + str(testTrainer) + " in the database"
            return 0.0
        finish=0.0
        for ride in rides:
            finish=finish+float(ride[4])/float(ride[6])            
        meanFinish=(finish/len(rides))
        if self.trainerStd<0.001:
            return 0.0
            #(meanFinish-self.jockeyMean)
        else:
            #print "returning norm test jockey = " + str((meanFinish-self.jockeyMean)/self.jockeyStd)
            return (meanFinish-self.trainerMean)/self.trainerStd
       

    def normaliseJockey(self, idx):
        """normalise the jockey"""
        """the jockey will be represented by their average finish position"""
        
        if self.jockeyStd<0.001:
            return 0.0
            #meanFinishes[idx]-self.jockeyMean
        else:
            #print "returning norm jockey = " + str((meanFinishes[idx]-self.jockeyMean)/self.jockeyStd)
            return (self.meanFinishes[idx]-self.jockeyMean)/self.jockeyStd
            
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
        return (float(ss[0])*6.35+float(ss[2])*0.45)
        #for idx, s in enumerate(ss):          
        
    def meanStdWeight(self, horses):
        self.weights=[]        
        for horse in horses:
            if horse[3] != ' ':
                self.weights.append(self.convertWeightKilos(horse[3]))
            else:
                self.weights.append(10.0)
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
        
    def subSortReduce(self, inputHorses, x, datestr, distance, verbose=1):
        """ sort the results by date.  If input date is present in sorted list,
        the remove it.  Return the most recent x"""
        #horse[9] is the date
        horses=inputHorses
        if len(horses) == 1:
            return horses
        date=datetime.datetime.strptime(str(datestr), "%Y-%m-%d")
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
        return sortDistance[0:min(x,len(sortDistance))]
        horses=sortDistance
        sortHorse=[]
        sortHorse.append(horses[0])
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

            if abs(self.meanFinishes[idx]-self.jockeyMean) > (2*self.jockeyStd):
                indexToRemove.append(idx)
                if verbose != 0:
                    print "2*std is " + str(2*self.jockeyStd)
                    print "input is " + str(self.meanFinishes[idx])
                    print "jockey name is " + str(horse[7])
                    print "mean is " + str(self.jockeyMean)
                    print "removing abnormal jockey from dataset"
                continue

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


        for idx in reversed(indexToRemove):
            allInputsReturn.pop(idx)
            horsesReturn.pop(idx)

        return allInputsReturn, horsesReturn

 
    def subNormaliseInputs(self, horses):
        """normalise the inputs.  horses is a list of all of the races that the
        horse under analysis has been in.  The function called for normalising
        take all of these races into consideration in comparison to a particular
        race idx.  This way each race gets normalised in turn"""        
        horsesn=[[0 for x in xrange(5)] for x in xrange(len(horses))]
        self.meanStdRaceLength(horses)
        self.meanStdJockey(horses)
        self.meanStdNumberOfHorses(horses)
        self.meanStdWeight(horses)
       # self.meanStdTrainer(horses)
       # jockeyWins=self.jockeyPercentWins(horses)
        self.meanStdGoing(horses)
        for idx in range(0, len(horses)):
            horsesn[idx][0]=self.normaliseRaceLength(idx)
            #print "done"
            horsesn[idx][1]=self.normaliseNumberOfHorses(idx)
            #print "done"
            #horsesn[idx][2]=self.normalisePastPosition(horses, idx)
            #print "done"
            horsesn[idx][2]=self.normaliseJockey(idx)
            #print "done" + str(horsesn[idx][3])
            horsesn[idx][3]=self.normaliseWeight(idx)
#            horsesn[idx][4]=jockeyWins[idx]
 #           horsesn[idx][5]=self.normaliseTrainer(idx)
            #print "done"
            horsesn[idx][4]=self.normaliseGoing(horses, idx)
            #print "done"
            #horsesn[idx][5]=1.0
           # age                      
       
        return horsesn
        

    def testFunction(self, jockeyName, numberHorses, raceLength, weight, going, draw, verbose=0):#, trainerName):
        """blah"""
        jockeyNames=[]
        jockeyNames.append(jockeyName)
        testn=[None]*5
        testn[0]=self.normaliseTestRaceLength(raceLength)
        testn[1]=self.normaliseTestNumberOfHorses(numberHorses)
        #testn[2]=self.normaliseTestPastPosition(horses[len(horses)-1][4])
        testn[2]=self.normaliseTestJockey(jockeyName)
        testn[3]=self.normaliseTestWeight(weight)
#        testn[4]=self.NeuralNetworkStuffInst.subJockeyPercentWins(jockeyNames)[0]
 #       testn[5]=self.NeuralNetworkStuffInst.normaliseTestTrainer(trainerName)
        testn[4]=self.normaliseTestGoing(going)
        #testn[4]=self.NeuralNetworkStuffInst.normaliseTestDraw(draw, numberHorses)
        #testn[5]=1.0
        return testn

