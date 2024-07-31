import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import serial
import threading

# Variables partagées et verrous
audio_data_shared = None
audio_data_lock = threading.Lock()

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

def audio_output_thread(device_index=0, rate=44100, channels=1):
    global audio_data_shared
    p = pyaudio.PyAudio()
    output_stream = p.open(format=pyaudio.paInt16,
                           channels=channels,
                           rate=rate,
                           output=True,
                           output_device_index=device_index)
    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation CVSD
                mod_data = cvsd_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Codage NRZ
                nrz_data = nrz_encode(mod_data)

                # Convertir les données NRZ en format compatible pour la sortie audio
                nrz_data_audio = np.int16(nrz_data * 32767)  # Scaler les données pour correspondre au format audio
                output_stream.write(nrz_data_audio.tobytes())
    except KeyboardInterrupt:
        pass
    finally:
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

def serial_output_thread():
    global audio_data_shared
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation CVSD
                mod_data = cvsd_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Codage NRZ
                nrz_data = nrz_encode(mod_data)

                # Convertir les données NRZ en format compatible pour la sortie série
                nrz_data_audio = np.int16(nrz_data * 32767)  # Scaler les données pour correspondre au format série
                ser.write(nrz_data_audio.tobytes())
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

def plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048):
    threading.Thread(target=audio_input_thread, args=(device_index, rate, channels, chunk_size)).start()
    threading.Thread(target=audio_output_thread, args=(device_index, rate, channels)).start()
    threading.Thread(target=serial_output_thread).start()

    print("Affichage et traitement du signal en cours...")
    
    plt.ion()
    fig, axs = plt.subplots(3, 1, sharex=True)
    
    x = np.arange(0, 2 * chunk_size, 2)
    
    # Initial plots for each subplot
    lines = []
    for ax in axs:
        line, = ax.plot(x, np.random.rand(chunk_size))
        lines.append(line)
    
    axs[0].set_ylim(-32768, 32768)
    axs[1].set_ylim(-0.2, 1.2)
    axs[2].set_ylim(-1.2, 1.2)
    
    axs[0].set_title('Signal Audio Original')
    axs[1].set_title('Signal Modulé CVSD')
    axs[2].set_title('Signal Codé en NRZ')

    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation CVSD
                mod_data = cvsd_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Codage NRZ
                nrz_data = nrz_encode(mod_data)

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
plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048)
