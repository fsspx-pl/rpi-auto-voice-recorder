#!/usr/bin/env python3
import pyaudio
import wave
import argparse
import os
from datetime import datetime
from status_update import updateChunkStatus

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Record audio')
    parser.add_argument('output', help='Output filename')
    parser.add_argument('-r', '--rate', help='Sampling rate (default: 44100)', default=44100)
    time_arg_group = parser.add_mutually_exclusive_group(required=True)
    time_arg_group.add_argument('-t', '--time', help='Recording time in seconds')
    time_arg_group.add_argument('--until', help='Date and time when recording should end ("YYYY-MM-DD HH:mm:ss")')
    parser.add_argument('-d', '--device', help='Device index', default=-1)
    args = parser.parse_args()

    # create output directory if needed
    outdir = os.path.dirname(args.output)
    if outdir != '': os.makedirs(outdir, exist_ok=True)

    WAVE_OUTPUT_FILENAME = args.output

    # parse time
    if args.time is not None:
        RECORD_SECONDS = int(args.time)
    elif args.until is not None:
        date = datetime.strptime(args.until, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        RECORD_SECONDS = (date - now).total_seconds()
    else:
        print("missing time argument")
        exit(1)

    DEVICE_INDEX = int(args.device)
    RATE = int(args.rate)
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    CHUNK = 1024

    audio = pyaudio.PyAudio()

    # for x in range(0, audio.get_device_count()):
    #     info = audio.get_device_info_by_index(x)
    #     print("info {0}".format(info))

    if DEVICE_INDEX < 0 or DEVICE_INDEX >= audio.get_device_count():
        DEVICE_INDEX = None # use default
        device_name = "DEFAULT"
    else:
        info = audio.get_device_info_by_index(DEVICE_INDEX)
        device_name = info["name"]

    print('---------------------------------')
    print('Opening stream using device ' + device_name)

    # start Recording
    stream = audio.open(input_device_index=DEVICE_INDEX,
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print('Stream opened')

    num_chunks = int(RATE / CHUNK * RECORD_SECONDS)

    print('---------------------------------')
    print('Recording %d seconds at %d Hz (%d chunks of size %d)' % (RECORD_SECONDS, RATE, num_chunks, CHUNK))

    frames = []
    prev_status_update = None

    for i in range(0, num_chunks):
        data = stream.read(CHUNK)
        print("Recording . . . (chunk %d/%d)" % (i+1, num_chunks), end='\r')
        prev_status_update = updateChunkStatus(i+1, num_chunks, prev_status_update)
        frames.append(data)

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    print("Recording finished")
    print('---------------------------------')

    print("Saving to " + WAVE_OUTPUT_FILENAME)

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(2)
    audio.get_sample_size(FORMAT)
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    print("Saved")