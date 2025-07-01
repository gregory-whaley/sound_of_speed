#/usr/bin/env bash

#  generate daily plot files.  assume run just after midnight
#  database file and all python files assumed to be located in capture directory

# generate scatterplot from yesterday's data
/home/greg/Documents/sos_master/.sos_venv/bin/python3  /home/greg/Documents/sos_master/sos_capture/daily_scatterplot.py 1
#
# generate heat map
/home/greg/Documents/sos_master/.sos_venv/bin/python3  /home/greg/Documents/sos_master/sos_capture/histograms_by_day.py
#
# generate bar chart of daily stats
/home/greg/Documents/sos_master/.sos_venv/bin/python3  /home/greg/Documents/sos_master/sos_capture/totals_by_day.py

