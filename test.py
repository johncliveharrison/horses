import tkinter as tk
import commands
import plot
import training
from collections import defaultdict
import sys

databases = ["results_2012.db", "results_2013.db", "results_2014.db",
             "results_2015.db", "results_2016.db", "results_2017.db", 
             "results_2018_2.db", "results_2019_2.db", "results_2020_2.db",
             "results_2021.db"]

myDict_net = {}


def on_scrollbar(*args):
    '''Scrolls both text widgets when the scrollbar is moved'''
    for txt_info_col in txt_info:
        txt_info_col.yview(*args)

def on_textscroll(*args):
    '''Moves the scrollbar and scrolls text widgets when the mousewheel
    is moved on a text widget'''
    scrollbar.set(*args)
    on_scrollbar('moveto', args[0])


def get_date_info():
    """ get the info about the date from the db and 
    display it in the db text box"""
    dateLookup = ent_dateInfo.get()
    dateInfos = commands.viewDate(dateLookup, databases)
    for dateInfo in dateInfos:
        txt_dateInfo.insert(0.0, str(dateInfo) + "\n")        

def train_info():
    global myDict_net
    myDict_net = training.train_net(databases)
    net_name = ""
    for ii, (key, value) in enumerate(myDict_net.items()):
        if ii != 0:
            net_name = net_name + " and "
        net_name = net_name + key
    net_name_variable.set(net_name)

def today_info():
    # clear the display
    for txt_info_col in txt_info:
        txt_info_col.delete("1.0", tk.END) 

    global myDict_net
    horses = training.runToday(databases, myDict_net)
    for ii, horse in enumerate(horses):
        for jj, header in enumerate(headerList):
            txt_info[jj].insert(0.0, str(horse[jj+1]) + "\n")


def get_info():
    """ this function will get the horse name from the 
    entry box and then display the results from the 
    lookup function to a text box"""
    #training.get_length_conversion()
    #return
    #training.get_going_conversion()
    #return

    horseName = ent_horseName.get()
    horseAge = ent_horseAge.get()
    horseWeight = ent_horseWeight.get()
    position = ent_position.get()
    raceLength = ent_raceLength.get()
    numberHorses = ent_numberHorses.get()
    jockeyName = ent_jockeyName.get()
    going = ent_going.get()
    raceDate = ent_raceDate.get()
    raceTime = ent_raceTime.get()
    raceVenue = ent_raceVenue.get()
    draw = ent_draw.get()
    trainerName = ent_trainerName.get()
    print(raceDate)
    print(horseName)
    for txt_info_col in txt_info:
        txt_info_col.delete("1.0", tk.END) 

    horses = commands.viewMultiple(databases, horseName=horseName, horseAge=horseAge, horseWeight=horseWeight, position=position, raceLength=raceLength, numberHorses=numberHorses, jockeyName=jockeyName, going=going, raceDate=raceDate, raceTime=raceTime, raceVenue=raceVenue, draw=draw, trainerName=trainerName)
    for ii, horse in enumerate(horses):
        for jj, header in enumerate(headerList):
            txt_info[jj].insert(0.0, str(horse[jj+1]) + "\n")

    if horseName:
        rows = commands.viewMultiple(databases,horseName=horseName)
        plot.days_since_last_race_plot(rows)
        #plot.horse_date_plot(rows)
        plot.race_length_plot(rows)
        plot.odds_plot(rows, databases)

    if raceVenue and raceTime and raceDate:
        horseName_rows = []
        rows = commands.viewMultiple(databases,raceVenue=raceVenue, raceTime=raceTime, raceDate=raceDate)
        #for row in rows:
        #    horseName_row = commands.viewMultiple(databases,horseName=str(row[1]))
        #    horseName_rows.append(horseName_row)
        #plot.race_plot(horseName_rows)
        global myDict_net
        training.runTestDates(databases, "2021-01-01", "2021-01-15", myDict_net)
        #result, result_horses = training.get_predicted_result(rows, databases, net)
        #print (result)
        #print (result_horses)

def clear_info():
    """ clear the text box displaying the searched for horse"""
    for txt_info_col in text_info:
        txt_info_col.delete("1.0", tk.END) 


def save_info():
    """ save the data in the text box to a file with the same
    name as the search horseName"""
    horseName = ent_horseName.get()
    with open(horseName+".csv", "w") as output_file:
        text = txt_info.get("1.0", tk.END)
        output_file.write(text)

window = tk.Tk()
net_name_variable = tk.StringVar()
net_name_variable.set("net not trained")

window.columnconfigure(0, weight=1, minsize=75)
window.rowconfigure(0, weight=1, minsize=50)
window.columnconfigure(1, weight=1, minsize=75)
window.rowconfigure(1, weight=1, minsize=50)

frm = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=5)
txt_frm = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=5)
db_frm = tk.Frame(master=window, relief=tk.SUNKEN, borderwidth=5)

# widgets for the horseinfo frame (frm)
#frm.rowconfigure(2, weight=1, minsize=50) 
#frm.columnconfigure(0, weight=1, minsize=75) 

lbl_horseName = tk.Label(master=frm, 
                        text="Horse Name")
ent_horseName = tk.Entry(master=frm)

lbl_horseAge = tk.Label(master=frm, 
                        text="Horse Age")
ent_horseAge = tk.Entry(master=frm)

lbl_horseWeight = tk.Label(master=frm, 
                        text="Horse Weight")
