# Finds the direction of origin from audio input from the respeaker hat
# Used by RedBrick in the segmentation library for turning left/right
# Mostly set up for the respeaker
# Based upon code from here:
# https://github.com/respeaker/mic_array
# Adapted by Angus Wallis 2020-2021

import pyaudio
import wave
import numpy as np
import math
from gcc_phat import gcc_phat
from time import sleep
from blinkt import set_pixel, show, set_all
import random
import time

pyaudio_instance = pyaudio.PyAudio()

SOUND_SPEED = 343.2

MIC_DISTANCE_6P1 = 0.064
MAX_TDOA_6P1 = MIC_DISTANCE_6P1 / float(SOUND_SPEED)

MIC_DISTANCE_4 = 0.08127
MAX_TDOA_4 = MIC_DISTANCE_4 / float(SOUND_SPEED)

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 4
RESPEAKER_WIDTH = 2

# run getDeviceInfo.py to get index
for i in range(pyaudio_instance.get_device_count()):
    dev = pyaudio_instance.get_device_info_by_index(i)
    name = dev['name'].encode('utf-8')
    print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])
    if dev['maxInputChannels'] == RESPEAKER_CHANNELS:
        print('Use {}'.format(name))
        device_index = i
        break
RESPEAKER_INDEX = device_index  # refer to input device id
CHUNK = int(16000/4)

p = pyaudio.PyAudio()


frames = []

def read_chunks(data):
    data = np.fromstring(data, dtype='int16')
    print('data', data)
    return data

def flash(side):
    if side > 5:
        side = 'left'
    else:
        side = 'right'
    return side

def guess(buf):
    MIC_GROUP_N = 2
    MIC_GROUP = [[0, 2], [1, 3]]

    tau = [0] * MIC_GROUP_N
    theta = [0] * MIC_GROUP_N
    for i, v in enumerate(MIC_GROUP):
        tau[i], _ = gcc_phat(buf[v[0]::4], buf[v[1]::4], fs=RESPEAKER_RATE, max_tau=MAX_TDOA_4, interp=1)
        theta[i] = math.asin(tau[i] / MAX_TDOA_4) * 180 / math.pi

    if np.abs(theta[0]) < np.abs(theta[1]):
        if theta[1] > 0:
            best_guess = (theta[0] + 360) % 360
        else:
            best_guess = (180 - theta[0])
    else:
        if theta[0] < 0:
            best_guess = (theta[1] + 360) % 360
        else:
            best_guess = (180 - theta[1])

        best_guess = (best_guess + 90 + 180) % 360

    best_guess = (-best_guess + 120) % 360

    return best_guess

def get_direc():
    guesses = []
    while guesses.count(best_guess) < 2:
        data = stream.read(CHUNK)
        data = read_chunks(data)
        best_guess = guess(data)
        best_guess = int(best_guess/30)
        guesses.append(best_guess)
    return best_guess

def get_side(q, stop):
    stream = p.open(
                rate=RESPEAKER_RATE,
                format=p.get_format_from_width(RESPEAKER_WIDTH),
                channels=RESPEAKER_CHANNELS,
                input=True,
                input_device_index=RESPEAKER_INDEX,)
    while True:
        data = stream.read(CHUNK)
        data = read_chunks(data)
        best_guess = guess(data)
        side = int(best_guess/30)
        side = flash(side)
        q.put(side)
        print(side)
        if stop():
            break
    stream.stop_stream()
    stream.close()
    return