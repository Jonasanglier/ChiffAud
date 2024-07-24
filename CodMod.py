import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import serial
import time

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

def plot_audio_stream(device_index=0, rate=44100, channels=1):
    p = pyaudio.PyAudio()
    
    # Configuration du flux audio pour l'entrée
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=channels,
                          rate=rate,
                          input=True,
                          input_device_index=device_index,
                          frames_per_buffer=1024)
    
    # Configuration du flux audio pour la sortie
    output_stream = p.open(format=pyaudio.paInt16,
                           channels=channels,
                           rate=rate,
                           output=True,
                           output_device_index=device_index)
    
    # Configuration du port série
    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

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
            data = input_stream.read(1024, exception_on_overflow=False)
            
            # Convertir les données audio en un tableau numpy
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Modulation CVSD
            mod_data = cvsd_modulate(audio_data)
            mod_data = np.array(mod_data)
            
            # Codage NRZ
            nrz_data = nrz_encode(mod_data)
            
            # Convertir les données NRZ en format compatible pour la sortie audio
            nrz_data_audio = np.int16(nrz_data * 32767)  # Scaler les données pour correspondre au format audio
            
            # Envoyer les données codées NRZ à la sortie audio
            output_stream.write(nrz_data_audio.tobytes())
            
            # Envoyer les données codées NRZ au port série
            for value in nrz_data:
                ser.write(f'{value}\n'.encode())
                time.sleep(1 / rate)
            
            # Mettre à jour les plots
            lines[0].set_ydata(audio_data)
            lines[1].set_ydata(mod_data)
            lines[2].set_ydata(nrz_data)
            
            fig.canvas.draw()
            fig.canvas.flush_events()
    
    except KeyboardInterrupt:
        print("Affichage et traitement terminés.")
    
    finally:
        # Arrêter les flux et fermer
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        ser.close()
        p.terminate()

# Utilisation du script
plot_audio_stream(device_index=0, rate=44100, channels=1)
