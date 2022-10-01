#!/usr/bin/env python3

import argparse
import json
from datetime import datetime

from common import *


def setTime(d, h_m):
    hour, minute, *rest = h_m.split(':')
    second, *_ = rest or [0]
    return d.replace(hour=int(hour), minute=int(minute), second=int(second), microsecond=0)


def getNextRecordingTimeFrom(filepath):
    recording_times = json.load(open(filepath))

    now = datetime.now()
    now.hour
    now.minute

    for t in recording_times:
        b = setTime(datetime.now(), t['begin'])
        e = setTime(datetime.now(), t['end'])
        if now < e:
            return (b, e)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Record audio based on the defined time')
    parser.add_argument('-i', '--input', help='Input recording times as JSON')
    args = parser.parse_args()

    input_filename = args.input

    if input_filename is None:
        print("")
        exit(1)

    t = getNextRecordingTimeFrom(input_filename)

    if t is None:
        print("no more today")
        exit(1)

    print(t[0].strftime(DATE_FORMAT))
    print(t[1].strftime(DATE_FORMAT))
