import pyaudio
import numpy as np
import matplotlib.pyplot as plt

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

def cvsd_demodulate(encoded, delta_init=0.2, mu=1.5):
    delta = delta_init
    estimate = 0
    decoded = []
    for i, bit in enumerate(encoded):
        if bit == 1:
            estimate += delta
        else:
            estimate -= delta

        decoded.append(estimate)

        if i >= 1 and encoded[i] == encoded[i-1]:
            delta *= mu
        else:
            delta /= mu

    return np.array(decoded)

def nrz_encode(data):
    """Encodage NRZ simple."""
    return np.where(data > 0.5, 1, -1)

def nrz_decode(data):
    """Décodage NRZ simple."""
    return np.where(data > 0, 1, 0)

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
    fig, axs = plt.subplots(5, 1, sharex=True)
    
    x = np.arange(0, 2 * 1024, 2)
    
    # Initial plots for each subplot
    lines = []
    for ax in axs:
        line, = ax.plot(x, np.random.rand(1024))
        lines.append(line)
    
    axs[0].set_ylim(-32768, 32768)
    axs[1].set_ylim(-0.2, 1.2)
    axs[2].set_ylim(-1.2, 1.2)
    axs[3].set_ylim(-0.2, 1.2)
    axs[4].set_ylim(-32768, 32768)
    
    axs[0].set_title('Signal Audio Original')
    axs[1].set_title('Signal Modulé CVSD')
    axs[2].set_title('Signal Codé en NRZ')
    axs[3].set_title('Signal Décodé en NRZ')
    axs[4].set_title('Signal Démodulé CVSD')

    try:
        while True:
            data = stream.read(1024, exception_on_overflow=False)
            
            # Convertir les données audio en un tableau numpy
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            # Modulation CVSD
            mod_data = cvsd_modulate(audio_data)
            mod_data = np.array(mod_data)
            
            # Codage NRZ
            nrz_data = nrz_encode(mod_data)
            
            # Décodage NRZ
            nrz_decoded_data = nrz_decode(nrz_data)
            
            # Démodulation CVSD
            demod_data = cvsd_demodulate(nrz_decoded_data)
            
            # Mettre à jour les plots
            lines[0].set_ydata(audio_data)
            lines[1].set_ydata(mod_data)
            lines[2].set_ydata(nrz_data)
            lines[3].set_ydata(nrz_decoded_data)
            lines[4].set_ydata(demod_data)
            
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
