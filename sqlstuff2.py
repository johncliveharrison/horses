import sqlite3
import re

class SqlStuff2:
    def __init__(self):
        """initialise the sql stuff"""
        #self.conn=sqlite3.connect('results_2017.db')
    def connectDatabase(self, databaseName):
        """connect to the results.db database"""
        self.conn=sqlite3.connect(databaseName)
    def createResultTable(self):
        """ create a table to hold all of the scraped results"""
        self.conn.execute("CREATE TABLE if not exists RESULTS_INFO( \
            ID INTEGER PRIMARY KEY AUTOINCREMENT, \
            HORSENAME TEXT, \
            HORSEAGE INTEGER, \
            HORSEWEIGHT TEXT, \
            POSITION INTEGER, \
            RACELENGTH TEXT, \
            NUMBERHORSES INTEGER, \
            JOCKEYNAME TEXT, \
            GOING TEXT, \
            RACEDATE DATE, \
            RACETIME, \
            RACEVENUE, \
            DRAW INTEGER, \
            TRAINERNAME TEXT, \
            FINISHINGTIME INTEGER, \
            ODDS TEXT);")

    def addResultStuffToTable(self, ResultStuff):
        for idx, self.horseName in enumerate(ResultStuff.horseNames):
            """create a string with this horses values"""
            self.val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'".format(\
                ResultStuff.horseNames[idx].replace("'", "''"),\
                ResultStuff.horseAges[idx], ResultStuff.horseWeights[idx], idx+1, \
                ResultStuff.raceLength, ResultStuff.numberOfHorses, ResultStuff.jockeys[idx].replace("'", "''"), \
                ResultStuff.going, ResultStuff.raceDate, ResultStuff.raceTime, \
                ResultStuff.raceName.replace("'", "''"), ResultStuff.draw[idx], \
                ResultStuff.trainers[idx].replace("'", "''"), ResultStuff.finishingTime, ResultStuff.odds[idx])
            #print self.val_str
            """create a string for the sql command"""
            self.sql_str="INSERT INTO RESULTS_INFO \
                (HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, RACETIME, RACEVENUE, DRAW, TRAINERNAME, FINISHINGTIME, ODDS) \
                VALUES ({});".format(self.val_str)
            #print self.sql_str
            self.conn.execute(self.sql_str)
            self.conn.commit()

    def getAllTable(self, date=-1):
        if date==-1:
            self.sql_str="SELECT * from RESULTS_INFO"
        else:
            self.sql_str="SELECT * from RESULTS_INFO where RACEDATE<'{}'".format(date)
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows

    def viewAllTable(self):
        self.getAllTable()
        for row in self.rows:
            print row

    def delDate(self, date):
        self.sql_str="DELETE from RESULTS_INFO where RACEDATE='{}'".format(date)
        self.conn.execute(self.sql_str)
        self.conn.commit()

    def delDuplicates(self):
        self.sql_str="DELETE from RESULTS_INFO where ID NOT IN (SELECT MIN(ID) ID FROM RESULTS_INFO GROUP BY HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, RACETIME, RACEVENUE, DRAW, TRAINERNAME, FINISHINGTIME, ODDS)"
        self.conn.execute(self.sql_str)
        self.conn.commit()

        
    def getDate(self, date):
        self.sql_str="SELECT * from RESULTS_INFO where RACEDATE='{}'".format(date)
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows

    def getAlGloing(self):
        """get all of the going information from the database"""
        self.sql_str="SELECT GOING from RESULTS_INFO"
        self.cursor=self.conn.execute(self.sql_str)
        allGoing=self.cursor.fetchall()
        return allGoing

    def getPosition(self, position):
        self.sql_str="SELECT * from RESULTS_INFO where POSITION='{}'".format(position)
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows

    def getTopWinners(self):
        winners=self.getPosition(1)
        winnerList=[]
        tally=[]
        for winner in winners:
            added=False
            for idx, entry in enumerate(winnerList):
                if winner[1]==entry[1]:
                    tally[idx]+=1
                    added=True
                    break
            if added==False:
                winnerList.append(winner)
                tally.append(1)
        greatest=0
        for idx, entry in enumerate(winnerList):
            #print entry[1] + " has won " + str(tally[idx]) + " times"
            if tally[idx] > greatest:
                greatest = tally[idx]
                greatestIdx = idx;
        print "the most wins is " + winnerList[greatestIdx][1] + " with " + str(greatest) + "  wins"
        return winnerList

    def getHorse(self, horseName):
        self.sql_str="SELECT * from RESULTS_INFO where HORSENAME='{}'".format(horseName.replace("'", "''"))
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows

    def getJockey(self, jockeyName):
        self.sql_str="SELECT * from RESULTS_INFO where JOCKEYNAME='{}'".format(jockeyName.replace("'", "''"))
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows    
    
    def getTrainer(self, trainerName):
        self.sql_str="SELECT * from RESULTS_INFO where TRAINERNAME='{}'".format(trainerName.replace("'", "''"))
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows    


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
            elif s=="y" or s=="yds":
                meters=meters+number
                number=0
            elif skip==0:
                number=number+float(s)
            else:
                skip=0                   
        return meters

    
   
    def viewHorse(self, horseName):        
        self.rows=self.getHorse(horseName)
        for self.row in self.rows:
            print self.row
            print str(self.convertRaceLengthMetres(self.row[5]))
            print str(self.convertRaceLengthMetres(self.row[5])/self.row[14])

    def viewJockey(self, jockeyName):
        self.rows=self.getJockey(jockeyName)
        for self.row in self.rows:
            print self.row

    def viewDate(self, date):        
        self.rows=self.getDate(date)
        for self.row in self.rows:
            print self.row

    def viewNewestDate(self):
        self.sql_str="SELECT *, max(RACEDATE) as MaxDate from RESULTS_INFO"
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        print self.rows
