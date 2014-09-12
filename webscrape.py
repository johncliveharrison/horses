import urllib2,  time, re
#from bs4 import BeautifulSoup
from BeautifulSoup import BeautifulSoup
import datetime
from string import whitespace
import sys
from sqlstuff2 import SqlStuff2
from neuralnetworks import NeuralNetwork
import os.path    
from random import randint
            
class HrefStuff:
    def __init__(self):
        self.fullResultHrefs=[]
        self.raceHrefs=[]
        self.raceTime=[]
        self.raceVenue=[]
       # self.horseName=[]
       # self.jockey=[]
    

    def webscrapePolite(self, href):
        """ check to see if this page already has been collected and is in the results folder
        if it hasn't been read previously then insert a wait between 10s and a minute to
        avoid bombarding the website with requests"""
        href_replace = href.replace("http://www.","")
        href_replace = href_replace.replace(".", "_")
        href_replace = href_replace.replace("/", "_")
        if os.path.isfile("horses_local/"+href_replace+".txt"):
            f=open("horses_local/"+href_replace+".txt", 'r').read()
            self.soup = BeautifulSoup(f)
            print "from file"
        else:
            waitint=randint(10,15)
            time.sleep(waitint)
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            content = opener.open(href).read()
            f=open("horses_local/"+href_replace+".txt", 'w')
            f.write(content)
            self.soup = BeautifulSoup(content)
            print "from web and writing file"
            
        return self.soup


    def getTestCardHref(self, date):
        """ get todays test card link"""
        self.date=date #time.strftime("%Y-%m-%d")
#        self.date="2014-08-03"
        print self.date
        self.url="http://www.racingpost.com/horses2/cards/home.sd?r_date=" + self.date
        return self.url

    def getTodaysRaces(self, href):
        """ get the hrefs for the races, exclude the terrestrial tv and worldwide stakes"""
        self.soup=self.webscrapePolite(href)
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
                if len(self.raceVenue)==0:
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
        #print self.url
        self.soup=self.webscrapePolite(self.url)
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
        self.li=self.ul.findAll("li")[3]
        self.going=self.li.find("strong").find(text=True)

        return (horseName, jockey, self.raceLength, weight, self.going)

    def getFullResultHrefs(self, date):
        """function to get the hrefs for the specified date"""
        self.date=date
        """add the date to the base url"""
        self.url="http://www.racingpost.com/horses2/results/home.sd?r_date=" + self.date
        self.soup=self.webscrapePolite(self.url)
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
        self.soup=self.webscrapePolite(self.href)
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

    def getRaceTime(self):
        """ get the time of the race"""
        try:
            self.h3=self.fullHeader.find("h3")
            self.span=self.h3.find("span", {"class":"timeNavigation"})
            spanStr=unicode.join(u'\n',map(unicode,self.span))
            colonPos=spanStr.index(':')
            self.raceTime=spanStr[colonPos-1:colonPos+3]
            #print self.raceTime
        except AttributeError:
            print "no race time found"

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
        self.getRaceTime()
        self.getHorseNames()
        self.getNumberOfHorses()
        self.getHorseWeightJockeyNameAge()        
        self.getRaceLengthGoing()        
        if self.numberOfHorses != len(self.jockeys):
            print self.numberOfHorses
            print self.jockeys
            print self.horseNames
            print self.raceName
