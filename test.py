import tkinter as tk
import commands

databases = ["results_2012.db", "results_2013.db", "results_2014.db",
             "results_2015.db", "results_2016.db", "results_2017.db", 
             "results_2018.db", "results_2019.db",]
def get_date_info():
    """ get the info about the date from the db and 
    display it in the db text box"""
    dateLookup = ent_dateInfo.get()
    dateInfos = commands.viewDate(dateLookup, databases)
    for dateInfo in dateInfos:
        txt_dateInfo.insert(0.0, str(dateInfo) + "\n")        

def get_info():
    """ this function will get the horse name from the 
    entry box and then display the results from the 
    lookup function to a text box"""
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
    txt_info.delete("1.0", tk.END) 
    headerStr = "ID,  HORSENAME, HORSEAGE, HORSEWEIGHT, POSITION, RACELENGTH, NUMBERHORSES, JOCKEYNAME, GOING, RACEDATE, ODDS"
    horses = commands.viewMultiple(databases, horseName=horseName, horseAge=horseAge, horseWeight=horseWeight, position=position, raceLength=raceLength, numberHorses=numberHorses, jockeyName=jockeyName, going=going, raceDate=raceDate, raceTime=raceTime, raceVenue=raceVenue, draw=draw, trainerName=trainerName)
    for horse in horses:
        txt_info.insert(0.0, str(horse) + "\n")
    txt_info.insert(0.0, headerStr + "\n")


def clear_info():
    """ clear the text box displaying the searched for horse"""
    txt_info.delete("1.0", tk.END) 

def save_info():
    """ save the data in the text box to a file with the same
    name as the search horseName"""
    horseName = ent_horseName.get()
    with open(horseName+".csv", "w") as output_file:
        text = txt_info.get("1.0", tk.END)
        output_file.write(text)

window = tk.Tk()

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
txt_frm.rowconfigure(0, weight=1, minsize=50) 
txt_frm.columnconfigure(0, weight=1, minsize=75) 

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

txt_info = tk.Text(master=txt_frm)
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
txt_info.grid(row=0, column=0, sticky="nsew")

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
db_frm.grid(row=0, column=1, sticky="nsew")
window.mainloop()
