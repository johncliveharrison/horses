import urllib2,  time, re
#from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import time

#import dryscrape
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
    

    def webscrapePolite(self, href, verbose=0, test=0):
        """ check to see if this page already has been collected and is in the results folder
        if it hasn't been read previously then insert a wait between 1s and 5 seconds to
        avoid bombarding the website with requests"""
        if verbose:
            print "href = " + str(href)
        href_replace = href.replace("http://www.","")
        href_replace = href_replace.replace(".", "_")
        href_replace = href_replace.replace("/", "_")
        if verbose:
            print str(href_replace)
        if os.path.isfile("horses_local/"+href_replace+".txt"):
            f=open("horses_local/"+href_replace+".txt", 'r').read()
            self.soup = BeautifulSoup(f)
            #print "from file"
        else:
            if test==1:
                sys.exit()
            waitint=randint(10,15)
            #time.sleep(waitint)
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            while True:
                try:
                    content = opener.open(href).read()
                    break
                except Exception, e:
                    print href
                    print e
                    if str(e).find('404') != -1:
                        print "webscrapePolite: skipping this result"
                        raise Exception(str(e))
                    elif str(e).find('403') != -1:
                        print "waiting for the 403 to timeout"
                        time.sleep(120)
                        content = opener.open(href).read()
                    else:
                        print e
                        raise Exception(str(e))
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
        self.url="https://www.racingpost.com/racecards/" + self.date
        return self.url

    def getTodaysRaces(self, href, verbose=False):
        """ get the hrefs for the races, exclude the terrestrial tv and worldwide stakes"""
        try:
            self.soup=self.webscrapePolite(href)
        except Exception, e:
            print "unable to scrape the test card main page"
            raise Exception(str(e))
        self.divBody=self.soup.body
        self.uiCanvas=self.divBody.find("div", {"class":"ui-canvas js-contentWrapper ui-advertising__skinsWrp ui-advertising__skinsWrp_secNav"})
        #print "uiCanvas ****************************************************"
        #print str(self.uiCanvas)
        self.uiContent=self.uiCanvas.findAll("div")#, {"class":"ui-content"})
        for content in self.uiContent:
            if content.find("div", {"data-test-selector":"RC-accordion__body"}):
                self.uiAccordianRows=content.find("div", {"data-test-selector":"RC-accordion__body"})
                break
        #self.mainContent=self.uiContent.find("main", {"class": ['js-RC-mainContent', 'RC-content-wrapper', 'ui-mainContent']})
        #print "mainContent ****************************************************"
        #print str(self.mainContent)
        #self.uiAccordianRows=self.mainContent.find("div", {"data-test-selector":"RC-accordion__body"})#"ui-accordion" "js-accordion" "RC-accordion"})# js-accordion RC-accordion"})
        #print "uiAccordianRows ****************************************************"
        #print str(self.uiAccordianRows)
        self.sectionRows=self.uiAccordianRows.findAll("section")#, {"class":"ui-accordion__row"})# js-accordion RC-accordion"})
      #  print "uiAccordian***************************************************"
        #print str(self.sectionRows)
        self.raceVenue=[]
        self.raceTimes=[[] for _ in range(len(self.sectionRows[:]))]
        for idx, uiAccordianRow in enumerate(self.sectionRows):
            rowSection= uiAccordianRow.findAll("div")
            header=rowSection[0]
            table=rowSection[3]
            h2Header=header.find("h2")
            divH2Header=h2Header.find("div")
            spanDivH2Header=divH2Header.find("span")
            maybeAbandoned=divH2Header.findAll("span")
            if len(maybeAbandoned) > 1:
                if "abandoned" in maybeAbandoned[1].get("class"):
                    continue
            raceVenue=" ".join(spanDivH2Header.find(text=True).split())
            if raceVenue == "Free to air TV Races":
                continue
            if raceVenue == "Worldwide Stakes Races":
                continue
            if raceVenue == "Scoop 6":
                continue
            if raceVenue == "WORLDWIDE STAKES":
                continue
                
            self.raceVenue.append(raceVenue)
            if verbose:
                print "so I got this far " + str(raceVenue)

            courseDescription=table.find("div", {"class":"RC-courseDescription__info"})
            meetingList=table.find("div", {"class":"RC-meetingList"})
            meetingItems=meetingList.findAll("div", {"class":"RC-meetingItem"})
            for meetingItem in meetingItems:
                href=meetingItem.find("a", {"class":"RC-meetingItem__link js-navigate-url"}).get("href")
                self.raceHrefs.append(href)
                time=meetingItem.find("div", {"class":"RC-meetingItem__time"}).find(text=True).strip()
                self.raceTimes[idx].append(time)
                if verbose:
                    print "and the time is " + str(time)
        # get the raceTimes and raceVenue into the same format as that returned by the
        # makeATestcardFromResults function
        raceTimes=[]
        raceVenue=[]
        for idx, daysRaceTimes in enumerate(self.raceTimes):
            for raceTime in daysRaceTimes:
                raceTimes.append(raceTime)
                raceVenue.append(self.raceVenue[idx])


        return self.raceHrefs, raceTimes, raceVenue

    def getCardContents(self, href, verbose=False):
        """ get the horse, jockey, number of horses and distance"""
        horseName=[]
        jockey=[]
        trainer=[]
        weight=[]
        draw=[]
        odd=[]
        self.url="https://www.racingpost.com" + href + "&raceTabs=lc_"
        try:
            self.soup=self.webscrapePolite(self.url)
        except Exception, e:
            print "self.soup=self.webscrapePolite(self.url)"
            print str(e)
            raise Exception(e);
        try:
            self.divBody=self.soup.body
        except Exception, e:
            print "self.divBody=self.soup.body"
            print str(e)
            raise Exception(e)
        try:
            self.uiCanvas=self.divBody.find("div", {"class":"ui-canvas js-contentWrapper ui-advertising__skinsWrp ui-advertising__skinsWrp_secNav"})
        except Exception, e:
            print "self.uiCanvas=self.divBody.find(div, {class:ui-canvas js-contentWrapper ui-advertising__skinsWrp ui-advertising__skinsWrp_secNav})"
            print str(e)
            raise Exception(e)
        try:
            self.uiContent=self.uiCanvas.find("div")#, {"class":"ui-content ui-content_marginless js-ui-content RC-desktop"})
        except Exception, e:
            print "self.uiContent=self.uiCanvas.find(div, {class:ui-content ui-content_marginless js-ui-content RC-mobile RC-desktop})"
            print str(e)
            raise Exception(e)
        try:
            main=self.uiContent.find("main")
        except Exception, e:
            print "main=self.uiContent.find(main)"
            print str(e)
            raise Exception(e)
        try:
            section=main.find("section")
        except Exception, e:
            print "section=main.find(section)"
            print str(e)
            raise Exception(e)

        #raceLength
        if verbose:
            print "got this far 1"
        cardHeader=section.find("div", {"class":"RC-cardHeader"})
        cardHeaderDetails=cardHeader.findAll("div")[-1]
        distance=cardHeaderDetails.find("strong", {"class":"RC-cardHeader__distance"}).find(text=True).strip()
        s=distance.strip("()")
        self.raceLength = s.replace('\\xbd', '.5')
        # try and get the rows in the table with the horse info
        sectionDiv=section.findAll("div", recursive=False)#"div", {"class":["RC-runnerRowwrapper", "js-RC-runnerRowWrapper"]})
        #print sectionDiv
        if verbose:
            print "got this far 2"
        for card in sectionDiv:
            if "RC-runnerRowWrapper" in card.get("class"):
                cardTable=card
        cardTableRows=[]
        cardTableDiv=cardTable.findAll("div")
        for rows in cardTableDiv:
            if "js-RC-runnerRow" in rows.get("class"):
                if not "js-runnerNonRunner" in rows.get("class"):
                    cardTableRows.append(rows)
        if verbose:
            print "got this far 3"

        try:
            CHROME_PATH = '/usr/bin/google-chrome'
            CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
            WINDOW_SIZE = "1920,1080"

            chrome_options = Options()  
            chrome_options.add_argument("--headless")  
            chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
            chrome_options.binary_location = CHROME_PATH
            
            driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                      chrome_options=chrome_options)  
            #driver = webdriver.Chrome()
            driver.get(self.url)
            time.sleep(15)
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource)
        except Exception, e:
            print "problem with selenium"
            raise Exception(str(e))

        for cardTableRow in cardTableRows:

            runnerCardWrapper=cardTableRow.find("div",{"class":"RC-runnerCardWrapper"})

            #horseName
            runnerRowHorseWrapper=runnerCardWrapper.find("div",{"class":"RC-runnerRowHorseWrapper"})
            runnerMainWrapper=runnerRowHorseWrapper.find("div",{"class":"RC-runnerMainWrapper"})
            a=runnerMainWrapper.find("a").find(text=True).strip()
            horseName.append(a)
            if verbose:
                print "horse name is " + str(a)
            #odds
            # get the javascript elements
            try:
                odds = soup.find("div",{"data-diffusion-horsename":str(a)})
                odds = odds.find("a").attrs
                print odds[0]
                odds = odds[4]
                #odds = odds.find("a", {"data-diffusion-fractional").find(text=True)
                #uibtn=htmlSource.find_element_by_class_name('ui-btn')

                print str(a)
                print odds[1]
                odd.append(odds[1])

            except Exception,e:
                print "error from selenium"
                print str(self.url)
                print str(e)
                raise Exception(str(e))

            #jockey
            runnerRowInfoWrapper=runnerCardWrapper.find("div",{"class":"RC-runnerRowInfoWrapper"})
            runnerInfoWrapper=runnerRowInfoWrapper.find("div",{"class":"RC-runnerInfoWrapper"})
            runnerInfoJockey=runnerInfoWrapper.find("div",{"class":"RC-runnerInfo RC-runnerInfo_jockey"})
            a=runnerInfoJockey.find("a").find(text=True).strip()
            jockey.append(a)
            if verbose:
                print "jockey is " + str(a)
            #trainer
            runnerInfoTrainer=runnerInfoWrapper.find("div",{"class":"RC-runnerInfo RC-runnerInfo_trainer"})
            a=runnerInfoTrainer.find("a").find(text=True).strip()
            trainer.append(a)
            if verbose:
                print "trainer is " + str(a)
            #weight
            runnerWgtOrWrapper=runnerRowInfoWrapper.find("div",{"class":"RC-runnerWgtorWrapper"})
            runnerWgt=runnerWgtOrWrapper.find("div",{"class":"RC-runnerWgt"})
            runnerWgtCarried=runnerWgt.find("span",{"class":"RC-runnerWgt__carried"})
            runnerWgtCarriedSt=runnerWgtCarried.find("span",{"class":"RC-runnerWgt__carried_st"}).find(text=True).strip()
            runnerWgtCarriedLb=runnerWgtCarried.find("span",{"class":"RC-runnerWgt__carried_lb"}).find(text=True).strip()
            Wgt=str(runnerWgtCarriedSt)+"-"+str(runnerWgtCarriedLb)
            weight.append(Wgt)          
            if verbose:
                print "weight is " + str(Wgt)
            #draw
            runnerNumber=runnerRowHorseWrapper.find("div",{"class":"RC-runnerNumber"})
            s=runnerNumber.find("span",{"class":"RC-runnerNumber__draw"}).find(text=True).strip().strip("()")
            draw.append(s)
            if verbose:
                print "draw is " + str(s)
        if verbose:
            print "got this far 4"
        #going
        keyInfo=cardHeader.find("div",{"class":"RC-cardHeader__keyInfo"})
        headerBox=keyInfo.find("div",{"class":"RC-headerBox"})
        infoRow=headerBox.findAll("div",{"class":"RC-headerBox__infoRow"})
        going=infoRow[2].find("div",{"class":"RC-headerBox__infoRow__content"}).find(text=True).split()
        if verbose:
            print going
        self.going=" ".join(going)

        return (horseName, jockey, self.raceLength, weight, self.going, draw, trainer, odd)

    def getFullResultHrefs(self, date):
        """function to get the hrefs for the specified date"""
        self.date=date
        """add the date to the base url"""
        self.url="http://www.racingpost.com/results/" + self.date
        self.soup=self.webscrapePolite(self.url)
        self.divBody=self.soup.body
        try:
            self.rpContainer=self.divBody.find("div", {"class":"rp-results rp-container cf js-contentWrapper"})
        except Exception, e:
            print "self.rpContainer=self.divBody.find"
            raise Exception(str(e))

        try:
            self.rpResultsWrapper=self.rpContainer.find("div", {"class":"rp-resultsWrapper__content"})
        except Exception, e:
            print "self.rpResultsWrapper=self.rpContainer.find"
            raise Exception(str(e))

        try:
            self.rpDataDirectiveRaceCourse=self.rpResultsWrapper.find("main", {"data-test-selector":"results-main-container"})
        except Exception, e:
            raise Exception(str(e))

        try:
            self.rpRaceCourse=self.rpDataDirectiveRaceCourse.find("div", {"class":"rp-raceCourse ui-accordion"})
        except Exception, e:
            print "self.rpRaceCourse=self.rpResultsWrapper.find"
            raise Exception(str(e))
 
        try:
            self.rpRaceCourseMeeting=self.rpRaceCourse.findAll("section", {"class":"rp-raceCourse__meetingContainer ui-accordion__row"})
        except Exception, e:
            print "self.rpRaceCourseMeeting=self.rpRaceCourse.findAll"
            raise Exception(str(e))

       # loop through the race courses for the day
        for rpRaceCourseMeeting in self.rpRaceCourseMeeting:
            try:
                self.rpRaceCoursePanel=rpRaceCourseMeeting.find("div", {"class":"rp-raceCourse__panel ui-accordion__content hidden"})
            except Exception, e:
                print "self.rpRaceCoursePanel=rpRaceCourseMeeting.find"
                raise Exception(str(e))
                
            if not self.rpRaceCoursePanel:
                continue

            try:
                self.rpRaceCoursePanelContainer=self.rpRaceCoursePanel.findAll("div", {"class":"rp-raceCourse__panel__container"})
            except Exception, e:
                print "self.rpRaceCoursePanelContainer=self.rpRaceCoursePanel.findAll"
                raise Exception(str(e))

            # loop through the races held at each course
            for rpRaceCoursePanelContainer in self.rpRaceCoursePanelContainer:
                try:
                    self.rpRaceCoursePanelRace=rpRaceCoursePanelContainer.find("div", {"data-diffusion-coursename":"WORLD WIDE STAKES"})
                    if len(self.rpRaceCoursePanelRace) > 0:
                        print "skipping the WORLD WIDE STAKES race"
                        continue
                except Exception,e:
                    pass
                try:
                    self.rpRaceCoursePanelRace=rpRaceCoursePanelContainer.find("div", {"data-diffusion-coursename":"SCOOP6 RACES"})
                    if len(self.rpRaceCoursePanelRace) > 0:
                        print "skipping the SCOOP6 race"
                        continue
                except Exception,e:
                    pass
                
                try:
                    self.rpRaceCoursePanelRace=rpRaceCoursePanelContainer.find("div", {"class":"rp-raceCourse__panel__race"})
                except Exception, e:
                    print "self.rpRaceCoursePanelRace=rpRaceCoursePanelContainer.find"
                    raise Exception(str(e))
                try:
                    self.fullResultHrefs.append(self.rpRaceCoursePanelRace.get("href")) 
                except Exception, e:
                    print "self.fullResultHrefs.append"
                    raise Exception(str(e))

                        
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
        try:
            self.soup=self.webscrapePolite(self.href)
        except Exception, e:
            raise Exception(str(e))
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

