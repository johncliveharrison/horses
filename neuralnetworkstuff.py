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

    def meanStdGoing(self, horses):
        return 1.0
        self.goings=[]
        self.possibleGoings=self.gatherGoing()#["Slow", "Yielding", "Standard", "Firm", "Good"]        
        for jj, horse in enumerate(horses):
            for ii, possibleGoing in enumerate(self.possibleGoings):
                if possibleGoing==horse[8]:
                    self.goings.append(float(ii))                    
            if len(self.goings)!=jj+1:
                print "unrecognised going " + horse[8]
#        print self.goings
        self.goingMean=array(self.goings).mean()
        self.goingStd=array(self.goings).std()


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
                    if goingstr=="Very":
                        break
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
        return 1.0
#        print "mean = " + str(self.goingMean)
#        print "std = " + str(self.goingStd)
        return self.goings[idx]
        if self.goingStd < 0.001:
            return 0.0
        goingn=(self.goings[idx]-self.goingMean)/self.goingStd
        return goingn

    def normaliseTestGoing(self, testGoing):
        """normalise the testGoing using the precalculated mean and std"""
        return 1.0
        goings=[]
        for ii, possibleGoing in enumerate(self.possibleGoings):
            if possibleGoing==testGoing.split(' ')[0]:
                goings.append(float(ii))                    
        if len(goings)!=1:
            if testGoing=="Very":
                print "going was very which is due to a mistake - counts as 0"
                return 0
            print "unrecognised going " + testGoing.split(' ')[0]
        return goings[0]
        if self.goingStd < 0.001:
            return 0.0
        return (goings[0]-self.goingMean)/self.goingStd
        
    def subSortReduce(self, horses, x):
        """ sort the results by date and return the most recent x"""
        #horse[9] is the date
        if len(horses) == 1:
            return horses
        sortHorse=[]
        sortHorse.append(horses[0])
        for ii in horses[1:len(horses)]:
            #print ii
            iterations = len(sortHorse)
            date1=datetime.datetime.strptime(str(ii[9]), "%Y-%m-%d")
            for idx in range(0, iterations):
               # print sortHorse[idx]
                date0=datetime.datetime.strptime(str(sortHorse[idx][9]), "%Y-%m-%d")
               # print date0
               # print date1
               
                if date1 > date0:
                    sortHorse.insert(idx, ii)
                    break
                elif idx == (iterations-1):
                    sortHorse.append(ii)
        #print sortHorse[0:min(x,len(sortHorse))]
        return sortHorse[0:min(x,len(sortHorse))]
               
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
#        self.meanStdGoing(horses)
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
            #print "done"
#            horsesn[idx][4]=self.normaliseGoing(horses, idx)
            #print "done"
            horsesn[idx][4]=1.0
           # age                      
       
        return horsesn
        
