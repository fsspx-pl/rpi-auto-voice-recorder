#!/usr/bin/env python3

from common import *
from datetime import datetime
from get_next_recording_time import getNextRecordingTime
import time
import os

def recordNext():
    next = getNextRecordingTime()
    if next is None:
        print("Nothing to record today")
        exit(1)

    begin = next[0]
    end = next[1]

    now = datetime.now()
    if now < begin:
        print("Waiting till", begin)
        s = (begin - now).total_seconds()
        time.sleep(s)

    now = datetime.now()
    filename = "recordings/%s.wav" % (now.strftime(FILE_DATE_FORMAT))

    print("Record until", end)
    os.system("./record.py --until \"%s\" \"%s\"" % (end.strftime(DATE_FORMAT), filename))

if __name__ == "__main__":
    recordNext()