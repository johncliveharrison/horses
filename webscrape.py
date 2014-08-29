import urllib2,  time, re
#from bs4 import BeautifulSoup
from BeautifulSoup import BeautifulSoup
import datetime
from string import whitespace
import sys
from sqlstuff import SqlStuff
from neuralnetworks import NeuralNetwork
    
            
class HrefStuff:
    def __init__(self):
        self.fullResultHrefs=[]
        self.raceHrefs=[]
        self.raceTime=[]
        self.raceVenue=[]
       # self.horseName=[]
       # self.jockey=[]
    
    def getTestCardHref(self, date):
        """ get todays test card link"""
        self.date=date #time.strftime("%Y-%m-%d")
#        self.date="2014-08-03"
        print self.date
        self.url="http://www.racingpost.com/horses2/cards/home.sd?r_date=" + self.date
        return self.url

    def getTodaysRaces(self, href):
        """ get the hrefs for the races, exclude the terrestrial tv and worldwide stakes"""
        self.webpage=urllib2.urlopen(href)
        self.soup=BeautifulSoup(self.webpage)
        self.divBody=self.soup.body
        self.racesList=self.divBody.find("div", {"class":"tabContent tabNoTB tabSelected"})
        """ here can find the race names"""
        self.h3=self.racesList.findAll("h3")
        noneRaceHeaders=0
        for idx, h3 in enumerate(self.h3):
            try:
                self.a=h3.find("a")
                self.raceVenue.append(self.a.find(text=True))
            except AttributeError:
                """ this covers the case for RACES SHOWN ON TERRESTRIAL TV"""
                noneRaceHeaders+=1
        self.tables=self.racesList.findAll("table", {"class":"cardsGrid"})
        self.raceTimes=[[] for _ in range(len(self.tables[noneRaceHeaders:]))]
        for idx, table in enumerate(self.tables[noneRaceHeaders:]):
            #for every cardGrid table we need to find all the rows
            self.tr=table.findAll("tr")
            # Now for all the rows we need to find the first td that contains the <a href 
            for tr in self.tr:
                self.td=tr.find("td")
                self.th=tr.find("th")
                self.a=self.td.find("a")
                try:
                    self.raceHrefs.append(self.a.get("href"))
                    """ here get the text as the racetime"""
                    self.a=self.th.find("a")
                    self.raceTimes[idx].append(self.a.find(text=True))
#                    print str(self.raceTime)
                except AttributeError:
                    """ doesn't matter if there was no link"""
#            self.raceTimes[idx]=self.raceTime
        return self.raceHrefs, self.raceTimes, self.raceVenue

    def getCardContents(self, href):
        """ get the horse, jockey, number of horses and distance"""
        horseName=[]
        jockey=[]
        weight=[]
        self.url="http://www.racingpost.com" + href + "&raceTabs=lc_"
