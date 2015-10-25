from sqlstuff2 import SqlStuff2


def pastComp(horseA, horseB):
    """ check to see if horseA has ever raced against horseB before.  Find which horse has
    won the most times.  Do this for all combinations of horses to create a results table.
    This can then be used in combination with the neural network to find a final result"""
    SqlStuffInst=SqlStuff2()
    horseAInfos=SqlStuffInst.getHorse(horseA)
    horseBInfos=SqlStuffInst.getHorse(horseB)
    horseAWins=0
    horseBWins=0
    for horseAInfo in horseAInfos:
#        print "doing something for horseA"
        for horseBInfo in horseBInfos:
#            print "doing something for horseB"
            if horseAInfo[10:12] == horseBInfo[10:12]:
                if horseAInfo[4] < horseBInfo[4]:
                    print "horse A won"
                    horseAWins+=1
                else:
                    horseBWins+=1
                    print "horse B won"

 #   if horseAWins == 0 and horseBWins == 0:
 #       print "these horses have not raced previously"
    
    return horseAWins, horseBWins

def pastPerf(horses):
    """ loop through the horses until no more position changes occur"""
    localPos=horses
    while True:
        currentPos=localPos
        for idx, horse in enumerate(localPos[1:len(localPos)]):
            """compare horse to the previous horse"""
            horseAWins, horseBWins = pastComp(localPos[idx], horse)
            if horseBWins > horseAWins:
                localPos[idx+1]=localPos[idx]
                localPos[idx]=horse

        if localPos==currentPos:
            break;
    return currentPos
