import gpiod
import time

square = 17
# Configuration du numéro de ligne GPIO (GPIO4 en Broadcom)
chip = gpiod.Chip('4')  # Utilisez '/dev/gpiochip0' pour le premier contrôleur GPIO
line = chip.get_line(square)  # GPIO4 en Broadcom BCM correspond à la broche physique 7

# Configuration de la ligne GPIO comme sortie
line.request(consumer='square_signal', type=gpiod.LINE_REQ_DIR_OUT)

# Fréquence du signal carré en Hz
frequency = 100000  # Changez cette valeur selon vos besoins

# Durée du cycle de travail (duty cycle), de 0 à 1 (50% = 0.5)
duty_cycle = 0.5

# Période du signal carré
period = 1.0 / frequency

try:
    while True:
        # Met la broche à l'état haut
        line.set_value(1)
        print("Signal HIGH")
        time.sleep(1)
        #time.sleep(period * duty_cycle)
        
        # Met la broche à l'état bas
        line.set_value(0)
        print("Signal LOW")
        time.sleep(1)

except KeyboardInterrupt:
    print("Programme interrompu")
    
finally:
    # Libération de la ligne GPIO
    line.release()

