import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import serial
import time
import threading
from queue import Queue

def cvsd_modulate(signal, delta_init=0.2, mu=1.5):
    encoded = []
    delta = delta_init
    estimate = 0
    for sample in signal:
        if sample > estimate:
            encoded.append(1)
            estimate += delta
        else:
            encoded.append(0)
            estimate -= delta

        if len(encoded) > 1 and encoded[-1] == encoded[-2]:
            delta *= mu
        else:
            delta /= mu
    return encoded

def nrz_encode(data):
    """Encodage NRZ simple."""
    return np.where(data > 0.5, 1, -1)

def audio_input_thread(input_queue, device_index=0, rate=44100, channels=1):
    p = pyaudio.PyAudio()
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=channels,
                          rate=rate,
                          input=True,
                          input_device_index=device_index,
                          frames_per_buffer=1024)
    try:
        while True:
            data = input_stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            input_queue.put(audio_data)
    except KeyboardInterrupt:
        pass
    finally:
        input_stream.stop_stream()
        input_stream.close()
        p.terminate()

def audio_output_thread(output_queue, device_index=0, rate=44100, channels=1):
    p = pyaudio.PyAudio()
    output_stream = p.open(format=pyaudio.paInt16,
                           channels=channels,
                           rate=rate,
                           output=True,
                           output_device_index=device_index)
    try:
        while True:
            nrz_data_audio = output_queue.get()
            output_stream.write(nrz_data_audio.tobytes())
    except KeyboardInterrupt:
        pass
    finally:
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

def serial_output_thread(serial_queue):
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    try:
        while True:
            nrz_data_audio = serial_queue.get()
            ser.write(nrz_data_audio.tobytes())
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

def plot_audio_stream(device_index=0, rate=44100, channels=1):
    input_queue = Queue()
    output_queue = Queue()
    serial_queue = Queue()

    threading.Thread(target=audio_input_thread, args=(input_queue, device_index, rate, channels)).start()
    threading.Thread(target=audio_output_thread, args=(output_queue, device_index, rate, channels)).start()
    threading.Thread(target=serial_output_thread, args=(serial_queue,)).start()

    print("Affichage et traitement du signal en cours...")
    
    plt.ion()
    fig, axs = plt.subplots(3, 1, sharex=True)
    
    x = np.arange(0, 2 * 1024, 2)
    
    # Initial plots for each subplot
    lines = []
    for ax in axs:
        line, = ax.plot(x, np.random.rand(1024))
        lines.append(line)
    
    axs[0].set_ylim(-32768, 32768)
    axs[1].set_ylim(-0.2, 1.2)
    axs[2].set_ylim(-1.2, 1.2)
    
    axs[0].set_title('Signal Audio Original')
    axs[1].set_title('Signal Modulé CVSD')
    axs[2].set_title('Signal Codé en NRZ')

    try:
        while True:
            audio_data = input_queue.get()
            
            # Modulation CVSD
            mod_data = cvsd_modulate(audio_data)
            mod_data = np.array(mod_data)
            
            # Codage NRZ
            nrz_data = nrz_encode(mod_data)
            
            # Convertir les données NRZ en format compatible pour la sortie audio
            nrz_data_audio = np.int16(nrz_data * 32767)  # Scaler les données pour correspondre au format audio
            
            # Mettre les données dans les files d'attente pour la sortie audio et série
            output_queue.put(nrz_data_audio)
            serial_queue.put(nrz_data_audio)
            
            # Mettre à jour les plots
            lines[0].set_ydata(audio_data)
            lines[1].set_ydata(mod_data)
            lines[2].set_ydata(nrz_data)
            
            fig.canvas.draw()
            fig.canvas.flush_events()
    
    except KeyboardInterrupt:
        print("Affichage et traitement terminés.")
    
    finally:
        plt.ioff()
        plt.show()

# Utilisation du script
plot_audio_stream(device_index=0, rate=44100, channels=1)
