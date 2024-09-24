import serial
import matplotlib.pyplot as plt
import time

# Initialiser la connexion série
ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=16000,
    timeout=1
)

# Vérifier si le port est ouvert
if ser.is_open:
    print("Port série ouvert et prêt")

# Liste pour stocker les données reçues
data_values = []
timestamps = []

# Temps initial
start_time = time.time()

# Initialiser la figure et la courbe
plt.ion()  # Mode interactif
fig, ax = plt.subplots()
line, = ax.plot([], [], label="Données série")
ax.set_xlim(0, 10)  # Vous pouvez ajuster les limites selon votre besoin
ax.set_ylim(0, 2)  # Plage des valeurs (ex : 0-255 pour un octet)
ax.set_xlabel("Temps (secondes)")
ax.set_ylabel("Valeur reçue")
ax.legend()
ax.grid(True)

try:
    while True:
        # Lire les données en bytes
        data = ser.read()

        if data:
            # Convertir les données en int (vous pouvez adapter en fonction de vos données)
            data_value = int.from_bytes(data, byteorder='big')  # Par exemple sur 1 octet
            data_values.append(data_value)

            # Enregistrer l'horodatage relatif
            timestamp = time.time() - start_time
            timestamps.append(timestamp)

            # Afficher la donnée dans le terminal
            print(f"Reçu (valeur décimale) : {data_value}")

            # Mettre à jour les données du graphique
            line.set_data(timestamps, data_values)

            # Ajuster les limites de l'axe x en fonction du temps
            ax.set_xlim(0, max(10, timestamp))

            # Redessiner le graphique
            plt.draw()
            plt.pause(0.01)  # Pause pour permettre l'affichage

except Exception as e:
    print(f"Erreur : {e}")

finally:
    # Fermer la connexion série
    ser.close()

# Fermer la figure à la fin (ne sera probablement jamais atteint dans une boucle infinie)
plt.ioff()
plt.show()

