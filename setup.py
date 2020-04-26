#!/usr/bin/env python3
"""Klang installation script."""
import os
from setuptools import setup, find_packages

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
)
