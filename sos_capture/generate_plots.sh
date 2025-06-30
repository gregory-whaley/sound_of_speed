#/usr/bin/env bash

#  generate daily plot files.  assume run just after midnight
#  database file and all python files assumed to be located in capture directory

# generate scatterplot from yesterday's data
dummy_directory/.sos_venv/bin/python3  dummy_directory/sos_capture/daily_scatterplot.py 1
#
# generate heat map
dummy_directory/.sos_venv/bin/python3  dummy_directory/sos_capture/histograms_by_day.py
#
# generate bar chart of daily stats
dummy_directory/.sos_venv/bin/python3  dummy_directory/sos_capture/totals_by_day.py

