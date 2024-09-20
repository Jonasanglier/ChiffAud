import serial
import time

# Ouvre le port série
ser = serial.Serial(
    port='/dev/ttyAMA0',   # Port UART du Raspberry Pi
    baudrate=9600,         # Baud rate (même des deux côtés)
    timeout=1              # Temps avant d'abandonner la lecture
)

# Assurez-vous que le port est bien ouvert
if ser.is_open:
    print("Port série ouvert et prêt")

# Envoie des données
while True:
    ser.write(b"Bonjour de Raspberry Pi 1\n")  # Envoie un message en bytes