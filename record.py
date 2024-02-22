#!/usr/bin/env python3

import torch
torch.set_num_threads(1)
import numpy as np
import pyaudio
import os
from ffmpeg import FFmpeg
import argparse
import threading
import queue
import wave
import datetime
from datetime import datetime
from torchaudio import functional
from helpers import create_folder_if_not_exists, convert_to_m4a, int2float
from upload import upload as upload_file
from log import log_message
from collections import deque

model, utils = torch.hub.load(repo_or_dir='vendor/silero-vad-master',
                              source='local',
                              model='silero_vad',
                              onnx=True)

(get_speech_timestamps,
 _, read_audio,
 VadIterator, _) = utils


# ## Pyaudio Set-up
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
VAD_TARGET_SAMPLE_RATE = 16000
NUM_SAMPLES = 1536
CHUNK = int(SAMPLE_RATE / 20)

audio = pyaudio.PyAudio()

def save_audio(data_queue, logging_queue, sample_rate, upload, folder_name='output'):
    while True:
        audio_data, filename = data_queue.get()
        create_folder_if_not_exists(folder_name)
        pathname = folder_name + '/' + filename
        wf = wave.open(pathname, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(audio_data))
        wf.close()
        output_file = convert_to_m4a(pathname)
        duration = len(audio_data) / sample_rate * 1000
        logging_queue.put("Saved detected speech of {} seconds to a file {}".format(round(duration, 2), output_file))
        if(upload):
            upload_file(output_file, os.path.basename(output_file), logging_queue)
        os.remove(pathname)
        data_queue.task_done()

def start_recording(device_index, min_silence_duration_ms=7000, upload=False, padding_ms=1000):
    vad_iterator = VadIterator(model, min_silence_duration_ms=min_silence_duration_ms, threshold=0.9)
    stream = open_stream(device_index)

    audio_data = []
    collect_samples = False
    padding_s = padding_ms/1000
    padding_chunks = int(SAMPLE_RATE * padding_s / CHUNK)
    padding_buffer = deque(maxlen=padding_chunks)
    
    logging_queue = queue.Queue()
    logging_listener = threading.Thread(target=log_message, args=(logging_queue,))
    logging_listener.start()

    data_queue = queue.Queue()
    save_listener = threading.Thread(target=save_audio, args=(data_queue,logging_queue, SAMPLE_RATE, upload))
    save_listener.start()

    logging_queue.put("Listening for voice activity...")
    while True:
        audio_chunk = stream.read(NUM_SAMPLES, exception_on_overflow=False)
        padding_buffer.append(audio_chunk)
        if(collect_samples):
            audio_data.append(audio_chunk)
    
        audio_int16 = np.frombuffer(audio_chunk, np.int16)
        audio_float32 = int2float(audio_int16)
        tensor_audio_chunk = torch.from_numpy(audio_float32)
        tensor_audio_chunk_downsampled = functional.resample(tensor_audio_chunk, SAMPLE_RATE, VAD_TARGET_SAMPLE_RATE)
        
        speech_dict = vad_iterator(tensor_audio_chunk_downsampled, return_seconds=True)
        if(speech_dict):
            if('start' in speech_dict) and not collect_samples:
                logging_queue.put("Detected speech started.")
                collect_samples = True
                audio_data = list(padding_buffer)
            if('end' in speech_dict) and collect_samples:
                filename = 'speech-%s.wav' % datetime.now().strftime('%Y%m%d%M%S')
                trim_ending = (min_silence_duration_ms)/1000 # as there is min_silence_duration_ms to wait before audio ends
                trim_ending_chunks = int(SAMPLE_RATE * trim_ending / CHUNK)
                audio_data = audio_data[:-trim_ending_chunks]
                data_queue.put((audio_data, filename))
                logging_queue.put("Detected speech ended.")
                collect_samples = False
                audio_data = []
                padding_buffer.clear()
                stream.close()
                stream = open_stream(device_index)

def open_stream(device_index):
    return audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=int(device_index)
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Record audio with voice activity detection (VAD)')
    parser.add_argument('-d', '--device', help='input device index', required=True)
    parser.add_argument('-s', '--silence', help='period of silence (in miliseconds) after which recording gets saved', default=7000)
    parser.add_argument('-u', '--upload', help='should be uploading', action='store_true')
    args = parser.parse_args()

    start_recording(args.device, args.silence, args.upload)



