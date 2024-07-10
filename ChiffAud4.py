import sounddevice as sd
import numpy as np
import wave

def record_audio(filename, duration, samplerate=44100, device = 1):
    print("Démarrage de l'enregistrement...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, dtype='int16')
    sd.wait()
    print("Enregistrement terminé.")

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_data.tobytes())

print(sd.query_devices())

if __name__ == "__main__":
    filename = 'output.wav'
    duration = 10

    record_audio(filename, duration)