#        print self.url
        self.webpage=urllib2.urlopen(self.url)
        self.soup=BeautifulSoup(self.webpage)
        self.divBody=self.soup.body
        self.cardGridWrapper=self.divBody.find("div", {"class":"cardGridWrapper"})
        self.tr=self.cardGridWrapper.findAll("tr", {"class":"cr"})
        for row in self.tr:
            self.horseNameRow=row.find("a")
            horseName.append(self.horseNameRow.find("b").find(text=True).replace('&acute;',"'"))            
            self.tdJockey=row.findAll("td")[6]
            try:
                jockey.append(self.tdJockey.find("a").find(text=True))
            except AttributeError:
                jockey.append("unknown")
            self.tdWeight=row.findAll("td")[4]
            try:
                weight.append(self.tdWeight.find(text=True))
            except AttributeError:
                weight.append("9-0")
                print "failed to find weight"
        self.ul=self.divBody.find("ul", {"class":"results clearfix"})
        self.li=self.ul.findAll("li")[2]
        self.length=self.li.find("strong").find(text=True)
        """get rid of the strange unicode half symbols"""
        s=self.length.split()[0].encode('unicode_escape')
        self.raceLength = s.replace('\\xbd', '.5')

        return (horseName, jockey, self.raceLength, weight)

    def getFullResultHrefs(self, date):
        """function to get the hrefs for the specified date"""
        self.date=date
        """add the date to the base url"""
        self.url="http://www.racingpost.com/horses2/results/home.sd?r_date=" + self.date
        self.webpage=urllib2.urlopen(self.url)
        self.soup=BeautifulSoup(self.webpage)
        self.divBody=self.soup.body
        self.divTabBlock=self.divBody.find("div", {"class":"tabBlock"})        
        self.tableResultGrids=self.divTabBlock.findAll("table", {"class":"resultGrid"})
        for self.tableResultGrid in self.tableResultGrids:
            self.ulBullActiveLinks=self.tableResultGrid.findAll("ul", {"class":"bull activeLink"})
            for self.ulBullActiveLink in self.ulBullActiveLinks:
                self.fullResultHref=self.ulBullActiveLink.find("a")
                self.fullResultHrefs.append(self.fullResultHref.get("href"))        
        return self.fullResultHrefs
    
    def getFullResults(self, href):
        """function to get the full results from the specified href"""
        self.href="http://www.racingpost.com/" + href
        self.webpage=urllib2.urlopen(self.href)
        self.soup=BeautifulSoup(self.webpage)
        self.divBody=self.soup.body
        self.mainWrapper=self.divBody.find("div", {"id":"mainwrapper"})
        self.popUpCenter=self.mainWrapper.find("div", {"class":"popUpCenter"})
        self.popUp=self.popUpCenter.find("div", {"class":"popUp"})        

    def getFullResultsHeader(self):
        """returns the header containing race and date etc"""        
        self.header=self.popUp.find("div", {"class":"leftColBig"})
        return self.header        

    def getFullResultsGrid(self):
        """returns the grid will the placings etc"""
        self.grid=self.popUp.find("table", {"class":"grid resultRaceGrid"})        
        return self.grid


