#!/usr/bin/python3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import sqlite3
from datetime import datetime
from datetime import timedelta


db_filename = 'speed.db'

today = datetime.now().date()


con = sqlite3.connect(db_filename)
db_cursor = con.cursor()

date_list = []  # empty list
speed_counts = []
speed_list = []

start_date = today - timedelta(180)

while (start_date <= today):
    date_str = start_date.strftime("%Y-%m-%d")
    select = "SELECT COUNT(date),AVG(speed) FROM speed WHERE date LIKE '%" + date_str + "%' AND speed > 0"
    result = db_cursor.execute(select)
    count,avg_speed = result.fetchone()    # return a tuple as a row
    speed_counts.append(count)
    speed_list.append(avg_speed)
    date_list.append(start_date)  
    
    start_date += timedelta(1)

con.close()



fig,ax1 = plt.subplots(figsize=(10,6))
ax1.bar(date_list,speed_counts,color='lightgrey',label='Daily Count')
ax1.set_xlabel('Date',fontsize=14)
ax1.set_ylabel('Volume (Cars/Day)',fontsize=14)
ax1.set_title('Traffic Volume and Average Speed',fontsize=18)


ax2 = ax1.twinx()     # generate 2nd plot with same x-axis
ax2.plot(date_list,speed_list,color='firebrick',label='Ave. Speed')
ax2.grid(True)
ax2.set_ylabel('Average Speed (MPH)',fontsize=14)

fig.legend(loc='best')

fig.savefig('totals_by_day.png',dpi=100)
#plt.show()

