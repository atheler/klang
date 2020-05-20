"""Audio file demo."""
import io
import pkgutil

from klang.audio.effects import (
    Delay, Tremolo, Filter, Transformer, StereoDelay, Bitcrusher, Subsampler
)
from klang.audio.klanggeber import Dac
from klang.audio.oscillators import Lfo
from klang.audio.sampling import AudioFile
from klang.audio.waves import triangle, square
from klang.constants import STEREO
from klang.klang import run_klang


def load_audio_file():
    """Load gong audio sample from package resources."""
    raw = pkgutil.get_data('klang.audio', 'samples/gong.wav')
    return io.BytesIO(raw)


if __name__ == '__main__':
    # Init blocks
    audioFile = AudioFile(load_audio_file(), playbackSpeed=.75, loop=True)
    audioFile.sample.trim(0, 44100)
    audioFile.play()

    tremolo = Tremolo(rate=1 / .2, wave_func=square)
    delay = StereoDelay(leftTime=1.5, rightTime=1.3, leftFeedback=.9, rightFeedback=.9, drywet=.5)
    filter_ = Filter()
    lfo = Lfo(frequency=.2, wave_func=triangle)
    scaler = Transformer.from_limits(100, 2000)
    dac = Dac(nChannels=STEREO)

    # Define block network
    lfo | scaler | filter_.frequency
    audioFile | tremolo | filter_ | delay | dac
    run_klang(dac)
