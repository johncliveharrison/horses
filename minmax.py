import re
from numpy import mean, std, array

""" this file contains the functions required to find the min and max
values for a field in the winners list"""
def minMaxDraw(horses, verbose=False):
    minDraw=100000
    maxDraw=0
    for ii, horse in enumerate(horses):
        try:
            tmp=horse[12]+1
        except Exception, e:
            continue
        if horse[12] > maxDraw:
            if horse[12] < 50:
                if verbose:
                    print "set the maxDraw to " + str(horse[12])
                maxDraw=horse[12]
        if horse[12] < minDraw:
            minDraw=horse[12]
    return [minDraw, maxDraw]

def normaliseDrawMinMax(draw, minMax):
    """ normalise the jockey performance based on min (worse)
    max(best) values"""
    oldValue=float(draw)
    maxDraw=float(minMax[1])
    minDraw=float(minMax[0])
    # Now normalise this draw next to the max and min
    oldRange = (maxDraw - minDraw)
    newMin=-1.0
    newMax=1.0

    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)
        newValue = (((oldValue - minDraw) * newRange) / oldRange) + newMin
    return newValue

def getGoing(goingIn):
    possibleSurfaces=["Hard", "Firm", "Good", "Soft", "Heavy", "Frozen"]
    possibleASurfaces=["Fast","filler1", "Standard", "filler2", "Slow"]
    possibleUSSurfaces=["filler1", "filler2", "Muddy", "Sloppy", "Sealed"]
    numberOfTerms=0
    going=0.0
    for ii, possibleGoing in enumerate(possibleSurfaces):
        for kk in goingIn.split():
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

    for ii, possibleGoing in enumerate(possibleASurfaces):
        for kk in goingIn.split():
            if possibleGoing==kk.strip():
                going+=2.0*ii
                numberOfTerms+=1

    for ii, possibleGoing in enumerate(possibleUSSurfaces):
        for kk in goingIn.split():
            if possibleGoing==kk.strip():
                going+=2.0*ii
                numberOfTerms+=1

    if numberOfTerms!=0:
            return (float(going/numberOfTerms))                   

def meanStdGoing(horses, verbose=0):
    goings=[]
    """ the possible goings for UK and Ireland surfaces are...
    hard, firm, good to firm, good, good to soft (aka yielding), soft, heavy
    the artificial surfaces are...        
    fast,  standard to fast, standard, standard to slow, slow
    The U.S. goings are different so avoid betting on US races!!!"""

    """ The artificial surfaces are padded so that they create a similar scale to
    the non-artificial surface (not sure that's a good idea??).  All values in the
    tables are doubles allowing 'Very' to have an effect by adding or decrememnting 1"""

    possibleSurfaces=["Hard", "Firm", "Good", "Soft", "Heavy", "Frozen"]
    possibleASurfaces=["Fast","filler1", "Standard", "filler2", "Slow"]
    possibleUSSurfaces=["filler1", "filler2", "Muddy", "Sloppy", "Sealed"]
    for jj, horse in enumerate(horses):
        numberOfTerms=0
        going=0.0
        for ii, possibleGoing in enumerate(possibleSurfaces):
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

        for ii, possibleGoing in enumerate(possibleASurfaces):
            for kk in horse[8].split():
                if possibleGoing==kk.strip():
                    going+=2.0*ii
                    numberOfTerms+=1

        for ii, possibleGoing in enumerate(possibleUSSurfaces):
            for kk in horse[8].split():
                if possibleGoing==kk.strip():
                    going+=2.0*ii
                    numberOfTerms+=1

        if numberOfTerms!=0:
            goings.append(float(going/numberOfTerms))                    
    goingMean=array(goings).mean()
    goingStd=array(goings).std()
    if verbose != 0:
        print possibleSurfaces
        print possibleASurfaces
        print goings
        print goingMean
        print goingStd
    return [goingMean, goingStd]

def normaliseGoing(going, meanStdGoing):
    """normalise going"""
    goingStd = meanStdGoing[1]
    goingMean = meanStdGoing[0]
    if goingStd < 0.001:
        return 0.0
    goingn=(going-goingMean)/goingStd
    return goingn


def convertRaceLengthMetres(distance):
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


def minMaxRaceLength(horses):
    print "minMaxRaceLength"
    minRaceLength=100000
    maxRaceLength=0
    for horse in horses:            
        lengthm=convertRaceLengthMetres(horse[5])
        if lengthm < minRaceLength:
            minRaceLength=lengthm
        if lengthm > maxRaceLength:
            maxRaceLength=lengthm

    return [minRaceLength, maxRaceLength]

def normaliseRaceLengthMinMax(raceLength, minMaxRaceLength):
    """normalise the race length by mapping input to range 0 to 1"""
    minRaceLength = minMaxRaceLength[0]
    maxRaceLength = minMaxRaceLength[1]
    oldRange = (maxRaceLength - minRaceLength)
    newMin=0.0
    newMax=1.0
    oldValue=convertRaceLengthMetres(raceLength)
    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)  
        newValue = (((float(oldValue) - float(minRaceLength)) * newRange) / float(oldRange)) + newMin
    return newValue


def minMaxSpeed(horses):
    """ find the min and max speed using the
    finish time and the distance in meters"""
    minSpeed = 10000
    maxSpeed = 0
    for horse in horses:
        lengthm=float(convertRaceLengthMetres(horse[5]))
        times = float(horse[14].strip('[]'))
        if times == 0:
            continue
        speedms = lengthm/times
        if speedms < minSpeed:
            minSpeed = speedms
        if speedms > maxSpeed:
            maxSpeed = speedms
    return [minSpeed, maxSpeed]


