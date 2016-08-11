from neuralnetworkstuff import NeuralNetworkStuff
from sqlstuff2 import SqlStuff2
import random
from math import exp
import sys

class NeuralNetwork:

    def __init__(self, numInput=6, numHidden=[5,6], numOutput=1, numHiddenLayers=1):
        """initialise some variables and arrays"""

        self.numberHiddenLayers=numHiddenLayers
        
        self.numInput=numInput
        self.numHidden=numHidden
        self.numOutput=numOutput
        self.allInputs=[]
        #input to hidden layer arrays and weights and biases
        self.inputs=[None]*numInput
        self.ihWeights=[[0 for x in xrange(numInput)] for x in xrange(numHidden[0])]
        self.cummulativeDeltaihWeights=[[0 for x in xrange(numInput)] for x in xrange(numHidden[0])]
        self.ihSums=[None]*numHidden[0]
        self.ihBiases=[None]*numHidden[0]
        self.cummulativeDeltaihBiases=[0.0]*numHidden[0]
        self.ihOutputs=[None]*numHidden[0]
        #hidden layer to hidden layer
        self.hiddenInputs=[None]*(numHidden[0]+1)
        self.hhWeights=[[0 for x in xrange(numHidden[0]+1)] for x in xrange(numHidden[1])]
        self.cummulativeDeltahhWeights=[[0 for x in xrange(numHidden[0]+1)] for x in xrange(numHidden[1])]
        self.hhSums=[None]*numHidden[1]
        self.hhBiases=[None]*numHidden[1]
        self.cummulativeDeltahhBiases=[0.0]*numHidden[1]
        self.hhOutputs=[None]*numHidden[1]
        #hidden layer to output layer
        self.hoWeights=[[0 for x in xrange(numHidden[1])] for x in xrange(numOutput)]
        self.cummulativeDeltahoWeights=[[0 for x in xrange(numHidden[1])] for x in xrange(numOutput)]
        self.hoSums=[None]*numOutput
        self.hoBiases=[None]*numOutput
        self.cummulativeDeltahoBiases=[0.0]*numOutput
        self.outputs=[None]*numOutput
        #back propogation
        self.oGrads=[None]*numOutput
        self.hoGrads=[None]*numHidden[1]
        self.hiGrads=[None]*numHidden[0]
        self.ihPrevWeightsDelta=[[0 for x in xrange(numInput)] for x in xrange(numHidden[0])]
        self.ihPrevBiasesDelta=[0.0]*numHidden[0]
        self.hhPrevWeightsDelta=[[0 for x in xrange(numHidden[0]+1)] for x in xrange(numHidden[1])]
        self.hhPrevBiasesDelta=[0.0]*numHidden[1]
        self.hoPrevWeightsDelta=[[0 for x in xrange(numHidden[1])] for x in xrange(numOutput)]
        self.hoPrevBiasesDelta=[0.0]*numOutput

        self.NeuralNetworkStuffInst=NeuralNetworkStuff()

    def NeuralNetwork(self, horseName, horseLimit, date, distance):
        """blah"""
        SqlStuffInst=SqlStuff2()
        
        """ get all the results for this horseName from the database"""
        horses=SqlStuffInst.getHorse(horseName)
        if len(horses)==0:
            print "No horse called " + str(horseName)
            return (0, 0.0)
        self.SetWeights()
        self.SetBiases()

        #print self.ihWeights
        #print self.hoWeights
        #print self.ihBiases
        #print self.hoBiases
        """test reducing and sorting the horses by date here before the normalising
        and try also doing the sort and reduction after the normalise"""
        sortedHorses=self.NeuralNetworkStuffInst.subSortReduce(horses, horseLimit, date, distance)
        del(horses)
        horses=sortedHorses
        eta = 0.5
        alpha=0.04
        ctr=0
        Error=0.5
        self.allInputs=self.NeuralNetworkStuffInst.subNormaliseInputs(horses)
        #having normalised the input values we should now remove abnormal data from the
        # training process. Abnormal data is a normalised value that lies more that 
        # 2std's away from the mean.
        usefulInputs, usefulHorses=self.NeuralNetworkStuffInst.subUsefuliseInputs(self.allInputs, horses)
        horses=usefulHorses
        self.allInputs=usefulInputs

        self.longestTime=0
        for resultNo, horse in enumerate(horses):
            if horses[resultNo][15]>self.longestTime:
                self.longestTime=horses[resultNo][15]

        while (ctr<10000 and Error > 0.02):
           # if ctr == 1000:
           #     print "Error = " + str(Error)
           #     ctr=0
            Error=0.0
            #loop through all the results for this horse
            for resultNo, horse in enumerate(horses):
                # get the normalised inputs for all of this horses results
                self.inputs=self.allInputs[resultNo]
                tValue=float(horses[resultNo][4])/float(horses[resultNo][6]) #float((horses[resultNo][15]+((horses[resultNo][4]-1)*2))/self.longestTime) #
                #print "Before weight update"
                #print "desired outputs = " + str(tValue)
                yValues=self.ComputeOutputs(self.inputs)
                #print "actual value = " + str(yValues[0])
                #Error=self.Error(tValue,yValues[0])
                Error=max(Error,self.Error(tValue,yValues[0]))
                self.AccumulateDeltas(tValue, eta)

            #print 'about to update weights'
            self.UpdateWeights(alpha,len(horses))
            #print "After weight update"
            #for resultNo, horse in enumerate(horses):
            #    self.inputs=self.allInputs[resultNo]
            #    tValue=float(horses[resultNo][4])/float(horses[resultNo][6])
            #    yValues=self.ComputeOutputs(self.inputs)
            #    Error=max(Error,self.Error(tValue,yValues[0]))
                #print "desired output = " + str(tValue)
                #print "outputs = " + str(yValues)
                #print "Error = " + str(Error)
            ctr+=1
        return (len(horses), Error)

        
    def Error(self, tValue, output):
        """blah"""
        return abs(tValue-output)


    def AccumulateDeltas(self, tValues, eta):
        """blah"""
        #compute the output gradient
        derivative=(1-self.outputs[0])*self.outputs[0]
        #print derivative
        self.oGrads[0]=derivative*(tValues-self.outputs[0])
        #print self.oGrads[0]
        for ii in range(0, len(self.hoGrads)):
            derivative=(1-self.hhOutputs[ii])*self.hhOutputs[ii]
            summ=0.0
            for oo in range(0, len(self.oGrads)):
                summ+=self.oGrads[oo]*self.hoWeights[oo][ii]
            self.hoGrads[ii]=derivative*summ

        for ii in range(0, len(self.hiGrads)):
            derivative=(1-self.ihOutputs[ii])*self.ihOutputs[ii]
            summ=0.0
            for oo in range(0, len(self.hoGrads)):
                summ+=self.hoGrads[oo]*self.hhWeights[oo][ii]
            self.hiGrads[ii]=derivative*summ


        for ii in range(0, len(self.ihWeights[0])):
            for jj in range(0, len(self.ihWeights)):                
                self.cummulativeDeltaihWeights[jj][ii]+=eta*self.hiGrads[jj]*self.inputs[ii]
                
        for ii in range(0, len(self.ihBiases)):
            self.cummulativeDeltaihBiases[ii]+=eta*self.hiGrads[ii]*1.0

        for ii in range(0, len(self.hhWeights[0])):
            for jj in range(0, len(self.hhWeights)):
                self.cummulativeDeltahhWeights[jj][ii]+=eta*self.hoGrads[jj]*self.hiddenInputs[ii]
                
        for ii in range(0, len(self.hhBiases)):
            self.cummulativeDeltahhBiases[ii]+=eta*self.hoGrads[ii]*1.0

        for ii in range(0, len(self.hoWeights[0])):
            for jj in range(0, len(self.hoWeights)):
                self.cummulativeDeltahoWeights[jj][ii]+=eta*self.oGrads[jj]*self.hhOutputs[ii]
    
        for ii in range(0, len(self.hoBiases)):
            self.cummulativeDeltahoBiases[ii]+=eta*self.oGrads[ii]*1.0
    

    def UpdateWeights(self, alpha, numRaces):
        """blah"""
               
        #update the input to the hidden weights
        for ii in range(0, len(self.ihWeights[0])):
            for jj in range(0, len(self.ihWeights)):                
                delta=self.cummulativeDeltaihWeights[jj][ii]/numRaces
                #zero this cumulatiom
                self.cummulativeDeltaihWeights[jj][ii]=0.0
                self.ihWeights[jj][ii]+=delta
                self.ihWeights[jj][ii]+=alpha*self.ihPrevWeightsDelta[jj][ii]
                self.ihPrevWeightsDelta[jj][ii]=delta

        for ii in range(0, len(self.ihBiases)):
            delta=self.cummulativeDeltaihBiases[ii]/numRaces
            self.cummulativeDeltaihBiases[ii]=0.0
            self.ihBiases[ii]+=delta
            self.ihBiases[ii]+=alpha*self.ihPrevBiasesDelta[ii]
            self.ihPrevBiasesDelta[ii]=delta


        for ii in range(0, len(self.hhWeights[0])):
            for jj in range(0, len(self.hhWeights)):                
                delta=self.cummulativeDeltahhWeights[jj][ii]/numRaces
                #zero this cumulation
                self.cummulativeDeltahhWeights[jj][ii]=0.0
                self.hhWeights[jj][ii]+=delta
                self.hhWeights[jj][ii]+=alpha*self.hhPrevWeightsDelta[jj][ii]
                self.hhPrevWeightsDelta[jj][ii]=delta

        for ii in range(0, len(self.hhBiases)):
            delta=self.cummulativeDeltahhBiases[ii]/numRaces
            self.cummulativeDeltahhBiases[ii]=0.0
            self.hhBiases[ii]+=delta
            self.hhBiases[ii]+=alpha*self.hhPrevBiasesDelta[ii]
            self.hhPrevBiasesDelta[ii]=delta
            

        for ii in range(0, len(self.hoWeights[0])):
            for jj in range(0, len(self.hoWeights)):
                delta=self.cummulativeDeltahoWeights[jj][ii]/numRaces
                self.cummulativeDeltahoWeights[jj][ii]=0.0
                self.hoWeights[jj][ii]+=delta
                self.hoWeights[jj][ii]+=alpha*self.hoPrevWeightsDelta[jj][ii]
                self.hoPrevWeightsDelta[jj][ii]=delta
                
        for ii in range(0, len(self.hoBiases)):
            delta=self.cummulativeDeltahoBiases[ii]/numRaces
            self.cummulativeDeltahoBiases[ii]=0.0
            self.hoBiases[ii]+=delta
            self.hoBiases[ii]+=alpha*self.hoPrevBiasesDelta[ii]
            self.hoPrevBiasesDelta[ii]=delta


    def SetWeights(self):
        """blah"""
        for hh in range(0, len(self.ihSums)):            
            for ii in range(0, len(self.inputs)):               
                self.ihWeights[hh][ii]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0
        for hh in range(0, len(self.ihSums)+1):
            for h2 in range(0, len(self.hhSums)):
                self.hhWeights[h2][hh]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0
    
        for h2 in range(0, len(self.hhSums)):
            for oo in range(0, len(self.outputs)):
                self.hoWeights[oo][h2]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

    def SetBiases(self):
        """Blah"""
        for hh in range(0, len(self.ihBiases)):
            self.ihBiases[hh]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

        for hh in range(0, len(self.hhBiases)):
            self.hhBiases[hh]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

        for oo in range(0, len(self.hoBiases)):
            self.hoBiases[oo]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

    def GetWeights(self):
        """blah"""

    def ComputeOutputs(self, xValues):
        """blah"""
        for ii in range(0,len(self.ihSums)):
            self.ihSums[ii]=0.0
        for ii in range(0,len(self.hhSums)):
            self.hhSums[ii]=0.0
        for ii in range(0, len(self.hoSums)):
            self.hoSums[ii]=0.0
        for jj in range(0,len(self.ihSums)):
            for ii in range(0, len(xValues)):
                #print self.ihSums
                self.ihSums[jj]+=xValues[ii]*self.ihWeights[jj][ii]
            #sys.exit(0)
            self.ihSums[jj]+=self.ihBiases[jj]
            self.ihOutputs[jj]=self.SigmoidFunction(self.ihSums[jj])
        self.hiddenInputs[0:len(self.ihOutputs)]=self.ihOutputs
        self.hiddenInputs[len(self.hiddenInputs)-1]=1.0
        for jj in range(0,len(self.hhSums)):
            for ii in range(0, len(self.hiddenInputs)):
                self.hhSums[jj]+=self.hiddenInputs[ii]*self.hhWeights[jj][ii]
            self.hhSums[jj]+=self.hhBiases[jj]
            self.hhOutputs[jj]=self.SigmoidFunction(self.hhSums[jj])
        for oo in range(0, len(self.hoSums)):
            for hh in range(0, len(self.hhSums)):
                self.hoSums[oo]+=self.hhOutputs[hh]*self.hoWeights[oo][hh]
            self.hoSums[oo]+=self.hoBiases[oo]
            #print "ihOutputs = " + str(self.ihOutputs)
            #print "hoWeights = " + str(self.hoWeights)
            #print "hoSums = " + str(self.hoSums)
            self.outputs[oo]=self.SigmoidFunction(self.hoSums[oo])
        return self.outputs
    def SigmoidFunction(self, x):
        """calculate the sigmoid activation"""
        if x < -45.0:
            return 0.0
        elif x > 45.0:
            return 1.0
        return 1.0 / (1.0 + exp(-x))

    def LinearFunction(self, x):
        """ use a linear function to calc output"""
        gradient = (600.0-20.0)/18
        return gradient*x + 20.0

    def testFunction(self, jockeyName, numberHorses, raceLength, weight, going, draw, verbose=0):#, trainerName):
        """blah"""
        jockeyNames=[]
        jockeyNames.append(jockeyName)
        testn=[None]*6
        testn[0]=self.NeuralNetworkStuffInst.normaliseTestRaceLength(raceLength)
        testn[1]=self.NeuralNetworkStuffInst.normaliseTestNumberOfHorses(numberHorses)
        #testn[2]=self.normaliseTestPastPosition(horses[len(horses)-1][4])
        testn[2]=self.NeuralNetworkStuffInst.normaliseTestJockey(jockeyName)
        testn[3]=self.NeuralNetworkStuffInst.normaliseTestWeight(weight)
#        testn[4]=self.NeuralNetworkStuffInst.subJockeyPercentWins(jockeyNames)[0]
 #       testn[5]=self.NeuralNetworkStuffInst.normaliseTestTrainer(trainerName)
        testn[4]=self.NeuralNetworkStuffInst.normaliseTestGoing(going)
        #testn[4]=self.NeuralNetworkStuffInst.normaliseTestDraw(draw, numberHorses)
        testn[5]=1.0
        yValues=self.ComputeOutputs(testn)[0]
        #print "yValue = " + str(yValues)
        #print "predicted finish = " + str(yValues[0]*float(numberHorses))

        if verbose != 0:
            print "Normalized racelength, no. horses, jockey, weight, going, 1.0"
            print testn
            for jj in range(0,len(self.ihSums)):
                for ii in range(0, len(testn)):
                    print "input " + str(ii) + "weight in h" + str(jj) + " is " + str(self.ihWeights[jj][ii])
                print "input " + str(jj) + " has bias " + str(self.ihBiases[jj])
        

        return yValues*float(numberHorses)#*self.longestTime#
