"""Audio file demo.

Some noisy ambient sound from a slightly pitched down gong sample and stereo
delay / filtering.
"""
import io
import pkgutil

from klang.audio import (
    Dac, Lfo, Tremolo, Filter, StereoDelay, AudioFile, triangle
)
from klang.constants import STEREO
from klang.klang import run_klang


def load_audio_file():
    """Load gong audio sample from package resources."""
    raw = pkgutil.get_data('klang.audio', 'samples/gong.wav')
    return io.BytesIO(raw)


# Initialize blocks
audioFile = AudioFile(load_audio_file(), playbackSpeed=.75, loop=True)
audioFile.sample.trim(0, 44100)  # Loop one second of audio
audioFile.play()
tremolo = Tremolo(rate=1 / .2, smoothness=.1)
delay = StereoDelay(leftTime=1.5, rightTime=1.3, leftFeedback=.9, rightFeedback=.9, drywet=.5)
filter_ = Filter()
lfo = Lfo(frequency=.2, wave_func=triangle, outputRange=(100, 2000))
dac = Dac(nChannels=STEREO)

# Define network
lfo | filter_.frequency
audioFile | tremolo | filter_ | delay | dac

if __name__ == '__main__':
    run_klang(dac)
