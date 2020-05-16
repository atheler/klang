#!/usr/bin/env python3
"""Klang installation script."""
import os
from setuptools import setup, find_packages, Extension
import numpy


ENVELOPE_EXT = Extension(
    'klang.audio._envelope',
    sources=['klang/audio/_envelope.c'],
    include_dirs=[numpy.get_include()],
)


setup(
    author='Alexander Theler',
    data_files=[
        ('resources', os.listdir('resources')),
    ],
    include_package_data=True,
    install_requires=[
        'numpy',
        'scipy',
        'matplotlib',
        'PyAudio',
        'pynput',
        'samplerate',
        'beautifulsoup4',
        'python-rtmidi',
    ],
    name='klang',
    packages=find_packages(),
    test_suite='tests',
    zip_safe=False,
    ext_modules=[ENVELOPE_EXT],
)
