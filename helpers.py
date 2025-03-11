import os
import numpy as np
from ffmpeg import FFmpeg
import json
import subprocess

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
    """Convert WAV file to M4A using subprocess to call FFmpeg directly."""
    output_file = input_file.replace('.wav', '.m4a')
    
    try:
        # Use subprocess to call FFmpeg directly
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',
            output_file
        ]
        
        # Run the command and capture output
        process = subprocess.run(
            cmd,
            check=False,  # Don't raise exception on non-zero exit
            capture_output=True,
            text=True
        )
        
        # Check if the conversion was successful
        if process.returncode != 0:
            print(f"FFmpeg error (code {process.returncode}):")
            print(process.stderr)
            return input_file  # Return original file on error
        
        return output_file
        
    except Exception as e:
        print(f"Error during audio conversion: {e}")
        return input_file  # Return original file on error

def calculateRms(sound):
    rms = np.sqrt(np.mean(sound**2))
    return rms

def from_json(json_path):
    with open(json_path) as f:
        config = json.load(f)
        f.close()
        return config
