import serial
import pyaudio
import numpy as np
import threading
import matplotlib.pyplot as plt

# Variables partagées et verrous
audio_data_shared = None
audio_data_lock = threading.Lock()

# Ouvre le port série UART
ser = serial.Serial(
    port='/dev/ttyAMA0',   # Port UART du Raspberry Pi
    baudrate=1600,        # Baud rate (même des deux côtés)
    timeout=1              # Temps avant d'abandonner la lecture
)

# Assurez-vous que le port série est bien ouvert
if ser.is_open:
    print("Port série ouvert et prêt")

# Fonction de modulation Delta
def delta_modulate(signal, delta_init=1):
    encoded = []
    estimate = 0  # Point de départ de l'estimation

    for sample in signal:
        if sample > estimate:
            encoded.append(1)
            estimate += delta_init
        else:
            encoded.append(0)
            estimate -= delta_init

    return encoded

# Fonction de démodulation Delta
def delta_demodulate(encoded, delta_init=1):
    estimate = 0
    signal_reconstructed = []

    for bit in encoded:
        if bit == 1:
            estimate += delta_init
        else:
            estimate -= delta_init
        signal_reconstructed.append(estimate)

    return np.array(signal_reconstructed, dtype=np.int16)

# Thread de capture audio
def audio_input_thread(device_index=0, rate=16000, channels=1, chunk_size=1024):
    global audio_data_shared
    p = pyaudio.PyAudio()
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=channels,
                          rate=rate,  # Fréquence d'échantillonnage à 16kHz
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

# Thread d'envoi UART en temps réel
def uart_output_thread():
    global audio_data_shared

    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation Delta
                mod_data = delta_modulate(audio_data)
                
                # Convertir les bits encodés en bytes
                mod_data_bytes = np.packbits(mod_data)  # Convertir la liste de bits en octets
                
                # Envoi sur UART
                ser.write(mod_data_bytes)

    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

# Thread d'affichage du signal audio, du signal modulé et du signal démodulé
def plot_thread(chunk_size=1024):
    global audio_data_shared

    # Configuration des graphes
    plt.ion()
    fig, axs = plt.subplots(3, 1, sharex=True)
    x = np.arange(0, chunk_size)

    # Plots initiaux pour les signaux
    line1, = axs[0].plot(x, np.random.rand(chunk_size), label="Signal capturé")
    line2, = axs[1].plot(x, np.random.rand(chunk_size), label="Signal modulé (bits)")
    line3, = axs[2].plot(x, np.random.rand(chunk_size), label="Signal démodulé")

    axs[0].set_ylim(-32768, 32768)  # Pour signal audio capturé
    axs[1].set_ylim(-0.2, 1.2)      # Pour signal modulé (0 ou 1)
    axs[2].set_ylim(-32768, 32768)  # Pour signal démodulé

    axs[0].set_title('Signal Audio Original (envoyé)')
    axs[1].set_title('Signal Modulé Delta (bits)')
    axs[2].set_title('Signal Audio Démodulé')

    plt.show()

    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation Delta
                mod_data = delta_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Démodulation Delta
                demodulated_data = delta_demodulate(mod_data)

                # Mettre à jour les graphes
                line1.set_ydata(audio_data)
                line2.set_ydata(mod_data)
                line3.set_ydata(demodulated_data)

                fig.canvas.draw()
                fig.canvas.flush_events()

    except KeyboardInterrupt:
        print("Affichage arrêté.")
    finally:
        plt.ioff()
        plt.show()

# Utilisation du script
def main():
    # Lancer les threads de capture audio, d'envoi UART et d'affichage
    threading.Thread(target=audio_input_thread, args=(0, 16000, 1, 1024)).start()  # 16kHz FE
    threading.Thread(target=uart_output_thread).start()
    threading.Thread(target=plot_thread, args=(1024,)).start()

    print("Capture, envoi UART et affichage en temps réel en cours...")
    
    # Attente infinie
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Arrêt du script.")

if __name__ == "__main__":
    main()
