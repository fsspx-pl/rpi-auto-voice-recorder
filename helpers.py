import os
import numpy as np
from ffmpeg import FFmpeg

def create_folder_if_not_exists(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")

def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound

def convert_to_m4a(input_file):
    output_file = os.path.splitext(input_file)[0] + ".m4a"
    FFmpeg().input(input_file).output(output_file, ar=44100).execute()
    return output_file