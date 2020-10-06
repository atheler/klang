#!/usr/bin/env python3
"""Klang installation script."""
import os
import sys
from setuptools import setup, find_packages, Extension

import numpy

import klang


INCLUDE_DIRS = ['/usr/local/include', '/usr/include', '/opt/include']
"""list: Include directories to check for library header files."""


def library_exists(library):
    """Check if C/C++ library is installed.

    Args:
        library (str): Header file to check.

    Returns:
        bool: Found library in INCLUDE_DIRS.
    """
    for directory in INCLUDE_DIRS:
        try:
            if library in os.listdir(directory):
                return True
        except FileNotFoundError:
            pass

    return False


if sys.version_info < (3, 0):
    raise SystemExit('Sorry, only Python 3 supported!')


if not library_exists('portaudio.h'):
    fmt = ('Portaudio seems not to be installed! Looked in the following'
           ' directories:\n%s')
    msg = fmt % '\n'.join('  ' + directory for directory in INCLUDE_DIRS)
    raise SystemExit(msg)


with open('README.rst', 'r') as fh:
    LONG_DESCRIPTION = fh.read()


KWARGS = dict(
    author='Alexander Theler',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: C',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Editors',
        'Topic :: Multimedia :: Sound/Audio :: MIDI',
        'Topic :: Multimedia :: Sound/Audio :: Mixers',
        'Topic :: Multimedia :: Sound/Audio :: Players',
        'Topic :: Multimedia :: Sound/Audio :: Sound Synthesis',
    ],
    description='Block based synthesis and music library',
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'PyAudio',
        'pynput',
        'samplerate',
        'requests',
        'beautifulsoup4',
        'python-rtmidi',
    ],
    keywords='synthesis music library',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    name='klang',
    package_data={
        'klang.audio': ['samples/gong.wav'],
        'klang.music': ['data/*.csv'],
    },
    packages=find_packages(),
    python_requires='>=3.0',  #TODO: ?
    test_suite='tests',
    url='https://github.com/atheler/klang',
    version=klang.__version__,
)


if __name__ == '__main__':
    try:
        setup(ext_modules=[
            Extension(
                name='klang.audio._envelope',
                sources=['klang/audio/_envelope.c'],
                include_dirs=[numpy.get_include()],
            ),
            Extension(
                name='klang.audio._filters',
                sources=['klang/audio/_filters.c'],
                include_dirs=[numpy.get_include()],
            ),
        ], **KWARGS)
    except SystemExit as err:
        print(err)
        print('Failed to built C-extensions. Continuing with pure Python fallback')
        setup(**KWARGS)
