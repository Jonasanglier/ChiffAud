import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import threading

# Variables partagées et verrous
audio_data_shared = None
audio_data_lock = threading.Lock()

# Thread de capture audio
def audio_input_thread(device_index=0, rate=44100, channels=1, chunk_size=2048):
    global audio_data_shared
    p = pyaudio.PyAudio()
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=channels,
                          rate=rate,
                          input=True,
                          input_device_index=device_index,
                          frames_per_buffer=chunk_size)
    try:
        while True:
            data = input_stream.read(chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            with audio_data_lock:
                audio_data_shared = audio_data
    except KeyboardInterrupt:
        pass
    finally:
        input_stream.stop_stream()
        input_stream.close()
        p.terminate()

# Thread d'affichage du signal audio
def plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048):
    threading.Thread(target=audio_input_thread, args=(device_index, rate, channels, chunk_size)).start()

    print("Affichage du signal audio en cours...")
    
    plt.ion()
    fig, ax = plt.subplots()

    x = np.arange(0, chunk_size, 1)
    
    # Plot initial
    line, = ax.plot(x, np.random.rand(chunk_size))
    ax.set_ylim(-32768, 32768)
    ax.set_title('Signal Audio Original')
    
    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Mettre à jour le plot
                line.set_ydata(audio_data)
                
                fig.canvas.draw()
                fig.canvas.flush_events()
    
    except KeyboardInterrupt:
        print("Affichage terminé.")
    
    finally:
        plt.ioff()
        plt.show()

# Utilisation du script
plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048)
