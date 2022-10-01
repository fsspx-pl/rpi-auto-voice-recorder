#!/usr/bin/env python3

import argparse
import os
import time
from datetime import datetime

from common import *
from get_next_recording_time import getNextRecordingTimeFrom


def recordNext(input, device):
    next = getNextRecordingTimeFrom(input)
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
    os.system("./record.py -d %s --until \"%s\" \"%s\"" %
              (device, end.strftime(DATE_FORMAT), filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Record audio based on the defined time')
    parser.add_argument('-i', '--input', help='Input JSON file', required=True)
    parser.add_argument('-c', '--consecutive',
                        help='Amount of consecutive entry times from input file, that audio recording will start on.', default=1)
    parser.add_argument('-d', '--device', help='Device index', default=-1)
    args = parser.parse_args()

    input_filename = args.input
    device = args.device
    ENTRIES = int(args.consecutive)

    print("Recording {0} entries defined in {1} ...".format(
        ENTRIES, input_filename))
    for x in range(ENTRIES):
        recordNext(input_filename, device)
