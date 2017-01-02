#!/usr/bin/env python3

from setuptools import setup
from os import path

HERE = path.abspath(path.dirname(__file__))

try:
    with open(path.join(HERE, 'README.md')) as f:
        long_description = f.read()
except:
    long_description = ''

setup(
    name='pynetatmo',
    version='0.0.18',
    description='Netatmo API wrapper written in Python',
    long_description=long_description,
    url='https://github.com/fabiocody/PyNetatmo.git',
    author='Fabio Codiglioni',
    author_email='fabiocody@icloud.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 4 - Beta'
    ],
    keywords='netatmo, thermostat, weather, security, welcome',
    py_modules=['netatmo'],
    install_requires=['pillow']
)
