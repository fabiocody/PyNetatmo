#!/usr/bin/env python3

from setuptools import setup
from os import path, getenv
import json
from getpass import getpass

HERE = path.abspath(path.dirname(__file__))
HOME = getenv('HOME')

try:
    with open(path.join(HERE, 'README.md')) as f:
        long_description = f.read()
except:
    long_description = ''

try:
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
finally:
    print()
    try:
        with open(path.join(HOME, '.pynetatmo.conf')) as f:
            conf = json.load(f)
            print('Configuration file already exists')
    except FileNotFoundError:
        configure = input('Would you like to be guided through the configuration steps (otherwise you will have to create the JSON file on your own)? [y/n] ')
        if configure == 'y' or configure == 'Y':
            with open(path.join(HOME, '.pynetatmo.conf'), 'w') as f:
                conf = dict()
                conf['user'] = input('User: ')
                conf['password'] = getpass()
                conf['client_id'] = input('Client ID: ')
                conf['client_secret'] = input('Client Secret: ')
                conf['scope'] = input('Scope: ')
                json.dump(conf, f, indent=4)
                print('Configuration file created.')
        else:
            print('Aborted. Please reed the docs to know what to do now.')
