import numpy as np
import serial
import time

def generate_square_wave(frequency, sample_rate, duration):
    """
    Génère un signal carré.
    
    :param frequency: Fréquence du signal carré en Hz
    :param sample_rate: Taux d'échantillonnage en échantillons par seconde
    :param duration: Durée du signal en secondes
    :return: Tableau de données contenant le signal carré
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    square_wave = 0.5 * (1 + np.sign(np.sin(2 * np.pi * frequency * t)))
    return square_wave

def send_square_wave_via_serial(port, baudrate, frequency, sample_rate, duration):
    """
    Envoie un signal carré via le port série.
    
    :param port: Port série (par exemple, '/dev/ttyUSB0' ou 'COM3')
    :param baudrate: Débit en bauds
    :param frequency: Fréquence du signal carré en Hz
    :param sample_rate: Taux d'échantillonnage en échantillons par seconde
    :param duration: Durée du signal en secondes
    """
    # Générer le signal carré
    square_wave = generate_square_wave(frequency, sample_rate, duration)
    
    # Convertir le signal en données série
    square_wave_serial = np.int16(square_wave * 32767)  # Scaler pour correspondre au format série
    square_wave_bytes = square_wave_serial.tobytes()
    
    # Configurer le port série
    ser = serial.Serial(port, baudrate, timeout=1)
    
    try:
        while True:
            ser.write(square_wave_bytes)
            time.sleep(duration)  # Attendre la durée du signal avant d'envoyer à nouveau
    except KeyboardInterrupt:
        print("Transmission terminée.")
    finally:
        ser.close()

# Paramètres
port = '/dev/ttyUSB0'  # Remplace par le port série correct
baudrate = 9600
frequency = 1  # Fréquence du signal carré en Hz
sample_rate = 44100  # Taux d'échantillonnage en échantillons par seconde
duration = 1  # Durée du signal en secondes

# Envoyer le signal carré via le port série
send_square_wave_via_serial(port, baudrate, frequency, sample_rate, duration)
