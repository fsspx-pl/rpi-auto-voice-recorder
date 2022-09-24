#!/usr/bin/env python3

import json
from datetime import datetime

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setHourAndMinute(d,h_m):
    h,m = h_m.split(':')
    return d.replace(hour=int(h), minute=int(m), second=0, microsecond=0)

if __name__ == "__main__":
    recording_times = json.load(open('recording_times.json'))

    now = datetime.now()
    now.hour
    now.minute

    for t in recording_times:
        b = setHourAndMinute(datetime.now(), t['begin'])
        e = setHourAndMinute(datetime.now(), t['end'])
        if now < e:
            print(b.strftime(DATE_FORMAT))
            print(e.strftime(DATE_FORMAT))
            exit(0)

    print("no more today")
    exit(1)