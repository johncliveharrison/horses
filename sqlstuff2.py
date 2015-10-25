import sqlite3

class SqlStuff2:
    def __init__(self):
        """initialise the sql stuff"""
        self.conn=sqlite3.connect('results5.db')
    def connectDatabase(self):
        """connect to the results.db database"""
        self.conn=sqlite3.connect('results5.db')
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
            JUMPS INTEGER, \
            FINISHINGTIME INTEGER);")

    def addResultStuffToTable(self, ResultStuff):
        for idx, self.horseName in enumerate(ResultStuff.horseNames):
            """create a string with this horses values"""
            self.val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}".format(\
                ResultStuff.horseNames[idx].replace("'", "''"),\
                ResultStuff.horseAges[idx], ResultStuff.horseWeights[idx], idx+1, \
                ResultStuff.raceLength, ResultStuff.numberOfHorses, ResultStuff.jockeys[idx].replace("'", "''"), \
                ResultStuff.going, ResultStuff.raceDate, ResultStuff.raceTime, \
                ResultStuff.raceName.replace("'", "''"), ResultStuff.draw[idx], \
                ResultStuff.trainers[idx].replace("'", "''"), ResultStuff.jumps, ResultStuff.finishingTime)
            #print self.val_str
            """create a string for the sql command"""
            self.sql_str="INSERT INTO RESULTS_INFO \
                (HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, RACETIME, RACEVENUE, DRAW, TRAINERNAME, JUMPS, FINISHINGTIME) \
                VALUES ({});".format(self.val_str)
            #print self.sql_str
            self.conn.execute(self.sql_str)
            self.conn.commit()

    def getAllTable(self):
        self.sql_str="SELECT * from RESULTS_INFO"
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

    def getDate(self, date):
        self.sql_str="SELECT * from RESULTS_INFO where RACEDATE='{}'".format(date)
        self.cursor=self.conn.execute(self.sql_str)
        self.rows=self.cursor.fetchall()
        return self.rows

    def getAllGoing(self):
        """get all of the going information from the database"""
        self.sql_str="SELECT GOING from RESULTS_INFO"
        self.cursor=self.conn.execute(self.sql_str)
        allGoing=self.cursor.fetchall()
        return allGoing


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
    
   
    def viewHorse(self, horseName):        
        self.rows=self.getHorse(horseName)
        for self.row in self.rows:
            print self.row

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