class ResultStuff:
    def __init__(self, fullResult, fullHeader, raceDate):
        self.fullResult=fullResult
        self.fullHeader=fullHeader
        self.raceDate= raceDate
        self.horseNames=[]
        self.horseAges=[]
        self.horseWeights=[]
        self.lengthGoingTypeTemp=[]
        self.jockeys=[]
        
    def getRaceName(self):
        """ get the name of the race"""
        """ if there is no race info available then do nothing"""
        try:
            self.h1=self.fullHeader.find("h1").find(text=True)
            self.raceNameDate=self.h1.split('Result')
            self.raceName=self.raceNameDate[0]
        except AttributeError:
            print "no RaceName found"

    def getRaceDate(self):
        """get the date of the race"""
        """if the is no race info then do nothing"""
        try:
            self.h1=self.fullHeader.find("h1").find(text=True)
            self.raceNameDate=self.h1.split('Result')
            self.raceDate=self.raceNameDate[1]           
        except AttributeError:
            print "no RaceDate found"

    def getNumberOfHorses(self):
        """get the number of horses that ran in the race"""
        try:
            self.numberOfHorses=len(self.horseNames)
        except AttributeError:
            print "no horseNames found cannot get numberOfHorses"

    def getRaceLength(self):
        """get the length of the race and convert to metres"""
        try:
            self.ul=self.fullHeader.find("ul")
            self.li=self.ul.find("li")
            self.lengthGoingType=self.li.find(text=True)
            self.lengthGoingTypeArray=self.lengthGoingType.strip().splitlines()                 
            for s in self.lengthGoingTypeArray:                                 
                if not re.match(r'^\s*$', s):
                    if '(' not in s:                      
                        self.lengthGoingTypeTemp.append(s)
            """get rid of the strange unicode half symbols"""
            s=self.lengthGoingTypeTemp[0].split()[0].encode('unicode_escape')
            self.raceLength = s.replace('\\xbd', '.5')
            #print self.raceLength
        except AttributeError:
            print "cound not find the raceLength"

    def getGoing(self):
        """function to find the going conditions for the race"""
        try:
            self.ul=self.fullHeader.find("ul")
            self.li=self.ul.find("li")
            self.lengthGoingType=self.li.find(text=True)
            self.lengthGoingTypeArray=self.lengthGoingType.strip().splitlines()          
            for s in self.lengthGoingTypeArray:               
                if not re.match(r'^\s*$', s):
                    if '(' not in s:               
                        self.lengthGoingTypeTemp.append(s)
            try:
                self.going=self.lengthGoingTypeTemp[0].split()[1]
            except IndexError:
                self.going="?unknown?"               
            #print self.lengthGoingTypeTemp[0]
            #print self.going
        except AttributeError:
            print "cound not find the going"

    def getRaceLengthGoing(self):
        """function to find the race length and the going"""
        try:
            self.ul=self.fullHeader.find("ul")
            self.li=self.ul.find("li")
            self.lengthGoingType=self.li.find(text=True)
            self.lengthGoingTypeArray=self.lengthGoingType.strip().splitlines()          
            for s in self.lengthGoingTypeArray:               
                if not re.match(r'^\s*$', s):
                    if '(' not in s:               
                        self.lengthGoingTypeTemp.append(s)
            """get rid of the strange unicode half symbols"""
            s=self.lengthGoingTypeTemp[0].split()[0]#.encode('unicode_escape')
            self.raceLength = s.replace('\\xbd', '.5')
            self.raceLength = self.raceLength.replace('&frac12;', '.5')
            try:
                self.going=self.lengthGoingTypeTemp[0].split()[1]
            except IndexError:
                self.going="?unknown?"
        except:
            print "couldn't get raceLength or going"

    def getHorseNames(self):
        """function to find all of the horse names in the full result popup"""
        """if there are no horsenames available then do nothing"""
        try:
            self.gridInfo=self.fullResult.findAll("b")
            for self.info in self.gridInfo:
                """use this if to get rid of the b instances that didn't have an a"""
                if self.info.find("a"):
                    self.horseInfo=self.info.find("a")
                    self.horseNames.append(self.horseInfo.find(text=True))
            #print self.horseNames
        except AttributeError:
            print "no HorseNames found"

    def getHorseAge(self):
        """function to find all of the horse ages in the full result popup"""
        """if there are no horse ages available then do nothing"""
        try:
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               for self.tr in self.trs:
                   """use this if to get rid of the None results when class=black is not found"""
                   if self.tr.find("td", {"class":"black"}):
                       self.horseAges.append(self.tr.find("td", {"class":"black"}).find(text=True))
            #print self.horseAges
        except AttributeError:
            print "no HorseAges found"

    def getHorseWeight(self):
        """functio to find all of the extra weights in the full result popup"""
        """if there are no horse weights available then do nothing"""
        try:
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               for self.tr in self.trs:
                   if self.tr.find("td", {"class":"nowrap black"}):                   
                       self.horseWeights.append(self.tr.find("td", {"class":"nowrap black"}).find(text=True).replace(u'\xa0', u' '))                                                                                                                    
            #print self.horseWeights
        except AttributeError:
            print "no HorseWeights found"

    def getJockeyName(self):
        """function to find all of the jockeys in the full result popup"""
        """if there are no jockeys available then do nothing"""
        try:
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               for self.tr in self.trs:
                   if self.tr.find("td", {"class":"lightGray"}):
                       clg=self.tr.find("td", {"class":"lightGray"})
                       if clg.find("a"):
                           self.jockeys.append(clg.find("a").find(text=True))                                                                                                                    
            #print self.jockeys
        except AttributeError:
            print "no jockeys found"

    def getHorseWeightJockeyNameAge(self):
        """function to get the weight jockey and going"""
        try:
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               numberOfWeights=len(self.horseWeights)
               numberOfAges=len(self.horseAges)
               numberOfJockeys=len(self.jockeys)
               if numberOfWeights==self.numberOfHorses:
                   break
               for self.tr in self.trs:                   
                   try:
                       #if self.tr.find("td", {"class":"nowrap black"}):                   
                       self.horseWeights.append(self.tr.find("td", {"class":"nowrap black"}).find(text=True).replace(u'\xa0', u' ').replace('&nbsp;',''))
                   except:
                       """do nothing"""    
                   try:
                       #if self.tr.find("td", {"class":"black"}): 
                       self.horseAges.append(self.tr.find("td", {"class":"black"}).find(text=True))
                   except:
                       """do nothing"""                         
                   try:
                       #if self.tr.find("td", {"class":"lightGray"}):
                       clg=self.tr.find("td", {"class":"lightGray"})
                       try:
                           #if clg.find("a"):
                           self.jockeys.append(clg.find("a").find(text=True))
                       except:
                           """do nothing""" 
                   except:
                       """do nothing"""
               if numberOfWeights==len(self.horseWeights):
                   self.horseWeights.append("unknown")
               if numberOfAges==len(self.horseAges):
                   self.horseAges.append("unknown")
               if numberOfJockeys==len(self.jockeys):
                   self.jockeys.append("unknown")                
                   
        except AttributeError:
            print "no tbody found in the full result"

    def getAllResultInfo(self):
        """ function to get all of the sql info"""
        self.getRaceName()
        self.getHorseNames()
        self.getNumberOfHorses()
        self.getHorseWeightJockeyNameAge()        
        self.getRaceLengthGoing()        
        if self.numberOfHorses != len(self.jockeys):
            print self.numberOfHorses
            print self.jockeys
            print self.horseNames
            print self.raceName
            

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)
               
