import pyaudio
import numpy as np
import threading
import gpiod
import time
import queue
from contextlib import contextmanager

# Audio parameters
RATE = 16000  # Sampling frequency (16 kHz)
CHUNK_SIZE = 1024  # Increased chunk size for better performance

# GPIO configuration
GPIO_CHIP = 'gpiochip0'
GPIO_LINE = 18

# Shared resources
audio_queue = queue.Queue(maxsize=10)
stop_event = threading.Event()

@contextmanager
def gpio_manager():
    chip = gpiod.Chip(GPIO_CHIP)
    line = chip.get_line(GPIO_LINE)
    line.request(consumer='delta_signal', type=gpiod.LINE_REQ_DIR_OUT)
    try:
        yield line
    finally:
        line.release()

def delta_modulate(sample, last_sample):
    if sample > last_sample:
        return 1, last_sample + 1
    else:
        return 0, last_sample - 1

def audio_input_thread(device_index=0):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK_SIZE)

    try:
        while not stop_event.is_set():
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            samples = np.frombuffer(data, dtype=np.int16)
            try:
                audio_queue.put(samples, block=True, timeout=0.1)
            except queue.Full:
                print("Warning: Audio buffer full, dropping samples")
    except Exception as e:
        print(f"Error in audio capture: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def processing_thread():
    last_sample = 0
    samples_processed = 0
    last_time = time.time()

    with gpio_manager() as gpio_line:
        while not stop_event.is_set():
            try:
                samples = audio_queue.get(block=True, timeout=0.1)
                for sample in samples:
                    bit, last_sample = delta_modulate(sample, last_sample)
                    try:
                        gpio_line.set_value(bit)
                    except gpiod.LineError as e:
                        print(f"GPIO error: {e}")
                
                samples_processed += len(samples)
                current_time = time.time()
                if current_time - last_time >= 1:
                    expected_samples = RATE
                    if samples_processed < expected_samples * 0.95:
                        print("Warning: Processing is falling behind")
                    samples_processed = 0
                    last_time = current_time
            
            except queue.Empty:
                continue

def main():
    audio_thread = threading.Thread(target=audio_input_thread)
    proc_thread = threading.Thread(target=processing_thread)
    
    audio_thread.start()
    proc_thread.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping threads...")
        stop_event.set()
    
    audio_thread.join()
    proc_thread.join()
    print("Program ended.")

if __name__ == "__main__":
    main()