from klang.audio.sampling import AudioFile
from klang.audio.effects import Delay, Tremolo, Filter, Transformer
from klang.audio.klanggeber import KlangGeber
from klang.audio.oscillators import Lfo
from klang.audio.waves import triangle

#FILEPATH = '/Users/sasha/Downloads/file_example_WAV_1MG.wav'
FILEPATH = '/Users/sasha/Downloads/a2002011001-e02.wav'

audioFile = AudioFile(FILEPATH, playbackSpeed=.25, loop=True)
#audioFile = AudioFile(FILEPATH, playbackSpeed=1.00)
#audioFile = AudioFile(FILEPATH, mode='crude')
#audioFile = AudioFile(FILEPATH, loop=True)


#audioFile.sample.trim(8500, 24420)
audioFile.sample.trim(0, 35000)
audioFile.play()
delay = Delay()
tremolo = Tremolo()
filter_ = Filter()

#subsampler = Subsampler(16)
#fx = Bitcrusher(nBits=11)
#fx = Delay(delay=.001, feedback=.7, drywet=.7)
#fx = tremolo
delay = Delay(delay=.8, feedback=.9, drywet=.5)


lfo = Lfo(frequency=.1, shape=1, wave_func=triangle)
#lfo.output.connect(fx.intensity)


#scaler = Transformer(scale=5000., offset=200.)
scaler = Transformer.from_limits(100, 2000)
lfo.output.connect(scaler.input)
scaler.output.connect(filter_.frequency)


audioFile.output.connect(delay.input)
delay.output.connect(filter_.input)


if __name__ == '__main__':
    with KlangGeber(nOutputs=1, filepath='filter_sweep.wav') as dac:
        #audioFile.output.connect(delay.input)
        #delay.output.connect(tremolo.input)
        #tremolo.output.connect(dac.input)
        #audioFile.output.connect(dac.input)
        #fx.output.connect(dac.input)
        #subsampler.output.connect(dac.input)

        filter_.output.connect(dac.input)