class ResultStuffObj:
    def __init__(self):
        self.raceDate =""
        self.raceTime =""
        self.raceName =""
        self.raceLength =""
        self.numberOfHorses = 0
        self.horseNames=[]
        self.odds=[]
        self.draw=[]
        self.horseAges=[]
        self.horseWeights=[]
        self.lengthGoingTypeTemp=[]
        self.jockeys=[]
        self.trainers=[]
        self.finishingTime=[]
        self.going=[]

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
        self.finishingTime=[]

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
            #print "raceName is " + str(self.raceName)
        except AttributeError:
            print "no RaceName found"

    def getRaceTime(self):
        """ get the time of the race"""
        try:
            self.h1=self.fullHeader.find("h1")
        except Exception ,e:
            print "self.h1=self.fullHeader.find"
            raise Exception(str(e));

        try:
            self.span=self.h1.find("span", {"class":"rp-raceTimeCourseName__time"})
        except Exception, e:
            print "self.span=self.h1.find"
            raise Exception(str(e))
        
        try:
            spanStr=unicode.join(u'\n',map(unicode,self.span))
            colonPos=spanStr.index(':')
            self.raceTime=spanStr[colonPos-1:colonPos+3]
            #print "race time is " + str(self.raceTime)
        except AttributeError:
            print str(self.span)
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
            #print "going is " + str(self.going)

            self.DistanceText=self.rpRaceTimeCourseNameDistance.find(text=True)
            self.DistanceStrip=self.DistanceText.strip()
            self.raceLength=re.sub('[()]', '', self.DistanceStrip)
            #print "length is " + str(self.raceLength)

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

    def getRaceFinishingTimes(self, verbose=False):
        """function to get the race finishing time from the result popup"""
        ref=10000
        minutes=0
        seconds=0
        try:
            self.ul=self.fullInfo.find("ul")
        except Exception, e:
            print "missing time - probable void race"
            self.finishingTime=0
            raise Exception(str(e))
        try:
            self.li=self.ul.find("li")
        except:
            print "missing time - probable void race"
            self.finishingTime=0
            raise Exception(str(e))
        try:
            self.span=self.li.findAll("span", {"class":"rp-raceInfo__value"})
        except:
            print "missing time - probable void race"
            self.finishingTime=0
            raise Exception(str(e))
 
        if verbose:
            print "found %d rp-raceInfo__value fields" % len(self.span)
        for value in self.span:

            self.raceFinishTime=str(value.find(text=True).strip())
            if verbose:
                print "race finish time is " + str(self.raceFinishTime)

            try:
                for ii, self.info in enumerate(self.raceFinishTime.split()):
                    if ii==0:
                        minutes=self.info.split("m")[0]
                        if len(self.info.split("m"))==1:
                            minutes=float(0)
                            seconds=float(self.info.split("s")[0])
                            break
                    if ii==1:
                        seconds=float(self.info.split("s")[0])
            except Exception,e:
                continue

            if verbose:
                print "minutes " + str(minutes)
                print "seconds " + str(seconds)
            time = 60*float(minutes)+seconds
            if verbose:
                print "time is " + str(time)
            if time > 0:
                break
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
                self.horseTableHorseContainer=self.td.find("div", {"class":"rp-horseTable__horseContainer"})
                self.horseTableInfo=self.horseTableHorseContainer.find("div", {"class":"rp-horseTable__info"})

                self.div=self.horseTableInfo.find("div", {"class":"rp-horseTable__horse"})
                self.horseDetails=self.div.find("span", {"class":"rp-horseTable__horse__details"})
                self.horsePrice=self.horseDetails.find("span", {"class":"rp-horseTable__horse__price"}).find(text=True).strip()
                self.horsePrice=re.sub('[A-Za-z]', '', self.horsePrice)
                self.odds.append(self.horsePrice)

            #print self.odds
        except AttributeError:
            print "no odds found"


    def getHorseNames(self):
        """function to find all of the horse names in the full result popup"""
        """if there are no horsenames available then do nothing"""
        try:
            self.bodys=self.fullResult.find("tbody")
        except Exception:
            print "tbody not found"
        try:
            self.trs=self.bodys.findAll("tr", {"class":"rp-horseTable__mainRow"})
        except Exception:
            print "horseTable__mainRow not found"
        try:
            for self.tr in self.trs:
                self.td=self.tr.find("td", {"class":"rp-horseTable__horseCell"})
                self.horseTableHorseContainer=self.td.find("div", {"class":"rp-horseTable__horseContainer"})
                self.horseTableInfo=self.horseTableHorseContainer.find("div", {"class":"rp-horseTable__info"})

                self.div=self.horseTableInfo.find("div", {"class":"rp-horseTable__horse"})
                #self.div=self.div.find("div")
                self.horseName=self.div.find("a").find(text=True).strip()
                self.horseNames.append(self.horseName)
            #print self.horseNames
                
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
            #print "the draw is " + str(self.draw)
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

            #print "jockeys " + str(self.jockeys)
            #print "ages " + str(self.horseAges)
            #print "weights " + str(self.horseWeights)
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
        try:
            self.getRaceFinishingTimes()
        except:
            pass
        if self.numberOfHorses != len(self.jockeys):
            print self.numberOfHorses
            print self.jockeys
            print self.horseNames
            print self.raceName
