import sqlite3

class SqlStuff:
    def __init__(self):
        """initialise the sql stuff"""
        self.conn=sqlite3.connect('results.db')
    def connectDatabase(self):
        """connect to the results.db database"""
        self.conn=sqlite3.connect('results.db')
    def createResultTable(self):
        """ create a table to hold all of the scraped results"""
        self.conn.execute("CREATE TABLE if not exists RESULTS_INFO( \
            ID INTEGER PRIMARY KEY AUTOINCREMENT, \
            HORSENAME TEXT, \
            HORSEAGE INTEGER, \
            HORSEWEIGHT NONE, \
            POSITION INTEGER, \
            RACELENGTH NONE, \
            NUMBERHORSES INTEGER, \
            JOCKEYNAME TEXT, \
            GOING TEXT, \
            RACEDATE NONE);")
    def addResultStuffToTable(self, ResultStuff):
        for idx, self.horseName in enumerate(ResultStuff.horseNames):
            """create a string with this horses values"""
            self.val_str="'{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}'".format(\
                ResultStuff.horseNames[idx].replace("'", "''"),\
                ResultStuff.horseAges[idx], ResultStuff.horseWeights[idx], idx+1, \
                ResultStuff.raceLength, ResultStuff.numberOfHorses, ResultStuff.jockeys[idx].replace("'", "''"), \
                ResultStuff.going, ResultStuff.raceDate) 
            #print self.val_str
            """create a string for the sql command"""
            self.sql_str="INSERT INTO RESULTS_INFO \
                (HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE) \
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
        print self.rows

    def delDate(self, date):
        self.sql_str="DELETE from RESULTS_INFO where RACEDATE='{}'".format(date)
        self.conn.execute(self.sql_str)
        self.conn.commit()
        

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
       
    def viewHorse(self, horseName):        
        self.rows=self.getHorse(horseName)
        for self.row in self.rows:
            print self.row

    def viewJockey(self, jockeyName):
        self.rows=self.getJockey(jockeyName)
        for self.row in self.rows:
            print self.row
