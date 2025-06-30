#!/usr/bin/python3

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import sqlite3
from datetime import datetime
from datetime import timedelta
import sys




def scatter_hist(x, y, ax, ax_histx, ax_histy):
    # no labels
    ax_histx.tick_params(axis="x", labelbottom=False)
    ax_histy.tick_params(axis="y", labelleft=False)

    # the scatter plot:
    ax.scatter(x, y,marker='o',s=(72./fig.dpi)**2)  # set circle marker with specified area size
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Speed (MPH)')
    ax.grid(True)
    ax.set_xlim(0,24)
    ax.set_ylim(0,60)
    

    # now determine nice limits by hand:
    binwidth = 1.0
    xmax = np.max(np.abs(x))
    lim = (int(xmax/binwidth) + 1) * binwidth
    bins = np.arange(-lim, lim + binwidth, binwidth)
    ax_histx.hist(x, bins=bins)
    ax_histx.grid(True)
    ax_histx.set_title('Daily Speed Scatterplot')
    ax_histx.set_ylabel('Cars/Hour')
    

    binwidth = 1.0
    ymax = np.max(np.abs(y))
    lim = (int(ymax/binwidth) + 1) * binwidth
    bins = np.arange(-lim, lim + binwidth, binwidth)
    ax_histy.hist(y, bins=bins, orientation='horizontal')
    ax_histy.grid(True)

num_days = 0   # pick today by default
if len(sys.argv) == 2:
    num_days = int(sys.argv[1])


today = datetime.now().date()
plot_date = today - timedelta(num_days)
date_str = plot_date.strftime("%Y-%m-%d")

db_filename = 'speed.db'
con = sqlite3.connect(db_filename)
db_cursor = con.cursor()
# generate sql query using select * from speed where date like '%-01-09%';
select = "SELECT date, speed FROM speed WHERE date LIKE '%" + date_str + "%'"
result = db_cursor.execute(select)
midnight = datetime.fromisoformat(date_str)  # as datetime object
hours = []  # empty list
speeds = []
for date_res,speed_res in result:
    hours.append((datetime.fromisoformat(date_res) - midnight).total_seconds()/3600)
    speeds.append(abs(speed_res))
con.close()

x = np.array(hours)
y = np.array(speeds)
if (len(x) == 0) or (len(y) == 0):
    sys.exit("Error...No data to plot.")

# Create a Figure, which doesn't have to be square.
fig = plt.figure(figsize=(10,6))

# Create the main Axes, leaving 25% of the figure space at the top and on the
# right to position marginals.
gs = GridSpec(1,1, figure=fig, top=0.75, right = 0.75)

ax = fig.add_subplot(gs[0,0])

# Create marginal Axes, which have 25% of the size of the main Axes.  Note that
# the inset Axes are positioned *outside* (on the right and the top) of the
# main Axes, by specifying axes coordinates greater than 1.  Axes coordinates
# less than 0 would likewise specify positions on the left and the bottom of
# the main Axes.
ax_histx = ax.inset_axes([0, 1.05, 1, 0.25], sharex=ax)
ax_histy = ax.inset_axes([1.05, 0, 0.25, 1], sharey=ax)

# Draw the scatter plot and marginals.
scatter_hist(x, y, ax, ax_histx, ax_histy)
ax.annotate('Date: '+date_str,xy=(1.05,1.2),xycoords='axes fraction',annotation_clip=False)

#plt.show()
fig.savefig('daily_scatterplot.png',dpi=100)   
