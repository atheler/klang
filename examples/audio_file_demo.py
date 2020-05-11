"""Audio file demo."""
from klang.audio.effects import Delay, Tremolo, Filter, Transformer
from klang.audio.klanggeber import Dac
from klang.audio.oscillators import Lfo
from klang.audio.sampling import AudioFile
from klang.audio.waves import triangle
from klang.constants import MONO, STEREO
from klang.klang import run_klang


#FILEPATH = '/Users/sasha/Downloads/file_example_WAV_1MG.wav'
FILEPATH = '/Users/sasha/Downloads/a2002011001-e02.wav'

# Init blocks
audioFile = AudioFile(FILEPATH, playbackSpeed=.25, loop=True)
#audioFile = AudioFile(FILEPATH, playbackSpeed=1.00)
#audioFile = AudioFile(FILEPATH, mode='crude')
#audioFile = AudioFile(FILEPATH, loop=True)
#audioFile.sample.trim(8500, 24420)
audioFile.sample.trim(0, 35000)
audioFile.play()

# Some effects
tremolo = Tremolo()
delay = Delay(time=.8, feedback=.9, drywet=.5)
filter_ = Filter()
#subsampler = Subsampler(16)
#fx = Bitcrusher(nBits=11)
#fx = Delay(delay=.001, feedback=.7, drywet=.7)
#fx = tremolo
lfo = Lfo(frequency=.1, wave_func=triangle)
scaler = Transformer.from_limits(100, 2000)
dac = Dac(nChannels=MONO)


if __name__ == '__main__':
    # Define block network
    lfo | scaler | filter_.frequency
    audioFile | delay | filter_ | dac

    run_klang(dac)
