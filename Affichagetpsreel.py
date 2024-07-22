import pyaudio
import numpy as np
import matplotlib.pyplot as plt

def plot_audio_stream(device_index=0, rate=44100, channels=1):
    p = pyaudio.PyAudio()
    
    # Configuration du flux audio
    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024)
    
    print("Affichage du signal en cours...")
    
    plt.ion()
    fig, ax = plt.subplots()
    x = np.arange(0, 2 * 1024, 2)
    line, = ax.plot(x, np.random.rand(1024))
    ax.set_ylim(-32768, 32768)
    ax.set_xlim(0, 1024)

    try:
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            
            # Convertir les données audio en un tableau numpy
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Mettre à jour la plot
            line.set_ydata(audio_data)
            fig.canvas.draw()
            fig.canvas.flush_events()
    
    except KeyboardInterrupt:
        print("Affichage terminé.")
    
    finally:
        # Arrêter le flux et fermer
        stream.stop_stream()
        stream.close()
        p.terminate()

# Utilisation du script
plot_audio_stream(device_index=0, rate=44100, channels=1)

