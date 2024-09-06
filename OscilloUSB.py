import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import time

# Configurer le port série
ser = serial.Serial('/dev/ttyUSB0', 9600) 

# Configurer l'affichage
plt.ion()  # Activer le mode interactif
fig, ax = plt.subplots()
xdata, ydata = [], []
ln, = plt.plot([], [], 'r-')
plt.xlabel('Temps (s)')
plt.ylabel('Données série')

def init():
    ax.set_xlim(0, 10)  # Afficher les 10 premières secondes
    ax.set_ylim(-1.5, 1.5)  # Limites des données (à ajuster selon vos besoins)
    return ln,

def update(frame):
    line = ser.readline().decode('utf-8').strip()
    try:
        y = float(line)
        xdata.append(time.time() - start_time)
        ydata.append(y)
        ln.set_data(xdata, ydata)
        ax.set_xlim(max(0, xdata[-1] - 10), xdata[-1])  # Glissement de fenêtre de 10 secondes
    except ValueError:
        pass  # Ignorez les lignes non numériques
    return ln,

start_time = time.time()
ani = FuncAnimation(fig, update, init_func=init, blit=True)
plt.show()

# Garder le script en cours d'exécution
while True:
    plt.pause(0.1)
