import pyaudio
import wave

if __name__ == "__main__":
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 3
    WAVE_OUTPUT_FILENAME = 'filename'
    DEVICE_INDEX = 0

    audio = pyaudio.PyAudio()

    list_audio = []
    for x in range(0, audio.get_device_count()):
        info = audio.get_device_info_by_index(x)
        print("info {0}".format(info))

    # start Recording
    stream = audio.open(input_device_index=DEVICE_INDEX,
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    # sample_rate=RATE)
    print("recording...")
    print('---------------------------------')
    print(int(RATE / CHUNK * RECORD_SECONDS))
    print('*********************************')

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        print("Recording . . .")

        frames.append(data)
    print("Recording finished. . .")

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(2)
    audio.get_sample_size(FORMAT)
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
