#!/usr/bin/python3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import sqlite3
from datetime import datetime
from datetime import timedelta


db_filename = 'speed.db'

today = datetime.now().date()
num_days = 300
num_speed_bins = 100
lowest_speed = 15
highest_speed = 60

con = sqlite3.connect(db_filename)
con.row_factory = sqlite3.Row
db_cursor = con.cursor()

date_list = []  # empty list
speed_counts = []
speed_list = []

start_date = today - timedelta(num_days)


while (start_date <= today):
    date_str = start_date.strftime("%Y-%m-%d")
    select = "SELECT speed FROM speed WHERE date LIKE '%" + date_str + "%'"
    result = db_cursor.execute(select)
    speed_list = np.abs(result.fetchall())   # consider positive values only
    speed_counts.append(np.histogram(speed_list,bins=num_speed_bins,range=(lowest_speed,highest_speed))[0])  # save counts only
    date_list.append(start_date)  
    start_date += timedelta(1)

con.close()

fig,ax = plt.subplots(figsize=(10,6))
y_scale = np.linspace(lowest_speed,highest_speed,num_speed_bins)
x_scale = np.arange(num_days+1)
#ax.pcolormesh(x_scale,y_scale,  np.transpose(speed_counts))
ax.pcolormesh(date_list,y_scale,  np.transpose(speed_counts))
ax.set_xlabel('Date',fontsize=14)
ax.set_ylabel('Speed (MPH)',fontsize=14)
ax.set_title('Traffic Distribution vs Date',fontsize=18)
ax.grid(True)


fig.savefig('histograms_by_day.png',dpi=100)
#plt.show()

