#!/usr/bin/python3
 
from datetime import datetime, timedelta
import requests
import time
import sched
import os
import atexit
import signal
import sys

# names of the HTTP request to switch on the triggers
_BASEURL = "https://maker.ifttt.com/trigger/{0}/with/key/{1}"

# read key for HTTP request from file 
with open("/home/pi/irrigazione/IFTTT_KEY", "r") as fkey:
    _KEY = fkey.read().strip()

# name of the log file to store information on the triggers 
_LOGFILE = "/home/pi/irrigazione/irrigazione.log"

# define function to print time and message to log file
def printLogMessage(msg):
    with open(_LOGFILE, "a") as flog:
        dtstring = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        flog.write("{0} : {1}\n".format(dtstring, msg))

# backup old log files
def backupOldLogs():
    if os.path.exists(_LOGFILE):
        for n in range(1000):
            # the file will be saved to a format like irrigazione.log_1
            targetfile = _LOGFILE + "_{}".format(n)
            if not os.path.exists(targetfile):  # when the file does not exist,
                # save with this name and break loop
                os.rename(_LOGFILE, targetfile)  
                break

# trigger event
def triggerEvent(triggerName):
    # write message to log file
    logmessage = "Switching trigger {0}".format(triggerName)
    printLogMessage(logmessage)
    # switch on trigger
    triggerURL = _BASEURL.format(triggerName, _KEY)
    requests.get(url = triggerURL)

# schedule a trigger event at a given time
def scheduleTriggerToday(s, triggerName, dt):
    # compute the number of seconds till the event
    now = datetime.today()
    waitseconds = (dt - now).total_seconds()
    # now schedule the event, only if seconds are positive (event in the future)
    if waitseconds > 0.:
        printLogMessage("Scheduling event '{}' in {} seconds".format(triggerName, int(waitseconds)))
        s.enter(waitseconds, 1, triggerEvent, kwargs={'triggerName': triggerName})
    
# schedule a waiting time till a certain time tomorrow at a given time
def scheduleWaitingTomorrow(s, hourmin):
    # compute the number of seconds till the event
    now = datetime.today()
    eventtime = now.replace(day=now.day, hour=hourmin[0], minute=hourmin[1],
                            second=0, microsecond=0) + timedelta(days=1)
    waitseconds = (eventtime - now).total_seconds()
    # now schedule the event
    s.enter(waitseconds, 1, printLogMessage,
            kwargs={'msg': "reached scheduling time"})


# read the list of events from a configuration file
def readConfiguration(f):

    # now time is needed to construct the proper datetime elements
    now = datetime.today()
    # initialize dictionary to store the events
    events = {}

    # loop over the lines of the configuration file
    for line in f:

        # split line with commas
        s = line.split(",")

        # the first two elements are the names of the starting and ending triggers
        triggerstart = s[0].strip()
        triggerend = s[1].strip()

        # then there is the starting time
        timestart = now.replace(day=now.day, hour=int(s[2].split(":")[0]), 
                minute=int(s[2].split(":")[1]), second=0, microsecond=0) 
        # and the duration of the event
        timeend = timestart + timedelta(minutes=int(s[3]))

        # now store the starting and ending events in the dictonary
        events[timestart] = triggerstart
        events[timeend] = triggerend

    # return dictionary
    return events

# ===============================================================================

def main():
    
    # first thing: backup old log files
    backupOldLogs()
    # now we can print an initial message 
    printLogMessage("Starting irrigazione.py")
    
    def closingMsg(): printLogMessage("Closing irrigazione.py")
    def stopIrrigazione(*args): sys.exit(0)
    atexit.register(closingMsg)
    signal.signal(signal.SIGTERM, stopIrrigazione)
    signal.signal(signal.SIGINT, stopIrrigazione)

    # =========================================================================
    
    # now, infinite loop with:
    # 1) at 1.00 at night, prepare the scheduling for the day
    # 2) run scheduling, till the 1.00 of the next day

    # when the service is started, the first scheduling can happen
    # anytime in the day, for this reason only events which are
    # supposed to happen in the future will be actually scheduled
    
    while True:
        
        printLogMessage("scheduling events for today")

        # read list of events from configuration file
        with open("/home/pi/irrigazione/triggers.dat") as fconfig:
            todayevents = readConfiguration(fconfig)
        print(todayevents)

        # initialize the schedule
        s = sched.scheduler()
        # schedule events stored in the dictionary
        for tm, evnt in todayevents.items():
           scheduleTriggerToday(s, evnt, tm)
        # schedule waiting till next scheduling time
        scheduleWaitingTomorrow(s, (1, 0))
        # now execute the scheduler
        s.run()
    
   
if __name__ == "__main__":  
    main()