def normaliseSpeed(horse, minMaxSpeedList):
    """ normalise the horse speed """
    oldValue=float(horse[14].strip('[]'))
    maxSpeed=minMaxSpeedList[1]
    minSpeed=minMaxSpeedList[0]

    oldRange = (maxSpeed - minSpeed)
    newMin=0.0
    newMax=1.0

    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)
        newValue = (((oldValue - minSpeed) * newRange) / oldRange) + newMin
    return newValue

def normaliseFinish(position, numberOfHorses):
    """ normalise the horse speed """
    oldValue=float(position)
    maxFinish=float(numberOfHorses)
    minFinish=float(1)

    oldRange = (maxFinish - minFinish)
    newMin=-1.0
    newMax=1.0

    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)
        newValue = (((oldValue - minFinish) * newRange) / oldRange) + newMin
    return newValue


def convertWeightKilos(weight):
    """convert the stone, pounds weight to kilos"""
    ss=re.findall('\d+|\D+', weight)
    if len(ss) < 3:
        return 60.0
    else:
        return (float(ss[0])*6.35+float(ss[2])*0.45)

def minMaxWeight(horses, verbose=False):
    weights=[]
    minWeight=100000
    maxWeight=0
    for ii, horse in enumerate(horses):
        try:
            kg=convertWeightKilos(horse[3])
            weights.append(kg)
        except Exception,e:
            print str(e)
            print "skipping weight %s for horse %s" % (str(horse[3]), str(horse[1]))
            continue
        if kg > maxWeight:
            if verbose:
                print "set the maxWeight to " + str(kg)
                maxWeight=kg
        if kg < minWeight:
            minWeight=kg
    return [minWeight, maxWeight]

def normaliseWeightMinMax(weight, minMaxWeight):
    """ normalise the weight based on min (worse)
    max(best) values"""
    oldValue=convertWeightKilos(weight)

    # Now normalise this trainers performance next to the max and min
    minWeight=minMaxWeight[0]
    maxWeight=minMaxWeight[1]
    oldRange = (maxWeight - minWeight)
    newMin=-1.0
    newMax=1.0

    if (oldRange == 0):
        newValue = newMin
    else:
        newRange = (newMax - newMin)
        newValue = (((oldValue - minWeight) * newRange) / oldRange) + newMin
    return newValue

def minMaxJockey(horses, databaseNamesList):
    jockeys={}
    #jockeyPerf=[]
    minJockey=100000
    maxJockey=0

    if os.path.exists(minMaxJockeyListFilename):
        print "reading jockeys from file in " + minMaxJockeyListFilename
        with open (minMaxJockeyListFilename, 'rb') as fp:
            jockeyPerf = pickle.load(fp)

    if not self.jockeyPerf:

        # first create a list where each jockey in the DS appears once
        for horse in horses:
            jockeyName=horse[7]
            if not jockeyName in jockeys.keys():
                jockeys[jockeyName]= []
                #now loop through the databases and add all entries in the dict
                for databaseName in databaseNamesList:
                    #print "databaseName is " + str(databaseName)
                    SqlStuffInst.connectDatabase(databaseName)
                    jockey=jockey + SqlStuffInst.getJockey(jockeyName)
                #now loop through the jockey and find the median score
                for ride in jockey:
                    OldRange = (ride[6] - 1)
                    if (OldRange == 0):
                        NewValue = 0.0
                    else:
                        NewRange = (1.0 - 0.0)  
                        NewValue = (((float(ride[4]) - 1.0) * NewRange) / float(OldRange)) #+ 0
                        # the 1.0- here makes it so a better jockey has a bigger value
                    finish=finish+float(1.0-NewValue)            
                meanFinishes=(finish/len(rides))
                #now put this value in the dictionary
                jockeys[jockeyName]=meanFinishes
            
        print "There are " + str(len(jockeys)) + " in the minMaxJockey function"

    for jockey in jockeys:
        meanFinishes=jockey
        if meanFinishes > maxJockey:
            maxJockey=meanFinishes
        if meanFinishes < minJockey:
            minJockey=meanFinishes

    with open(self.minMaxJockeyListFilename, 'wb') as fp:
        pickle.dump(self.jockeys, fp)

    return [minJockey, maxJockey], jockeys


def normaliseJockeyMinMax(jockey, minMaxJockey):
    """ normalise the jockey performance based on min (worse)
    max(best) values"""

    # Now normalise this jockeys performance next to the max and min
    try:
        minJockey=minMaxJockey[0]
        maxJockey=minMaxJockey[1]
        oldRange = (maxJockey - minJockey)
        newMin=-1.0
        newMax=1.0
    except Exception,e:
        print "something up with the minmax jockey values passed in"
        raise Exception(str(e))
    try:
        oldValue=jockey
    except Exception, e:
        print "something up with the jockey value passed in"
        raise Exception(str(e))

    try:
        if (oldRange == 0):
            newValue = newMin
        else:
            newRange = (newMax - newMin)  
            newValue = (((oldValue - self.minJockey) * newRange) / oldRange) + newMin
    except Exception,e:
        print "something up with the normalise jockey calc"
        raise Exception(str(e))
    return newValue
