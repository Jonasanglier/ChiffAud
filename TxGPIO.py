import pyaudio
import numpy as np
import threading
import gpiod
import time
import queue
from contextlib import contextmanager

# ============================================
# Paramètres Audio et GPIO
# ============================================

# Paramètres audio
RATE = 16000           # Fréquence d'échantillonnage (16 kHz)
CHUNK_SIZE = 1024      # Taille du buffer audio, améliorée pour les performances

# Configuration de GPIO
GPIO_CHIP = 'gpiochip0'  # Identifiant du contrôleur GPIO (habituellement /dev/gpiochip0)
GPIO_LINE = 18           # Ligne GPIO utilisée (broche 18)

# Ressources partagées
audio_queue = queue.Queue(maxsize=10)  # File d'attente pour stocker les données audio à traiter
stop_event = threading.Event()         # Événement pour arrêter proprement les threads

# ============================================
# Gestionnaire de contexte pour GPIO
# ============================================

@contextmanager
def gpio_manager():
    # Configuration et acquisition de la ligne GPIO
    chip = gpiod.Chip(GPIO_CHIP)
    line = chip.get_line(GPIO_LINE)
    line.request(consumer='delta_signal', type=gpiod.LINE_REQ_DIR_OUT)  # Configurer la ligne GPIO comme sortie
    try:
        yield line  # Fournir l'accès à la ligne GPIO
    finally:
        line.release()  # Libérer la ligne GPIO à la fin de l'utilisation

# ============================================
# Fonction de modulation delta
# ============================================

def delta_modulate(sample, last_sample):
    """Effectue la modulation delta d'un échantillon audio."""
    if sample > last_sample:
        return 1, last_sample + 1  # Bit = 1 si l'échantillon actuel est supérieur à l'échantillon précédent
    else:
        return 0, last_sample - 1  # Bit = 0 sinon

# ============================================
# Thread de capture audio
# ============================================

def audio_input_thread(device_index=0):
    """Thread responsable de la capture du signal audio du microphone."""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK_SIZE)

    try:
        while not stop_event.is_set():
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)  # Lire les échantillons audio
            samples = np.frombuffer(data, dtype=np.int16)                # Convertir en tableau numpy
            
            # Essayer d'ajouter les échantillons dans la file d'attente
            try:
                audio_queue.put(samples, block=True, timeout=0.1)
            except queue.Full:
                print("Warning: Audio buffer full, dropping samples")   # Avertir si la file d'attente est pleine
    except Exception as e:
        print(f"Error in audio capture: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()  # Libérer les ressources audio

# ============================================
# Thread de traitement et sortie GPIO
# ============================================

def processing_thread():
    """Thread responsable du traitement du signal et de la transmission par GPIO."""
    last_sample = 0   # Dernier échantillon traité
    samples_processed = 0
    last_time = time.time()

    with gpio_manager() as gpio_line:
        while not stop_event.is_set():
            try:
                samples = audio_queue.get(block=True, timeout=0.1)  # Récupérer les échantillons de la file d'attente
                
                # Effectuer la modulation delta et transmettre le signal via GPIO
                for sample in samples:
                    bit, last_sample = delta_modulate(sample, last_sample)
                    try:
                        gpio_line.set_value(bit)
                    except gpiod.LineError as e:
                        print(f"GPIO error: {e}")
                
                samples_processed += len(samples)
                
                # Vérifier les performances toutes les secondes
                current_time = time.time()
                if current_time - last_time >= 1:
                    expected_samples = RATE
                    if samples_processed < expected_samples * 0.95:
                        print("Warning: Processing is falling behind")
                    samples_processed = 0
                    last_time = current_time
            
            except queue.Empty:
                continue  # Continuer si la file d'attente est vide

# ============================================
# Fonction principale
# ============================================

def main():
    """Démarre les threads de capture audio et de traitement."""
    audio_thread = threading.Thread(target=audio_input_thread)  # Thread de capture audio
    proc_thread = threading.Thread(target=processing_thread)    # Thread de traitement
    
    audio_thread.start()
    proc_thread.start()

    try:
        while True:
            time.sleep(0.1)  # Boucle principale du programme
    except KeyboardInterrupt:
        print("Stopping threads...")
        stop_event.set()  # Arrêter proprement les threads lorsque Ctrl+C est pressé
    
    # Attendre la fin des threads
    audio_thread.join()
    proc_thread.join()
    print("Program ended.")

# ============================================
# Point d'entrée du script
# ============================================

if __name__ == "__main__":
    main()
