#!/usr/bin/env python3

import json
from datetime import datetime

def setHourAndMinute(d,h_m):
    h,m = h_m.split(':')
    return d.replace(hour=int(h), minute=int(m), second=0, microsecond=0)

if __name__ == "__main__":
    mass_times = json.load(open('mass_times.json'))

    now = datetime.now()
    now.hour
    now.minute

    for mt in mass_times:
        b = setHourAndMinute(datetime.now(), mt['begin'])
        e = setHourAndMinute(datetime.now(), mt['end'])
        if now < e:
            print(b)
            print(e)
            exit(0)

    print("no more today")
    exit(1)