#!/usr/bin/env python3
"""Klang installation script."""
import os
from setuptools import setup, find_packages, Extension

import numpy

import klang


ENVELOPE_EXT = Extension(
    name='klang.audio._envelope',
    sources=['klang/audio/_envelope.c'],
    include_dirs=[numpy.get_include()],
)
"""Extension: C ADSR envelope generator."""

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()


def listdir(directory):
    """Same as os.listdir but with full path."""
    return [
        os.path.join(directory, fn) for fn in os.listdir(directory)
    ]


setup(
    author='Alexander Theler',
    classifiers=[ 'Development Status :: 3 - Alpha', 'Environment :: Console', 'Intended Audience :: Developers', 'Intended Audience :: Education', 'Intended Audience :: End Users/Desktop', 'Operating System :: MacOS', 'Operating System :: POSIX :: Linux', 'Operating System :: Unix', 'Programming Language :: C', 'Programming Language :: Python :: 3', 'Programming Language :: Python :: 3 :: Only', 'Topic :: Multimedia :: Sound/Audio', 'Topic :: Multimedia :: Sound/Audio :: Editors', 'Topic :: Multimedia :: Sound/Audio :: MIDI', 'Topic :: Multimedia :: Sound/Audio :: Mixers', 'Topic :: Multimedia :: Sound/Audio :: Players', 'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis', ],
    description='Block based synthesis and music library',
    ext_modules=[ENVELOPE_EXT],
    include_package_data=True,
    install_requires=[ 'numpy', 'scipy', 'matplotlib', 'PyAudio', 'pynput', 'samplerate', 'beautifulsoup4', 'python-rtmidi', ],
    keywords='synthesis music library',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    name='klang',
    package_data={ 'klang.audio': ['samples/gong.wav'], 'klang.music': ['data/*.csv'], },
    packages=find_packages(),
    python_requires='>=3.0',  #?
    test_suite='tests',
    url='https://github.com/atheler/klang',
    version=klang.__version__,
)
