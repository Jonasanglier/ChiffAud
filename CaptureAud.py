import pyaudio
import wave

def record_audio(output_filename, duration=5, channels=2, rate=44100, device_index=0):
    p = pyaudio.PyAudio()
    
    # Configuration du flux audio
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024)
    
    print("Enregistrement en cours...")
    frames = []
    
    # Enregistrement de l'audio
    for _ in range(0, int(rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)
    
    print("Enregistrement terminé.")
    
    # Arrêter le flux et fermer
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Sauvegarde de l'enregistrement dans un fichier WAV
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

# Utilisation du script
record_audio('output.wav', duration=5, channels=2, rate=44100, device_index=0)
