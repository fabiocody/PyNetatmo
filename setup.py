#!/usr/bin/env python3

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

try:
    with open(path.join(here, 'README.md')) as f:
        long_description = f.read()
except:
    long_description = ''

setup(
    name='pynetatmo',
    version='0.0.1',
    description='Netatmo API wrapper written in Python',
    long_description=long_description,
    url='https://github.com/fabiocody/PyNetatmo.git',
    author='Fabio Codiglioni',
    author_email='fabiocody@icloud.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha'
    ],
    keywords='netatmo, thermostat',
    py_modules=['netatmo']
)
