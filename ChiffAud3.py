#!/usr/bin/env python3
"""
SIMULATEUR DE CHIFFREUR FAIT EN JUILLET 2024 PAR JONASZ SANGLIER A THALES GENNEVILLIERS

Matplotlib et NumPy doivent être installés.
"""
import argparse
import queue
import sys
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd #type: ignore

from scipy.signal import butter, lfilter
from matplotlib.animation import FuncAnimation


def int_or_str(text):
    """Convertit une chaîne en entier sinon renvoie la chaîne telle quelle."""
    try:
        return int(text)
    except ValueError:
        return text

# Création du parser d'arguments pour afficher les périphériques audio disponibles
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='affiche la liste des périphériques audio et quitte')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)

# Ajout des arguments au parser principal
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'channels', type=int, default=[1], nargs='*', metavar='CHANNEL',
    help='input channels to plot (default: the first)')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-w', '--window', type=float, default=200, metavar='DURATION',
    help='visible time slot (default: %(default)s ms)')
parser.add_argument(
    '-i', '--interval', type=float, default=30,
    help='minimum time between plot updates (default: %(default)s ms)')
parser.add_argument(
    '-b', '--blocksize', type=int, help='block size (in samples)')
parser.add_argument(
    '-r', '--samplerate', type=float, default=16000.0, help='sampling rate of audio device')
parser.add_argument(
    '-n', '--downsample', type=int, default=1, metavar='N',
    help='display every Nth sample (default: %(default)s)')
args = parser.parse_args(remaining)
if any(c < 1 for c in args.channels):
    parser.error('argument CHANNEL: must be >= 1')
mapping = [c - 1 for c in args.channels]  # Les numéros de canal commencent à 1
q = queue.Queue()  # création de file d'attente

def audio_callback(indata, frames, time, status):
    """Cette fonction est appelée (à partir d'un thread séparé) pour chaque bloc audio."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata[::args.downsample, mapping])

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

def cvsd_demodulate(encoded, delta_init=0.2, mu=1.5):
    delta = delta_init
    estimate = 0
    decoded = []
    for i, bit in enumerate(encoded):
        if bit == 1:
            estimate += delta
        else:
            estimate -= delta

        decoded.append(estimate)

        if i >= 1 and encoded[i] == encoded[i-1]:
            delta *= mu
        else:
            delta /= mu

    return np.array(decoded)

def nrz_encode(data):
    """Encodage NRZ simple."""
    return np.where(data > 0.5, 1, -1)

def nrz_decode(data):
    """Décodage NRZ simple."""
    return np.where(data > 0, 1, 0)

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def update_plot(frame):
    global plotdata, plotdata_mod, plotdata_nrz, plotdata_nrz_decoded, plotdata_demod
    while True:
        try:
            data = q.get_nowait()
        except queue.Empty:
            break
        
        shift = len(data)
        plotdata = np.roll(plotdata, -shift, axis=0)
        plotdata[-shift:, :] = data

        # Modulation CVSD
        mod_data = cvsd_modulate(data.flatten())
        mod_data = np.array(mod_data).reshape(-1, len(args.channels))
        plotdata_mod = np.roll(plotdata_mod, -shift, axis=0)
        plotdata_mod[-shift:, :] = mod_data

        # Codage NRZ du signal audio modulé
        nrz_data = nrz_encode(mod_data)
        plotdata_nrz = np.roll(plotdata_nrz, -shift, axis=0)
        plotdata_nrz[-shift:, :] = nrz_data

        # Décodage NRZ
        nrz_decoded_data = nrz_decode(nrz_data)
        plotdata_nrz_decoded = np.roll(plotdata_nrz_decoded, -shift, axis=0)
        plotdata_nrz_decoded[-shift:, :] = nrz_decoded_data

        # Démodulation CVSD
        demod_data = cvsd_demodulate(nrz_decoded_data.flatten())
        demod_data = demod_data.reshape(-1, len(args.channels))

        # Application du filtre passe-bas
        cutoff_frequency = 7999.0  # fréquence de coupure en Hz, à ajuster selon tes besoins
        demod_data = lowpass_filter(demod_data, cutoff_frequency, args.samplerate)

        plotdata_demod = np.roll(plotdata_demod, -shift, axis=0)
        plotdata_demod[-shift:, :] = demod_data

    for column, (line, line_mod, line_nrz, line_nrz_dec, line_demod) in enumerate(zip(lines, lines_mod, lines_nrz, lines_nrz_decoded, lines_demod)):
        line.set_ydata(plotdata[:, column])
        line_mod.set_ydata(plotdata_mod[:, column])
        line_nrz.set_ydata(plotdata_nrz[:, column])
        line_nrz_dec.set_ydata(plotdata_nrz_decoded[:, column])
        line_demod.set_ydata(plotdata_demod[:, column])
    return lines + lines_mod + lines_nrz + lines_nrz_decoded + lines_demod


try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']

    length = int(args.window * args.samplerate / (1000 * args.downsample))
    plotdata = np.zeros((length, len(args.channels)))
    plotdata_mod = np.zeros((length, len(args.channels)))
    plotdata_nrz = np.zeros((length, len(args.channels)))
    plotdata_nrz_decoded = np.zeros((length, len(args.channels)))
    plotdata_demod = np.zeros((length, len(args.channels)))

    fig, axs = plt.subplots(5, 1, sharex=True)
    lines = axs[0].plot(plotdata)
    lines_mod = axs[1].plot(plotdata_mod)
    lines_nrz = axs[2].plot(plotdata_nrz)
    lines_nrz_decoded = axs[3].plot(plotdata_nrz_decoded)
    lines_demod = axs[4].plot(plotdata_demod)

    axs[0].set_title('Signal Audio Original')
    axs[0].set_ylim(ymin=-1.2, ymax=1.2)

    axs[1].set_title('Signal Modulé CVSD')
    axs[1].set_ylim(ymin=-0.2, ymax=1.2)

    axs[2].set_title('Signal Codé en NRZ')
    axs[2].set_ylim(ymin=-1.2, ymax=1.2)

    axs[3].set_title('Signal Décodé en NRZ')
    axs[3].set_ylim(ymin=-0.2, ymax=1.2)

    axs[4].set_title('Signal Démodulé CVSD')
    axs[4].set_ylim(ymin=-1.2, ymax=1.2)

    fig.tight_layout(pad=0.5)

    stream = sd.InputStream(
        device=args.device, channels=max(args.channels),
        samplerate=args.samplerate, callback=audio_callback)
    ani = FuncAnimation(fig, update_plot, interval=args.interval, blit=True)
    with stream:
        plt.show()
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
