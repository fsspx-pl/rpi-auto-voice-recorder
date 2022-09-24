#!/usr/bin/env python3

from common import *
import json
from datetime import datetime


def setHourAndMinute(d,h_m):
    h,m = h_m.split(':')
    return d.replace(hour=int(h), minute=int(m), second=0, microsecond=0)

def getNextRecordingTime():
    recording_times = json.load(open('recording_times.json'))

    now = datetime.now()
    now.hour
    now.minute

    for t in recording_times:
        b = setHourAndMinute(datetime.now(), t['begin'])
        e = setHourAndMinute(datetime.now(), t['end'])
        if now < e:
            return (b,e)
    return None

if __name__ == "__main__":
    t = getNextRecordingTime()
    if t is None:
        print("no more today")
        exit(1)

    print(t[0].strftime(DATE_FORMAT))
    print(t[1].strftime(DATE_FORMAT))