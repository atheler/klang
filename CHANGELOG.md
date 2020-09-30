# Changelog

## [0.2.0] - 2020-09-30

### Added
- More examples
- New effects: Reverb, RingModulator
- Python fallback for envelopes
- Ring buffer based filters as C extension and with Python fallback
- `run_audio_engine(...)` with duration, fadeout and offline bouncing.
- PwmOscillator
- Some type hinting
- Possible to pipe from `OutputBase`
- Some new note effects

### Changed
- Sequencer with grid argument, playback speed independent of pattern length,
  support for different length sequences, single output mode
- Lfo with outputRange (instead of prepending Trafo blocks everywhere)
- Arpeggiator and Arpeggio (simplified, random pattern stay constant as long as there are no new note)
- RingBuffer
- Tremolo effect with smoothness and duty cycle

### Removed
