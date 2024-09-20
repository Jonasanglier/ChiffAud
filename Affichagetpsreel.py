import pyaudio
import numpy as np
import matplotlib.pyplot as plt

# Paramètres d'audio
CHUNK = 1024        # Nombre d'échantillons par chunk
RATE = 16000        # Fréquence d'échantillonnage (16kHz)
CHANNELS = 1        # Nombre de canaux (1 pour mono)
FORMAT = pyaudio.paInt16  # Format des données (16-bit)

# Initialisation de PyAudio
p = pyaudio.PyAudio()

input_device_index = 0  # Mettre l'index correct ici

# Ouverture du flux audio
input_stream = p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      input=True,
                      input_device_index=input_device_index,  # Utiliser l'index de la carte son
                      frames_per_buffer=CHUNK)

# Configuration du graphique
plt.ion()  # Mode interactif
fig, ax = plt.subplots()
x = np.arange(0, 2 * CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK), '-')

ax.set_ylim(-60000, 60000)  # Plage d'amplitude pour 16 bits (signed int)
ax.set_xlim(0, CHUNK)

# Titre du graphe
ax.set_title('Signal Audio')

print("Visualisation du signal audio en cours...")

try:
    while True:
        # Lecture des données du microphone
        data = input_stream.read(CHUNK, exception_on_overflow=False)
        
        # Conversion des données en tableau numpy
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Mise à jour du graphique
        line.set_ydata(audio_data)
        fig.canvas.draw()
        fig.canvas.flush_events()

except KeyboardInterrupt:
    print("Arrêt du programme.")

finally:
    # Fermeture du flux et du PyAudio
    input_stream.stop_stream()
    input_stream.close()
    p.terminate()
    plt.ioff()
    plt.show()
