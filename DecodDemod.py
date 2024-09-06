import pyaudio
import numpy as np
import gpiod
import threading
import time

# Variables partagées et verrous
decoded_audio_shared = None
decoded_audio_lock = threading.Lock()

def cvsd_demodulate(encoded, delta_init=0.2, mu=1.5):
    decoded = []
    delta = delta_init
    estimate = 0

    for bit in encoded:
        if bit == 1:
            estimate += delta
        else:
            estimate -= delta

        # Clamping the estimate to avoid overflow
        estimate = np.clip(estimate, -32768, 32767)
        decoded.append(estimate)

        if len(decoded) > 1 and encoded[len(decoded)-1] == encoded[len(decoded)-2]:
            delta *= mu
        else:
            delta /= mu

    return np.array(decoded, dtype=np.int16)

def gpio_input_thread():
    global decoded_audio_shared
    chip = gpiod.Chip('4')  # Use '/dev/gpiochip0' for the first GPIO controller
    line = chip.get_line(22)  # GPIO22
    line.request(consumer='cvsd_signal', type=gpiod.LINE_REQ_DIR_IN)

    try:
        while True:
            encoded_signal = []
            for _ in range(2048):  # Read chunks of 2048 bits
                bit = line.get_value()
                encoded_signal.append(bit)
                time.sleep(1 / 44100)  # Adjust timing based on your requirements

            # CVSD Demodulation
            decoded_audio = cvsd_demodulate(encoded_signal)

            with decoded_audio_lock:
                decoded_audio_shared = decoded_audio

    except KeyboardInterrupt:
        pass
    finally:
        line.release()

def audio_output_thread(rate=44100, channels=1):
    global decoded_audio_shared
    p = pyaudio.PyAudio()
    output_stream = p.open(format=pyaudio.paInt16,
                           channels=channels,
                           rate=rate,
                           output=True)

    try:
        while True:
            with decoded_audio_lock:
                if decoded_audio_shared is not None:
                    decoded_audio = decoded_audio_shared.copy()
                else:
                    decoded_audio = None

            if decoded_audio is not None:
                output_stream.write(decoded_audio.tobytes())

    except KeyboardInterrupt:
        pass
    finally:
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

# Utilisation du script
threading.Thread(target=gpio_input_thread).start()
threading.Thread(target=audio_output_thread).start()

print("Réception et lecture du signal en cours...")