def makeATestcard(date):
    """ extract the information from the days cards"""
    HrefStuffInst=HrefStuff()
    horseName=[]
    jockeyName=[]
    raceLength=[]
    weights=[]
    """ get the href for the days test card"""
    todaysTestCardHref=HrefStuffInst.getTestCardHref(date)
    """ extract all of the links for the races from the days card"""
    todaysRaces, todaysRaceTimes, todaysRaceVenues=HrefStuffInst.getTodaysRaces(todaysTestCardHref)
    for todaysRace in todaysRaces:
        horse, jockey, length, weight=HrefStuffInst.getCardContents(todaysRace)
        horseName.append(horse)
        jockeyName.append(jockey)
        raceLength.append(length)
        weights.append(weight)
    return (horseName, jockeyName, raceLength, weights, todaysRaceTimes, todaysRaceVenues)    

def makeADatabase(dateStart, dateEnd, test = "false"):
    dateStartSplit=dateStart.split('-')
    dateEndSplit=dateEnd.split('-')
    SqlStuffInst=SqlStuff()        
    SqlStuffInst.createResultTable()
    """ user enters the date """
    #date=raw_input("enter the required date yyyy-mm-dd")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))):
        date=time.strftime("%Y-%m-%d", single_date.timetuple())       
        #date="2014-07-{}".format(day)
        print date
        time.sleep(1)
        ResultStuffInsts=[]       
        """
        for fullResultHref in fullResultHrefs:
            webpage=urllib2.urlopen(fullResultHref.get("href"))"""

        HrefStuffInst=HrefStuff()
        """ get the hrefs that must be appended to http://www.racingpost.com/"""
        fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)

        """loop through the number of races and make a ResultStuff object for each"""
        for fullResultHref in fullResultHrefs:
            HrefStuffInst.getFullResults(fullResultHref)
            #print "got full results webpage for..."
            fullResult=HrefStuffInst.getFullResultsGrid()
            fullHeader=HrefStuffInst.getFullResultsHeader()
            ResultStuffInst=ResultStuff(fullResult, fullHeader, date)
            ResultStuffInst.getAllResultInfo()            
            """ResultStuffInst.getRaceDate()
            ResultStuffInst.getHorseNames()
            ResultStuffInst.getNumberOfHorses()
            ResultStuffInst.getRaceLength()
            ResultStuffInst.getHorseAge()
            ResultStuffInst.getHorseWeight()
            ResultStuffInst.getJockeyName()
            ResultStuffInst.getGoing()"""
            ResultStuffInsts.append(ResultStuffInst)
        """loop through the ResultStuff class objects and add them to the database"""        
        for ResultStuffInst in ResultStuffInsts:
            if test == "false":
                SqlStuffInst.addResultStuffToTable(ResultStuffInst)
            else:
                for idx, horseName in enumerate(ResultStuffInst.horseNames):
                    """create a string with this horses values"""
                    val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'".format(\
                    ResultStuffInst.horseNames[idx].replace("'", "''"),\
                    ResultStuffInst.horseAges[idx], ResultStuffInst.horseWeights[idx], idx+1, \
                    ResultStuffInst.raceLength, ResultStuffInst.numberOfHorses, ResultStuffInst.jockeys[idx].replace("'", "''"), \
                    ResultStuffInst.going, ResultStuffInst.raceDate) 
                    print val_str
        
