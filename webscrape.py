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
        if it hasn't been read previously then insert a wait between 1s and 5 seconds to
        avoid bombarding the website with requests"""
        href_replace = href.replace("http://www.","")
        href_replace = href_replace.replace(".", "_")
        href_replace = href_replace.replace("/", "_")
        if os.path.isfile("horses_local/"+href_replace+".txt"):
            f=open("horses_local/"+href_replace+".txt", 'r').read()
            self.soup = BeautifulSoup(f)
            #print "from file"
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
        # get the raceTimes and raceVenue into the same format as that returned by the
        # makeATestcardFromResults function
        raceTimes=[]
        raceVenue=[]
        for idx, daysRaceTimes in enumerate(self.raceTimes):
            for raceTime in daysRaceTimes:
                raceTimes.append(raceTime)
                raceVenue.append(self.raceVenue[idx])


        return self.raceHrefs, raceTimes, raceVenue

    def getCardContents(self, href):
        """ get the horse, jockey, number of horses and distance"""
        horseName=[]
        jockey=[]
        trainer=[]
        weight=[]
        draw=[]
        self.url="http://www.racingpost.com" + href + "&raceTabs=lc_"
        #print self.url
        self.soup=self.webscrapePolite(self.url)
        self.divBody=self.soup.body
        self.cardGridWrapper=self.divBody.find("div", {"class":"cardGridWrapper"})
        self.tr=self.cardGridWrapper.findAll("tr", {"class":"cr"})
        for row in self.tr:
            try:
                draw.append(row.findAll("td")[0].find("sup").find(text=True))                
                #print "found draw"
            except AttributeError:
                draw.append("255")
                #print "did not find draw"
            self.horseNameRow=row.find("a")
            horseName.append(self.horseNameRow.find("b").find(text=True).replace('&acute;',"'"))            
            self.tdJockey=row.findAll("td")[6]
            self.tdTrainer=row.findAll("td")[5]
            try:
                jockey.append(self.tdJockey.find("a").find(text=True))
            except AttributeError:
                jockey.append("unknown")
            try:
                trainer.append(self.tdTrainer.find("a").find(text=True))
            except AttributeError:
                trainer.append("unknown")
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

        return (horseName, jockey, self.raceLength, weight, self.going, draw, trainer)

    def getFullResultHrefs(self, date):
        """function to get the hrefs for the specified date"""
        self.date=date
        """add the date to the base url"""
        self.url="http://www.racingpost.com/results/" + self.date
        self.soup=self.webscrapePolite(self.url)
        self.divBody=self.soup.body
        self.rpContainer=self.divBody.find("div", {"class":"rp-results rp-container cf js-contentWrapper"})
        self.rpResultsWrapper=self.rpContainer.find("div", {"class":"rp-resultsWrapper__content"})
        self.rpRaceCourse=self.rpResultsWrapper.find("div", {"class":"rp-raceCourse"})
        self.rpRaceCourseMeeting=self.rpRaceCourse.findAll("section", {"class":"rp-raceCourse__meetingContainer"})
        # loop through the race courses for the day
        for rpRaceCourseMeeting in self.rpRaceCourseMeeting:
            self.rpRaceCoursePanel=rpRaceCourseMeeting.find("div", {"class":"rp-raceCourse__panel"})
            if not self.rpRaceCoursePanel:
                continue
            self.rpRaceCoursePanelContainer=self.rpRaceCoursePanel.findAll("div", {"class":"rp-raceCourse__panel__container"})
            # loop through the races held at each course
            for rpRaceCoursePanelContainer in self.rpRaceCoursePanelContainer:
                self.fullResultHrefs.append(rpRaceCoursePanelContainer.get("href")) 
                
        """print self.rpRaceCourseMeeting
        for self.fself.rpRaceCoursePanself.rpRaceCoursePanullResultButton in self.fullResultButtons:
            self.fullResultHrefs.append(self.fullResultButton.get("href")) 
            print self.fullResultButton.get("href")"""
        """self.divTabBlock=self.divBody.find("div", {"class":"tabBlock"})        
        self.tableResultGrids=self.divTabBlock.findAll("table", {"class":"resultGrid"})
        for self.tableResultGrid in self.tableResultGrids:
            self.ulBullActiveLinks=self.tableResultGrid.findAll("ul", {"class":"bull activeLink"})
            for self.ulBullActiveLink in self.ulBullActiveLinks:
                self.fullResultHref=self.ulBullActiveLink.find("a")
                self.fullResultHrefs.append(self.fullResultHref.get("href"))        """
        return self.fullResultHrefs
    
    def getFullResults(self, href):
        """function to get the full results from the specified href"""
        self.href="http://www.racingpost.com/" + href
        self.soup=self.webscrapePolite(self.href)
        self.divBody=self.soup.body
        self.rpResults=self.divBody.find("div", {"class":"rp-results rp-container cf js-contentWrapper"})
        self.rpResultsWrapper=self.rpResults.find("main", {"class":"rp-resultsWrapper__content"})
        self.rpResultsSection=self.rpResultsWrapper.find("section", {"class":"rp-resultsWrapper__section"})        

    def getFullResultsHeader(self):
        """returns the header containing race and date etc"""        
        self.rpRaceTimeCourseName=self.rpResultsSection.find("div", {"class":"rp-raceTimeCourseName"})
        return self.rpRaceTimeCourseName        

    def getFullResultsGrid(self):
        """returns the grid will the placings etc"""
        self.rpHorseTable=self.rpResultsSection.find("div", {"class":"rp-horseTable"})        
        self.rpHorseTableContent=self.rpHorseTable.find("table", {"class":"rp-horseTable__table"})
        return self.rpHorseTableContent

    def getFullRaceInfo(self):
        """returns the raceinfo with the number of finishers and time etc."""
        self.rpRaceInfo=self.rpResultsSection.find("div", {"class":"rp-raceInfo"})
        return self.rpRaceInfo


class ResultStuff:
    def __init__(self, fullResult, fullHeader, fullInfo, raceDate):
        self.fullResult=fullResult
        self.fullHeader=fullHeader
        self.fullInfo=fullInfo
        self.raceDate= raceDate
        self.horseNames=[]
        self.odds=[]
        self.draw=[]
        self.horseAges=[]
        self.horseWeights=[]
        self.lengthGoingTypeTemp=[]
        self.jockeys=[]
        self.trainers=[]
        
    def getRaceName(self):
        """ get the name of the race"""
        """ if there is no race info available then do nothing"""
        try:
            self.h1=self.fullHeader.find("h1")
            if not self.h1:
                raise ValueError("did not find h1")


            self.classes=self.h1.findAll("a")
            if not self.classes:
                raise ValueError("did not find a")

            for class_ in self.classes:
                self.class_=class_.get("class").strip()
                if self.class_.find("rp-raceTimeCourseName__name") != -1:
                    self.raceName=class_.find(text=True).strip()

            if not self.raceName:
                raise AttributeError
            print "raceName is " + str(self.raceName)
        except AttributeError:
            print "no RaceName found"

    def getRaceTime(self):
        """ get the time of the race"""
        try:
            self.h1=self.fullHeader.find("h1")
            self.span=self.h1.find("span", {"class":"rp-raceTimeCourseName__time"})
            spanStr=unicode.join(u'\n',map(unicode,self.span))
            colonPos=spanStr.index(':')
            self.raceTime=spanStr[colonPos-1:colonPos+3]
            print "race time is " + str(self.raceTime)
        except AttributeError:
            print "no race time found"


    def getNumberOfHorses(self):
        """get the number of horses that ran in the race"""
        try:
            self.numberOfHorses=len(self.horseNames)
        except AttributeError:
            print "no horseNames found cannot get numberOfHorses"


    def isNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


    def getRaceLengthGoingJumps(self, verbose=0):
        """function to find the race length and the going"""
        try:
            self.rpRaceTimeCourseNameInfo=self.fullHeader.find("div", {"class":"rp-raceTimeCourseName__info"})
            self.rpRaceTimeCourseNameInfoContainer=self.rpRaceTimeCourseNameInfo.find("span", {"class":"rp-raceTimeCourseName__info_container"})
            self.rpRaceTimeCourseNameCondition=self.rpRaceTimeCourseNameInfoContainer.find("span", {"class":"rp-raceTimeCourseName_condition"})
            self.rpRaceTimeCourseNameDistance=self.rpRaceTimeCourseNameInfoContainer.find("span", {"class":"rp-raceTimeCourseName_distanceFull"})
            # if the full distance is not found then look for the non full version of the distance
            if not self.rpRaceTimeCourseNameDistance:
                self.rpRaceTimeCourseNameDistance=self.rpRaceTimeCourseNameInfoContainer.find("span", {"class":"rp-raceTimeCourseName_distance"})               
            self.goingType=self.rpRaceTimeCourseNameCondition.find(text=True)
            self.going=self.goingType.strip()
            print "going is " + str(self.going)

            self.DistanceText=self.rpRaceTimeCourseNameDistance.find(text=True)
            self.DistanceStrip=self.DistanceText.strip()
            self.raceLength=re.sub('[()]', '', self.DistanceStrip)
            print "length is " + str(self.raceLength)

            """self.lengthGoingTypeArray=self.lengthGoingType.strip().splitlines()          

            try:                
                g=self.lengthGoingTypeTemp[0].split()
                self.going=''
                self.jumps=0
                for going in g[1:len(g)]:
                    if self.isNumber(going)==True:
                        self.jumps=int(going)
                        break
                    self.going=str(self.going) + ' ' + str(going)
                if verbose != 0:
                    print "going= " + str(self.going)
            except IndexError:
                self.going="?unknown?"
                self.jumps=255"""

            """for s in self.lengthGoingTypeArray:               
                if not re.match(r'^\s*$', s):
                    if '(' not in s:               
                        self.lengthGoingTypeTemp.append(s)
            #get rid of the strange unicode half symbols
            s=self.lengthGoingTypeTemp[0].split()[0]#.encode('unicode_escape')
            self.raceLength = s.replace('\\xbd', '.5')
            self.raceLength = self.raceLength.replace('&frac12;', '.5')"""
            
        except:
            print "couldn't get raceLength or going"

    def getRaceFinishingTimes(self, verbose=0):
        """function to get the race finishing time from the result popup"""
        ref=10000
        minutes=0
        seconds=0
        self.ul=self.fullInfo.find("ul")
        self.li=self.ul.find("li")
        self.span=self.li.findAll("span", {"class":"rp-raceInfo__value"})[0].find(text=True).strip()
        print "race finish time is " + str(self.span)
        self.raceFinishTime=str(self.span)
        for ii, self.info in enumerate(self.raceFinishTime.split()):
            if ii==0:
                minutes=self.info.split("m")[0]
                if len(self.info.split("m"))==1:
                    minutes=float(0)
                    seconds=float(self.info.split("s")[0])
                    break
            if ii==1:
                seconds=float(self.info.split("s")[0])
        if verbose!=0:
            print "minutes " + str(minutes)
            print "seconds " + str(seconds)
        time = 60*float(minutes)+seconds
        self.finishingTime=time

    def remove(soup, tagname):
        print "heeelllllo!"
        for tag in soup.findAll(tagname):
            print str(tag)
            contents = tag.contents
            parent = tag.parent
            tag.extract()
            for tag in contents:
                parent.append(tag)


    def getOdds(self):
        """function to find all of the odds in the full result popup"""
        """if there are no odds available then do nothing"""
        try:
            self.bodys=self.fullResult.find("tbody")
            self.trs=self.bodys.findAll("tr", {"class":"rp-horseTable__mainRow"})
            for self.tr in self.trs:

                self.td=self.tr.find("td", {"class":"rp-horseTable__horseCell"})
                self.div=self.td.find("div", {"class":"rp-horseTable__horse"})
                self.div=self.div.find("div")
                self.horsePrice=self.div.find("span", {"class":"rp-horseTable__horse__price"}).find(text=True).strip()
                self.horsePrice=re.sub('[A-Za-z]', '', self.horsePrice)
                self.odds.append(self.horsePrice)

            print self.odds
        except AttributeError:
            print "no odds found"


    def getHorseNames(self):
        """function to find all of the horse names in the full result popup"""
        """if there are no horsenames available then do nothing"""
        try:
            self.bodys=self.fullResult.find("tbody")
            self.trs=self.bodys.findAll("tr", {"class":"rp-horseTable__mainRow"})
            for self.tr in self.trs:

                self.td=self.tr.find("td", {"class":"rp-horseTable__horseCell"})
                self.div=self.td.find("div", {"class":"rp-horseTable__horse"})
                self.div=self.div.find("div")
                self.horseName=self.div.find("a").find(text=True).strip()
                self.horseNames.append(self.horseName)
            print self.horseNames
                
        except AttributeError:
            print "no HorseNames found"

    def getDraw(self):
        """function to find all of the horse ages in the full result popup"""
        """if there are no horse ages available then do nothing"""
        try:
            self.bodys=self.fullResult.find("tbody")
            self.trs=self.bodys.findAll("tr", {"class":"rp-horseTable__mainRow"})

            for self.tr in self.trs:
                self.td=self.tr.find("td")
                self.div=self.td.find("div", {"class":"rp-horseTable__pos"})
                self.span=self.div.findAll("span")
                for span in self.span:
                    if str(span).find('sup') != -1:
                        self.sup=span.find('sup')
                        self.draw.append(re.sub('[^0-9]', '', str(self.sup)).strip())
            print "the draw is " + str(self.draw)
            """
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               for self.tr in self.trs:
                   #use this if to get rid of the None results when class=black is not found
                   if self.tr.find("td", {"class":"nowrap noPad"}):
                       try:
                           self.draw.append(self.tr.find("td", {"class":"nowrap noPad"}).find("span", {"class":"draw"}).find(text=True))
                       except AttributeError:
                           # if a draw is not found then it was a hurdles race.  255 indicates this
                           self.draw.append("255")
                       #print "draw=" + str(self.tr.find("td", {"class":"nowrap noPad"}).find("span", {"class":"draw"}).find(text=True))"""
        except AttributeError:
            print "something went wrong finding the draw"


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

    def getTrainerName(self):
        """function to get all of the trainer names in the result popup"""
        try:
            self.bodys=self.fullResult.findAll("tbody")
            for self.body in self.bodys:
               self.trs=self.body.findAll("tr")
               for self.tr in self.trs:
                   if self.tr.findAll("td", {"class":"nowrap black"})[1]:
                       clg=self.tr.findAll("td", {"class":"lightGray"})[1]
                       if clg.find("a"):
                           self.trainers.append(clg.find("a").find(text=True)) 
        except AttributeError:
            print "No trainers found"

                    

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

    def getWeightAgeJockeyTrainer(self):
        """function to get the weight jockey and going"""
        try:
            self.bodys=self.fullResult.find("tbody")
            self.trs=self.bodys.findAll("tr", {"class":"rp-horseTable__mainRow"})

            for self.tr in self.trs:
                self.humanTd=self.tr.find("td", {"class":"rp-horseTable__humanCell"})
                self.ageTd=self.tr.find("td", {"class":"rp-horseTable__spanNarrow"})
                self.wgtTd=self.tr.find("td", {"class":"rp-horseTable__spanNarrow rp-horseTable__wgt"})

                self.humanDiv=self.humanTd.find("div", {"class": "rp-horseTable__human"})
                self.humanSpan=self.humanDiv.findAll("span", {"class": "rp-horseTable__human__wrapper"})
                self.jockeys.append(self.humanSpan[0].find("a").find(text=True).strip())
                self.trainers.append(self.humanSpan[1].find("a").find(text=True).strip())
                self.horseAges.append(self.ageTd.find(text=True).strip())
                self.wgtSpanSt=self.wgtTd.find("span", {"class": "rp-horseTable__st"})
                self.wgtSpanLb=self.wgtTd.find("span", {"data-ending": "lb"})
                wgt=self.wgtSpanSt.find(text=True).strip()+"-"+re.sub('[^0-9]', '', str(self.wgtSpanLb))
                self.horseWeights.append(wgt)

            print "jockeys " + str(self.jockeys)
            print "ages " + str(self.horseAges)
            print "weights " + str(self.horseWeights)
        except AttributeError:
            print "no tbody found in the full result"

    def getAllResultInfo(self):
        """ function to get all of the sql info"""
        self.getRaceName()
        self.getRaceTime()
        self.getHorseNames()
        self.getOdds()
        self.getDraw()
        self.getNumberOfHorses()
        self.getWeightAgeJockeyTrainer()
        self.getRaceLengthGoingJumps()
        self.getRaceFinishingTimes()
        if self.numberOfHorses != len(self.jockeys):
            print self.numberOfHorses
            print self.jockeys
            print self.horseNames
            print self.raceName
