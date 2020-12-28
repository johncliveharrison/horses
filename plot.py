import pandas as pd
import matplotlib.pyplot as plt
import datetime
import minmax
import commands

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def horse_date_plot(rows):
    date_time_list = []
    position = []
    legend_list = []
    for row in rows:
        date_time_list.append(str(row[9]))
        date_time = pd.to_datetime(date_time_list)
        position.append((float(row[4])/float(row[6])))
    
    DF = pd.DataFrame()
    DF['position'] = position
    DF = DF.set_index(date_time)
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.xlabel("date")
    plt.ylabel("position")
    plt.plot(DF)
    legend_list.append(str(rows[0][1]))
    plt.legend(legend_list, loc='upper left')

    plt.show(block=False)

def odds_plot(rows, databases):
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.xlabel("date")
    plt.ylabel("odds")

    date_time_list = []
    position = []
    normalized_odds_list = []
    legend_list = []
    for ii, row in enumerate(rows):
        date_time_list.append(str(row[9]))
        position.append((float(row[4])/float(row[6])))
        """ for each row need to get the race info and then
        get a list of the odds and find the min max for normalizing"""
        raceVenue = row[11]
        raceTime = row[10]
        raceDate = row[9]
        race_rows = commands.viewMultiple(databases,raceVenue=raceVenue, raceTime=raceTime, raceDate=raceDate)
        race_odds_list = []
        for race_row in race_rows:
            print (race_row[15])
            race_odds_split = race_row[15].split("/")
            try:
                race_odds = float(race_odds_split[0])/float(race_odds_split[1])
            except ValueError as e:
                print (race_row[15])
                print (race_odds_split)
                print (e)
            race_odds_list.append(race_odds)
        max_odds = max(race_odds_list)
        min_odds = min(race_odds_list)
        odds_range = max_odds - min_odds

        odds_split = row[15].split("/")
        odds = float(odds_split[0])/float(odds_split[1])
        normalized_odds = float(odds - min_odds)/float(odds_range)
        normalized_odds_list.append(float(normalized_odds)) 

    date_time = pd.to_datetime(date_time_list)
    DF = pd.DataFrame()
    DF['odds'] = normalized_odds_list
    DF = DF.set_index(date_time)
    plt.plot(DF)

    DF = pd.DataFrame()
    DF['position'] = position
    DF = DF.set_index(date_time)
    plt.plot(DF)

    legend_list.append(str(rows[0][1]))
    plt.legend(legend_list, loc='upper left')
    plt.show(block=False)



def race_length_plot(rows):
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.xlabel("date")
    plt.ylabel("race length")

    date_time_list = []
    position = []
    length_list = []
    normalized_length_list = []
    legend_list = []
    for ii, row in enumerate(rows):
        date_time_list.append(str(row[9]))
        position.append((float(row[4])/float(row[6])))
        length = minmax.convertRaceLengthMetres(row[5])
        length_list.append(length)
    max_length = max(length_list)
    min_length = min(length_list)
    length_range = max_length - min_length
    for length_entry in length_list:
        normalized_length = float(length_entry - min_length)/float(length_range)
        normalized_length_list.append(float(normalized_length)) 

    date_time = pd.to_datetime(date_time_list)
    DF = pd.DataFrame()
    DF['length'] = normalized_length_list
    DF = DF.set_index(date_time)
    plt.plot(DF)

    DF = pd.DataFrame()
    DF['position'] = position
    DF = DF.set_index(date_time)
    plt.plot(DF)

    legend_list.append(str(rows[0][1]))
    plt.legend(legend_list, loc='upper left')
    plt.show(block=False)



def days_since_last_race_plot(rows):

    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.xlabel("date")
    plt.ylabel("days")

    date_time_list = []
    position = []
    days_list = []
    legend_list = []
    for ii, row in enumerate(rows):
        date_time_list.append(str(row[9]))
        if ii == 0:
            dateStartSplit=rows[ii][9].split('-')
            dateEndSplit=rows[ii][9].split('-')
        else:
            dateStartSplit=rows[ii][9].split('-')
            dateEndSplit=rows[ii-1][9].split('-')
   
        dateStart=datetime.date(int(dateStartSplit[0]),int(dateStartSplit[1]),int(dateStartSplit[2]))
        dateEnd=datetime.date(int(dateEndSplit[0]),int(dateEndSplit[1]),int(dateEndSplit[2]))
        days = dateStart - dateEnd
        days_list.append(days.days)
    print(days_list[1:-1])
    days_list_max = max(days_list[1:-1])
    days_list_min = min(days_list[1:-1])
    days_list_range = days_list_max - days_list_min
    days_list_normalized = []
    days_list_normalized.append(float(0.5))
    for ii, day in enumerate(days_list):
        if ii>0:
            days_list_normalized.append(1.0-float(day - days_list_min)/float(days_list_range))

    date_time = pd.to_datetime(date_time_list)
    DF = pd.DataFrame()
    DF['days'] = days_list_normalized
    DF = DF.set_index(date_time)
    plt.plot(DF)

    for row in rows:
        position.append((float(row[4])/float(row[6])))

    DF = pd.DataFrame()
    DF['position'] = position
    DF = DF.set_index(date_time)
    plt.plot(DF)

    legend_list.append(str(rows[0][1]))
    plt.legend(legend_list, loc='upper left')
    plt.show(block=False)


def race_plot(horseName_rows):
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.3)
    plt.xticks(rotation=90)
    plt.xlabel("date")
    plt.ylabel("position")
    legend_list = []

    for ii, rows in enumerate(horseName_rows):
        date_time_list = []
        position = []
        for row in rows:
            date_time_list.append(str(row[9]))
            date_time = pd.to_datetime(date_time_list)
            position.append((float(row[4])/float(row[6])))
    
        DF = pd.DataFrame()
        DF['position'] = position
        DF = DF.set_index(date_time)
        plt.plot(DF)
        legend_list.append(str(rows[0][1]))
    #legend_list.reverse()
    plt.legend(legend_list, loc='upper left')
    plt.show(block=False)