def makeAResult(date):
    """ make an array of all the result infos for the day"""
    #date=time.strftime("%Y-%m-%d")
    #date="2014-07-{}".format(day)
    print date
    time.sleep(1)
    ResultStuffInsts=[]       
    """
    for fullResultHref in fullResultHrefs:
    webpage=urllib2.urlopen(fullResultHref.get("href"))"""

    HrefStuffInst=HrefStuff()
    """ get the hrefs that must be appended to http://www.racingpost.com/"""
    fullResultHrefs=HrefStuffInst.getFullResultHrefs(date)

    """loop through the number of races and make a ResultStuff object for each"""
    for fullResultHref in fullResultHrefs:
        HrefStuffInst.getFullResults(fullResultHref)
        #print "got full results webpage for..."
        fullResult=HrefStuffInst.getFullResultsGrid()
        fullHeader=HrefStuffInst.getFullResultsHeader()
        ResultStuffInst=ResultStuff(fullResult, fullHeader, date)
        ResultStuffInst.getAllResultInfo()            
        """ResultStuffInst.getRaceDate()
        ResultStuffInst.getHorseNames()
        ResultStuffInst.getNumberOfHorses()
        ResultStuffInst.getRaceLength()
        ResultStuffInst.getHorseAge()
        ResultStuffInst.getHorseWeight()
        ResultStuffInst.getJockeyName()
        ResultStuffInst.getGoing()"""
        ResultStuffInsts.append(ResultStuffInst)
    return ResultStuffInsts

def writeAResult(date, filenameAppend):
    """write the dates result to a file"""
    todaysResults=makeAResult(date)
    f = open(str(date)+str(filenameAppend),'a')
    original = sys.stdout
    sys.stdout = Tee(sys.stdout, f)
    for idx, ii in enumerate(todaysResults):
        print "race number " + str(idx) 
        for jdx, jj in enumerate(todaysResults[idx].horseNames):
            print str(jj)
    sys.stdout = original

def viewADatabase():
    SqlStuffInst=SqlStuff()
    SqlStuffInst.viewAllTable()

def viewHorse(horseName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE"
    SqlStuffInst=SqlStuff()
    SqlStuffInst.viewHorse(horseName)

def viewJockey(jockeyName):
    print "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE"
    SqlStuffInst=SqlStuff()
    SqlStuffInst.viewJockey(jockeyName)

def delDate(date):
    SqlStuffInst=SqlStuff()
    SqlStuffInst.delDate(date)

def delDateRange(dateStart, dateStop):
    dateStartSplit=dateStart.split("-")
    dateStopSplit=dateStop.split("-")
    for single_date in daterange(datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2])), datetime.date(int(dateStopSplit[0]),int(dateStopSplit[1]),int(dateStopSplit[2]))):
        print single_date
        delDate(single_date)

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)

