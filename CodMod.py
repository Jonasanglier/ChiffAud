import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import threading
import gpiod
import time

# Variables partagées et verrous
audio_data_shared = None
audio_data_lock = threading.Lock()

def cvsd_modulate(signal, delta_init=0.2, mu=1.5):
    encoded = []
    delta = delta_init
    estimate = 0
    for sample in signal:
        if sample > estimate:
            encoded.append(1)
            estimate += delta
        else:
            encoded.append(0)
            estimate -= delta

        if len(encoded) > 1 and encoded[-1] == encoded[-2]:
            delta *= mu
        else:
            delta /= mu
    return encoded

def audio_input_thread(device_index=0, rate=44100, channels=1, chunk_size=2048):
    global audio_data_shared
    p = pyaudio.PyAudio()
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=channels,
                          rate=rate,
                          input=True,
                          input_device_index=device_index,
                          frames_per_buffer=chunk_size)
    try:
        while True:
            data = input_stream.read(chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            with audio_data_lock:
                audio_data_shared = audio_data
    except KeyboardInterrupt:
        pass
    finally:
        input_stream.stop_stream()
        input_stream.close()
        p.terminate()

def gpio_output_thread():
    global audio_data_shared
    chip = gpiod.Chip('4')  # Use '/dev/gpiochip0' for the first GPIO controller
    line = chip.get_line(17)  # GPIO17
    line.request(consumer='cvsd_signal', type=gpiod.LINE_REQ_DIR_OUT)

    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation CVSD
                mod_data = cvsd_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Send CVSD data to GPIO
                for bit in mod_data:
                    line.set_value(bit)
                    time.sleep(1 / 44100)  # Adjust timing based on your requirements
    except KeyboardInterrupt:
        pass
    finally:
        line.release()

def plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048):
    threading.Thread(target=audio_input_thread, args=(device_index, rate, channels, chunk_size)).start()
    threading.Thread(target=gpio_output_thread).start()

    print("Affichage et traitement du signal en cours...")
    
    plt.ion()
    fig, axs = plt.subplots(2, 1, sharex=True)
    
    x = np.arange(0, 2 * chunk_size, 2)
    
    # Initial plots for each subplot
    lines = []
    for ax in axs:
        line, = ax.plot(x, np.random.rand(chunk_size))
        lines.append(line)
    
    axs[0].set_ylim(-32768, 32768)
    axs[1].set_ylim(-0.2, 1.2)
    
    axs[0].set_title('Signal Audio Original')
    axs[1].set_title('Signal Modulé CVSD')

    try:
        while True:
            with audio_data_lock:
                if audio_data_shared is not None:
                    audio_data = audio_data_shared.copy()
                else:
                    audio_data = None

            if audio_data is not None:
                # Modulation CVSD
                mod_data = cvsd_modulate(audio_data)
                mod_data = np.array(mod_data)

                # Mettre à jour les plots
                lines[0].set_ydata(audio_data)
                lines[1].set_ydata(mod_data)
                
                fig.canvas.draw()
                fig.canvas.flush_events()
    
    except KeyboardInterrupt:
        print("Affichage et traitement terminés.")
    
    finally:
        plt.ioff()
        plt.show()

# Utilisation du script
plot_audio_stream(device_index=0, rate=44100, channels=1, chunk_size=2048)
