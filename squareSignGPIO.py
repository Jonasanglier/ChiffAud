import gpiod
import time

# Configuration de GPIO
chip = gpiod.Chip('gpiochip0')
line = chip.get_line(18)
line.request(consumer='test_signal', type=gpiod.LINE_REQ_DIR_OUT)

try:
    while True:
        line.set_value(1)  # Mettre la broche à HIGH
        time.sleep(0.5)    # Attendre 0,5 seconde
        line.set_value(0)  # Mettre la broche à LOW
        time.sleep(0.5)    # Attendre 0,5 seconde
except KeyboardInterrupt:
    print("Fin du test.")
