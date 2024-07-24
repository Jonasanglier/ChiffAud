import serial
import time
import numpy as np

# Configuration du port série
port = '/dev/ttyUSB0'
baudrate = 9600  # Ajustez la vitesse de transmission selon vos besoins

# Paramètres du signal sinusoïdal
frequency = 1  # Fréquence en Hz
amplitude = 1  # Amplitude
sampling_rate = 100  # Taux d'échantillonnage en Hz
duration = 1 / frequency  # Durée d'un cycle en secondes

# Générer un cycle de signal sinusoïdal
t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
sin_wave = amplitude * np.sin(2 * np.pi * frequency * t)

try:
    # Ouverture du port série
    ser = serial.Serial(port, baudrate, timeout=1)

    # Vérification de l'ouverture du port
    if ser.is_open:
        print(f'Port {ser.name} ouvert avec succès')
    else:
        print(f'Impossible d\'ouvrir le port {ser.name}')
        exit(1)

    print('Envoi du signal sinusoïdal en continu. Appuyez sur Ctrl+C pour arrêter.')

    # Envoyer le signal sinusoïdal en continu
    while True:
        for value in sin_wave:
            # Envoyer la valeur du signal convertie en string et encodée en bytes
            ser.write(f'{value}\n'.encode())
            # Attendre un intervalle de temps pour correspondre au taux d'échantillonnage
            time.sleep(1 / sampling_rate)

except KeyboardInterrupt:
    print('Arrêt du signal demandé par l\'utilisateur.')
except serial.SerialException as e:
    print(f'Erreur: {e}')
finally:
    if ser.is_open:
        ser.close()
        print('Port fermé')