def sortResult(decimalResult, horse, basedOn, error, sortList, sortDecimal):
    """ sort the results by date and return the most recent x"""
    if len(sortList)==0:
        sortList.append(str(horse) + '('+str(decimalResult)+')('+str(basedOn)+')('+str(error)+')')  # appemd the first horse
        sortDecimal.append(decimalResult)
        return sortDecimal, sortList
    
    iterations = len(sortList)
    decimal1=decimalResult
    for idx in range(0, iterations):

        decimal0=sortDecimal[idx]

        if decimal1==0.0:
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.append(decimal1)
            break
        elif decimal0==0.0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.insert(idx,decimal1)
            break
        elif decimal1 < decimal0:
            sortList.insert(idx, str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.insert(idx,decimal1)
            break
        elif idx == (iterations-1):
            sortList.append(str(horse) + '('+str(decimal1)+')('+str(basedOn)+')('+str(error)+')')
            sortDecimal.append(decimal1)

    return sortDecimal, sortList



def neuralNet(horseLimit, filenameAppend, afterResult = "noResult", date=time.strftime("%Y-%m-%d")):
    horseName=[]
    jockeyName=[]
    lengths=[]
    
    in_loop = True
    #while in_loop == True:
    #    horseName.append(raw_input("Horse name?"))
    #    jockeyName.append(raw_input("Jockey name?"))
    #    again = raw_input("exit loop y/n?")
    #    if again == 'y':
    #        in_loop=False
    horses, jockeys, lengths, weights, todaysRaceTimes, todaysRaceVenues=makeATestcard(date)
    if afterResult != "noResult":
        todaysResults=makeAResult(date)
    print todaysRaceVenues
    #numberHorses=raw_input("Number of Horses?")
    #raceLength=raw_input("race length?")
    #for ii in range(0,startRace):
    #    horses.pop(ii)
    #    jockeys.pop(ii)
    #    lengths.pop(ii)
    #    print "remove race" + str(ii) + "from list"
  
    venuesRaceNo=0
    venueNumber=0
    for raceNo, race in enumerate(horses):
        
        numberHorses=len(horses[raceNo])
        position=[0.0]*numberHorses
        basedOn=[]
        sortList=[]
        sortDecimal=[]

        for idx, horse in enumerate(race):
            NeuralNetworkInst=NeuralNetwork()
            bO, error = NeuralNetworkInst.NeuralNetwork(horse, int(horseLimit))
            basedOn.append(bO)
            if basedOn[idx] != 0:
                sortDecimal, sortList=sortResult(float(NeuralNetworkInst.testFunction(jockeys[raceNo][idx], numberHorses, lengths[raceNo], weights[raceNo][idx])), str(horse), str(basedOn[idx]), str(error), sortList, sortDecimal)
            else:
                sortDecimal, sortList=sortResult(float(0.0), str(horse), str(basedOn[idx]), str(error), sortList, sortDecimal);
           # print sortList
        #position.sort()
        f = open(str(date)+str(filenameAppend),'a')
        original = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        
        print str(raceNo) + ' ' + str(todaysRaceVenues[venueNumber]) + ' ' + str(todaysRaceTimes[venueNumber][venuesRaceNo]) 
        for ii, pos in enumerate(sortList):
            #splitpos=re.split(r'(\d+)', pos)
            try:
                if afterResult == "noResult":
                    print str(ii+1) + pos
                else:
                    print str(ii+1) + pos + '                  ' + str(todaysResults[raceNo].horseNames[ii])
            except IndexError:
                """if there are none finishers this will be the exception"""
        venuesRaceNo+=1
        if venuesRaceNo==len(todaysRaceTimes[venueNumber]):
            venuesRaceNo=0
            venueNumber+=1
            #todaysRaceVenues.pop(0)
#' ' + str(splitpos[4]) + ' (' + str(splitpos[1]) + str(splitpos[2]) + str(splitpos[3]) + ')('+str(splitpos[5])+')('+str(splitpos[6])+str(splitpos[7])+')'

        
        #use the original
        sys.stdout = original
        print "This won't appear on file"  # Only on stdout
        f.close()






#makeADatabase()
#SqlStuffInst=SqlStuff()
#SqlStuffInst.viewAllTable()
#SqlStuffInst.viewHorse("Parlour Games")
#rows=cursor.fetchall()
#print rows

#    fullResults.append(HrefStuffInst.getFullResults(fullResultHref))  
#print fullResultHrefs


#divBlock=divContainer.findAll("div", {"class":"block"})
#divSep=divBlock[3].findAll("div", {"class":"separator"})
#members=divSep[3].findAll("a")

#for member in members:
#    print member.find(text=True)
#    print member.get("title")
#    print member.get("href")
   
