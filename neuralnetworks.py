from neuralnetworkstuff import NeuralNetworkStuff
from sqlstuff import SqlStuff
import random
from math import exp

class NeuralNetwork:

    def __init__(self, numInput=5, numHidden=6, numOutput=1):
        """initialise some variables and arrays"""
        
        self.numInput=numInput
        self.numHidden=numHidden
        self.numOutput=numOutput
        self.allInputs=[]
        #input to hidden layer and input to output layer arrays
        self.inputs=[None]*numInput
        self.ihWeights=[[0 for x in xrange(numInput)] for x in xrange(numHidden)]
        self.cummulativeDeltaihWeights=[[0 for x in xrange(numInput)] for x in xrange(numHidden)]
        self.ihSums=[None]*numHidden
        self.ihBiases=[None]*numHidden
        self.cummulativeDeltaihBiases=[0.0]*numHidden
        self.ihOutputs=[None]*numHidden
        #hidden layer to output layer
        self.hoWeights=[[0 for x in xrange(numHidden)] for x in xrange(numOutput)]
        self.cummulativeDeltahoWeights=[[0 for x in xrange(numHidden)] for x in xrange(numOutput)]
        self.hoSums=[None]*numOutput
        self.hoBiases=[None]*numOutput
        self.cummulativeDeltahoBiases=[0.0]*numOutput
        self.outputs=[None]*numOutput
        #back propogation
        self.oGrads=[None]*numOutput
        self.hGrads=[None]*numHidden
        self.ihPrevWeightsDelta=[[0 for x in xrange(numInput)] for x in xrange(numHidden)]
        self.ihPrevBiasesDelta=[0.0]*numHidden
        self.hoPrevWeightsDelta=[[0 for x in xrange(numHidden)] for x in xrange(numOutput)]
        self.hoPrevBiasesDelta=[0.0]*numOutput

        self.NeuralNetworkStuffInst=NeuralNetworkStuff()

    def NeuralNetwork(self, horseName, horseLimit):
        """blah"""
        SqlStuffInst=SqlStuff()
        
        # get all the results for this horseName
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
        
        # test reducing and sorting the horses by date here before the normalising
        # and try also doing the sort and reduction after the noralise
        sortedHorses=self.NeuralNetworkStuffInst.subSortReduce(horses, horseLimit)
        del(horses)
        horses=sortedHorses

        eta = 0.5
        alpha=0.04
        ctr=0
        Error=0.5
        self.allInputs=self.NeuralNetworkStuffInst.subNormaliseInputs(horses)
        while (ctr<10000 and Error > 0.001):
            #print "iteration = " + str(ctr)

            #loop through all the results for this horse
            for resultNo, horse in enumerate(horses):
                # get the normalised inputs for all of this horses results
                self.inputs=self.allInputs[resultNo]
                tValue=float(horses[resultNo][4])/float(horses[resultNo][6])
                #print "Before weight update"
                #print "desired outputs = " + str(tValue)
                yValues=self.ComputeOutputs(self.inputs)
                Error=self.Error(tValue,yValues[0])
                self.AccumulateDeltas(tValue, eta)

            self.UpdateWeights(alpha,len(horses))
            #print "After weight update"
            for resultNo, horse in enumerate(horses):
                self.inputs=self.allInputs[resultNo]
                tValue=float(horses[resultNo][4])/float(horses[resultNo][6])
                yValues=self.ComputeOutputs(self.inputs)
                Error=max(Error,self.Error(tValue,yValues[0]))
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
        for ii in range(0, len(self.hGrads)):
            derivative=(1-self.ihOutputs[ii])*self.ihOutputs[ii]
            summ=0.0
            for oo in range(0, len(self.oGrads)):
                summ+=self.oGrads[oo]*self.hoWeights[oo][ii]
            self.hGrads[ii]=derivative*summ
        for ii in range(0, len(self.ihWeights[0])):
            for jj in range(0, len(self.ihWeights)):                
                self.cummulativeDeltaihWeights[jj][ii]+=eta*self.hGrads[jj]*self.inputs[ii]
                
        for ii in range(0, len(self.ihBiases)):
            self.cummulativeDeltaihBiases[ii]+=eta*self.hGrads[ii]*1.0
         

        for ii in range(0, len(self.hoWeights[0])):
            for jj in range(0, len(self.hoWeights)):
                self.cummulativeDeltahoWeights[jj][ii]+=eta*self.oGrads[jj]*self.ihOutputs[ii]
    
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
            for ii in range(0, len(self.inputs)-1):               
                self.ihWeights[hh][ii]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0
                
            for oo in range(0, len(self.outputs)):
                self.hoWeights[oo][hh]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

    def SetBiases(self):
        """Blah"""
        for hh in range(0, len(self.ihBiases)):
            self.ihBiases[hh]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

        for oo in range(0, len(self.hoBiases)):
            self.hoBiases[oo]=(float(random.randrange(0, 1000, 3))-500.0)/1000.0

    def GetWeights(self):
        """blah"""

    def ComputeOutputs(self, xValues):
        """blah"""
        for ii in range(0,len(self.ihSums)):
            self.ihSums[ii]=0.0
        for ii in range(0, len(self.hoSums)):
            self.hoSums[ii]=0.0
        for jj in range(0,len(self.ihSums)):
            for ii in range(0, len(xValues)-1):
                self.ihSums[jj]+=xValues[ii]*self.ihWeights[jj][ii]
            self.ihSums[jj]+=self.ihBiases[jj]
            self.ihOutputs[jj]=self.SigmoidFunction(self.ihSums[jj])
        for oo in range(0, len(self.hoSums)):
            for hh in range(0, len(self.ihSums)):
                self.hoSums[oo]+=self.ihOutputs[hh]*self.hoWeights[oo][hh]
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

    def testFunction(self, jockeyName, numberHorses, raceLength, weight):
        """blah"""
        testn=[None]*5
        testn[0]=self.NeuralNetworkStuffInst.normaliseTestRaceLength(raceLength)
        testn[1]=self.NeuralNetworkStuffInst.normaliseTestNumberOfHorses(numberHorses)
        #testn[2]=self.normaliseTestPastPosition(horses[len(horses)-1][4])
        testn[2]=self.NeuralNetworkStuffInst.normaliseTestJockey(jockeyName)
        testn[3]=self.NeuralNetworkStuffInst.normaliseTestWeight(weight)
        #testn[5]=self.normaliseTestGoing(test[8])
        testn[4]=1.0
        yValues=self.ComputeOutputs(testn)
        #print "yValue = " + str(yValues)
        #print "predicted finish = " + str(yValues[0]*float(numberHorses))
        return yValues[0]*float(numberHorses)
