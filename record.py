import torch
torch.set_num_threads(1)
import numpy as np
import pyaudio
import os
from ffmpeg import FFmpeg

model, utils = torch.hub.load(repo_or_dir='vendor/silero-vad-master',
                              source='local',
                              model='silero_vad',
                              onnx=True)

(get_speech_timestamps,
 _, read_audio,
 VadIterator, _) = utils

# ### Helper Methods

def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound

# ## Pyaudio Set-up

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
VAD_TARGET_SAMPLE_RATE = 16000
CHUNK = int(SAMPLE_RATE / 20)

audio = pyaudio.PyAudio()

import threading
import queue
import wave
import datetime
from datetime import datetime
from torchaudio import functional

NUM_SAMPLES = 1536

def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

def save_audio(data_queue, logging_queue, sample_rate, folder_name='output'):
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
        os.remove(pathname)
        data_queue.task_done()

def convert_to_m4a(input_file):
    output_file = os.path.splitext(input_file)[0] + ".m4a"
    FFmpeg().input(input_file).output(output_file, ar=44100).execute()
    return output_file

def log_message(logging_queue):
    while True:
        message = logging_queue.get()
        print(message, flush=True)
        logging_queue.task_done()

def start_recording():
    vad_iterator = VadIterator(model, min_silence_duration_ms=3000, threshold=0.7)
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=0
    )

    audio_data = []
    
    logging_queue = queue.Queue()
    logging_listener = threading.Thread(target=log_message, args=(logging_queue,))
    logging_listener.start()

    data_queue = queue.Queue()
    save_listener = threading.Thread(target=save_audio, args=(data_queue,logging_queue, SAMPLE_RATE))
    save_listener.start()

    
    logging_queue.put("Listening for voice activity...")
    while True:
        audio_chunk = stream.read(NUM_SAMPLES, exception_on_overflow=False)
        audio_data.append(audio_chunk)
    
        audio_int16 = np.frombuffer(audio_chunk, np.int16)
        audio_float32 = int2float(audio_int16)
        tensor_audio_chunk = torch.from_numpy(audio_float32)
        tensor_audio_chunk_downsampled = functional.resample(tensor_audio_chunk, SAMPLE_RATE, VAD_TARGET_SAMPLE_RATE)
        
        speech_dict = vad_iterator(tensor_audio_chunk_downsampled, return_seconds=True)
        if(speech_dict):
            if('start' in speech_dict):
                logging_queue.put("Detected speech started.")
            if('end' in speech_dict):
                filename = 'speech-%s.wav' % datetime.now().strftime('%Y%m%d%M%S')
                data_queue.put((audio_data, filename))
                logging_queue.put("Detected speech ended.")
                audio_data = []


start_recording()