ent_horseWeight = tk.Entry(master=frm)

lbl_position = tk.Label(master=frm, 
                        text="Position")
ent_position = tk.Entry(master=frm)

lbl_raceLength = tk.Label(master=frm, 
                        text="Race Length")
ent_raceLength = tk.Entry(master=frm)

lbl_numberHorses = tk.Label(master=frm, 
                        text="Number Horses")
ent_numberHorses = tk.Entry(master=frm)

lbl_jockeyName = tk.Label(master=frm, 
                        text="Jockey Name")
ent_jockeyName = tk.Entry(master=frm)

lbl_going = tk.Label(master=frm, 
                        text="Going")
ent_going = tk.Entry(master=frm)

lbl_raceDate = tk.Label(master=frm, 
                        text="Race Date")
ent_raceDate = tk.Entry(master=frm)

lbl_raceTime = tk.Label(master=frm, 
                        text="Race Time")
ent_raceTime = tk.Entry(master=frm)

lbl_raceVenue = tk.Label(master=frm, 
                        text="Race Venue")
ent_raceVenue = tk.Entry(master=frm)

lbl_draw = tk.Label(master=frm, 
                        text="Draw")
ent_draw = tk.Entry(master=frm)

lbl_trainerName = tk.Label(master=frm, 
                        text="Trainer Name")
ent_trainerName = tk.Entry(master=frm)


btn_info = tk.Button(master=frm,
                          text="go",
                          command=get_info)

btn_clear = tk.Button(master=frm,
                      text="clear",
                      command=clear_info)

btn_save = tk.Button(master=frm,
                      text="save",
                      command=save_info)

lbl_netName = tk.Label(master=frm, 
                       textvariable=net_name_variable)

btn_net = tk.Button(master=frm,
                    text="train",
                    command=train_info)

btn_today = tk.Button(master=frm,
                      text="today",
                      command=today_info)


headerList = ["HORSENAME", "HORSEAGE", "HORSEWEIGHT", "POSITION", "RACELENGTH", "NUMBERHORSES", "JOCKEYNAME", "GOING", "RACEDATE", "RACETIME", "RACEVENUE", "DRAW", "TRAINER", "FINISHTIME", "ODDS"]
txt_frm.rowconfigure(0, weight=1, minsize=50) 

lbl_header = []
txt_info = []
for ii, header in enumerate(headerList):
    lbl_header.append(tk.Label(master=txt_frm, 
                               text=header))
    lbl_header[ii].grid(row=0, column=ii, sticky="nsew")
    txt_info.append(tk.Text(master=txt_frm))
    txt_info[ii].grid(row=1, column=ii, sticky="nsew")
    if ii==1:
        txt_frm.columnconfigure(ii, weight=1, minsize=8) 
    else:
        txt_frm.columnconfigure(ii, weight=1, minsize=15) 
    # Changing the settings to make the scrolling work
    txt_info[ii]['yscrollcommand'] = on_textscroll

scrollbar = tk.Scrollbar(master=txt_frm)
scrollbar.grid(row=1, column = len(headerList), sticky="nsew")

# Changing the settings to make the scrolling work
scrollbar['command'] = on_scrollbar


lbl_horseName.grid(row=0, column=0)
ent_horseName.grid(row=1, column=0)

lbl_horseAge.grid(row=0, column=1)
ent_horseAge.grid(row=1, column=1)

lbl_horseWeight.grid(row=0, column=2)
ent_horseWeight.grid(row=1, column=2)

lbl_position.grid(row=0, column=3)
ent_position.grid(row=1, column=3)

lbl_raceLength.grid(row=0, column=4)
ent_raceLength.grid(row=1, column=4)

lbl_numberHorses.grid(row=0, column=5)
ent_numberHorses.grid(row=1, column=5)

lbl_jockeyName.grid(row=0, column=6)
ent_jockeyName.grid(row=1, column=6)

lbl_going.grid(row=2, column=0)
ent_going.grid(row=3, column=0)

lbl_raceDate.grid(row=2, column=1)
ent_raceDate.grid(row=3, column=1)

lbl_raceTime.grid(row=2, column=2)
ent_raceTime.grid(row=3, column=2)

lbl_raceVenue.grid(row=2, column=3)
ent_raceVenue.grid(row=3, column=3)

lbl_draw.grid(row=2, column=4)
ent_draw.grid(row=3, column=4)

lbl_trainerName.grid(row=2, column=5)
ent_trainerName.grid(row=3, column=5)


btn_info.grid(row=2, column=6)
btn_clear.grid(row=3, column=6)
btn_save.grid(row=5, column=1)

lbl_netName.grid(row=1, column=10)
btn_net.grid(row=0, column=10)
btn_today.grid(row=3, column=10)

# widgets for the database frame (db_frm)
db_frm.rowconfigure(2, weight=1, minsize=50) 
db_frm.columnconfigure(0, weight=1, minsize=75) 

newestDate = commands.viewNewestDate(databases, False)
lbl_newestDate1 = tk.Label(master=db_frm,
                           text="Newest Date")
lbl_newestDate2 = tk.Label(master=db_frm,
                           text=newestDate)
lbl_newestDate1.grid(row=0, column=0)
lbl_newestDate2.grid(row=0, column=1)


# position the frames
frm.grid(row=0, column=0, sticky="nsew")
txt_frm.grid(row=1, column=0, sticky="nsew")
db_frm.grid(row=2, column=0, sticky="nsew")
window.mainloop()
