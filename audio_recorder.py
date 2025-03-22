#!/usr/bin/env python3

import torch
torch.set_num_threads(1)
import numpy as np
import pyaudio
import os
import argparse
import threading
import queue
import wave
import datetime
from datetime import datetime
from torchaudio import functional
from helpers import create_folder_if_not_exists, convert_to_m4a, from_json, int2float
from file_uploader import upload as upload_file
from log import log_message
from collections import deque
from math import floor
import ptz

class AudioRecorder:
    def __init__(
        self,
        device_index,
        min_silence_duration_ms=7000,
        upload=False,
        padding_ms=1000,
        min_record_time_seconds=15,
        record_video=False
    ):
        self.device_index = device_index
        self.min_silence_duration_ms = min_silence_duration_ms
        self.padding_ms = padding_ms
        self.model, self.utils = torch.hub.load(repo_or_dir='vendor/silero-vad-master',
                                                source='local',
                                                model='silero_vad',
                                                onnx=True)

        (self.get_speech_timestamps,
         _,
         self.read_audio,
         self.VadIterator, _) = self.utils

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SAMPLE_RATE = 44100
        self.VAD_TARGET_SAMPLE_RATE = 16000
        self.NUM_SAMPLES = 1536
        self.CHUNK = int(self.SAMPLE_RATE / 20)
        self.MIN_RECORD_TIME_SECONDS = min_record_time_seconds

        self.audio = pyaudio.PyAudio()

        self.logging_queue = queue.Queue()
        self.logging_listener = threading.Thread(target=log_message, args=(self.logging_queue,))
        self.logging_listener.start()

        self.data_queue = queue.Queue()
        self.save_listener = threading.Thread(target=self.save_audio, args=(self.data_queue, self.logging_queue, self.SAMPLE_RATE, upload))
        self.save_listener.start()

        if(not record_video):
            return

        # Initialize camera-related attributes
        self.myCam = None
        self.positions = None
        
        # Try to initialize the camera
        try:
            self.logging_queue.put("Initializing camera")
            self.myCam = ptz.ptzcam()
            self.positions = from_json('camera_positions.json')
            self.move_to(self.positions['prezbiterium'])
        except Exception as e:
            self.logging_queue.put(f"Failed to instantiate camera: {e}")

    def save_audio(self, data_queue, logging_queue, sample_rate, upload, folder_name='output'):
        while True:
            try:
                audio_data, filename = data_queue.get()
                duration = len(audio_data) / sample_rate * 1000
                minutes = floor(duration/60)
                seconds = round(duration % 60)
                
                if(duration < self.MIN_RECORD_TIME_SECONDS):
                    logging_queue.put(f"Too short speech duration of {seconds}s, it has to be at least {self.MIN_RECORD_TIME_SECONDS}s. Skipping...")
                else:
                    create_folder_if_not_exists(folder_name)
                    pathname = folder_name + '/' + filename
                    
                    with wave.open(pathname, 'wb') as wf:
                        wf.setnchannels(self.CHANNELS)
                        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
                        wf.setframerate(self.SAMPLE_RATE)
                        wf.writeframes(b''.join(audio_data))
                    
                    output_file = convert_to_m4a(pathname)
                    logging_queue.put(f"Saved detected speech of {minutes}m{seconds}s to a file {output_file}")
                    
                    if output_file != pathname and os.path.exists(output_file):
                        try:
                            os.remove(pathname)
                            logging_queue.put(f"Removed original WAV file: {pathname}")
                        except Exception as e:
                            logging_queue.put(f"Error removing WAV file {pathname}: {e}")
                    
                    if(upload):
                        upload_file(output_file, os.path.basename(output_file), logging_queue)
                
                data_queue.task_done()
            except Exception as e:
                logging_queue.put(f"Error in save_audio: {e}")
                data_queue.task_done()

    def start_recording(self):
        self.vad_iterator = self.VadIterator(self.model, min_silence_duration_ms=self.min_silence_duration_ms, threshold=0.997)
        self.stream = self.open_stream(self.device_index)

        self.audio_data = []
        self.collect_samples = False
        self.padding_s = self.padding_ms/1000
        self.padding_chunks = int(self.SAMPLE_RATE * self.padding_s / self.CHUNK)
        self.padding_buffer = deque(maxlen=self.padding_chunks)

        self.logging_queue.put("Listening for voice activity...")
        while True:
            speech_dict = self.process_audio_chunk()
            self.detect_speech_start(speech_dict)
            self.detect_speech_end(speech_dict)

    def process_audio_chunk(self):
        audio_chunk = self.stream.read(self.NUM_SAMPLES, exception_on_overflow=False)
        self.padding_buffer.append(audio_chunk)
        if(self.collect_samples):
            self.audio_data.append(audio_chunk)

        audio_int16 = np.frombuffer(audio_chunk, np.int16)
        audio_float32 = int2float(audio_int16)
        tensor_audio_chunk = torch.from_numpy(audio_float32)
        tensor_audio_chunk_downsampled = functional.resample(tensor_audio_chunk, self.SAMPLE_RATE, self.VAD_TARGET_SAMPLE_RATE)
        speech_dict = self.vad_iterator(tensor_audio_chunk_downsampled, return_seconds=True)
        return speech_dict

    def detect_speech_start(self, speech_dict):
        if(speech_dict and 'start' in speech_dict and not self.collect_samples):
            self.logging_queue.put("Detected speech started.")
            self.collect_samples = True
            self.audio_data = list(self.padding_buffer)
            if(self.myCam):
                self.move_to(self.positions['ambona'])

    def detect_speech_end(self, speech_dict):
        if(speech_dict and 'end' in speech_dict and self.collect_samples):
            filename = 'speech-%s.wav' % datetime.now().strftime('%Y-%-m-%d-%M-%S')
            trim_ending = (self.min_silence_duration_ms)/1000 # as there is min_silence_duration_ms to wait before audio ends
            trim_ending_chunks = int(self.SAMPLE_RATE * trim_ending / self.CHUNK)
            self.audio_data = self.audio_data[:-trim_ending_chunks]
            self.data_queue.put((self.audio_data, filename))
            self.logging_queue.put("Detected speech ended.")
            self.collect_samples = False
            self.audio_data = []
            self.padding_buffer.clear()
            self.stream.close()
            self.stream = self.open_stream(self.device_index)

            if(self.myCam):
                self.move_to(self.positions['prezbiterium'])

    def open_stream(self, device_index):
        return self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            input_device_index=int(device_index)
        )
    
    def move_to(self, position):
        self.myCam.move_abspantilt(position.pan, position.tilt, 1)
        self.myCam.zoom(position.zoom, 1) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Record audio with voice activity detection (VAD)')
    parser.add_argument('-d', '--device', help='input device index', required=True)
    parser.add_argument('-s', '--silence', help='period of silence (in miliseconds) after which recording gets saved', default=7000, type=int)
    parser.add_argument('-u', '--upload', help='should be uploading', action='store_true')
    parser.add_argument('-m', '--min-record-time-seconds', help='minimum recording time (in seconds)', default=15, type=int)
    parser.add_argument('-c', '--record-video', help='whether to record video', action='store_true')
    args = parser.parse_args()

    audio_recorder = AudioRecorder(
        device_index=args.device,
        min_silence_duration_ms=args.silence,
        upload=args.upload,
        min_record_time_seconds=args.min_record_time_seconds,
        record_video=args.record_video
    ).start_recording()
