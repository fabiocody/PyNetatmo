#!/usr/bin/env python3

from setuptools import setup
from os import path, getenv
from sys import stdin, stdout, stderr
from getpass import getpass
from subprocess import getoutput
from select import select
from platform import python_version_tuple
import json

'''
try:
    PY_VERSION = [int(i) for i in python_version_tuple()]
    if PY_VERSION[0] != 3 and PY_VERSION[1] < 4:
        print('ERROR: Python 3.4 or higher is required.\nAborted.')
        exit(1)
except:
    pass
'''

HERE = path.abspath(path.dirname(__file__))

'''
try:
    HOME = path.expanduser('~' + getoutput('who am i').split()[0])
except:
    HOME = getenv('HOME')
'''

try:
    with open(path.join(HERE, 'README.md')) as f:
        long_description = f.read()
except:
    long_description = ''

#try:
setup(
    name='pynetatmo',
    version='0.0.3',
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
        'Development Status :: 3 - Alpha'
    ],
    keywords='netatmo, thermostat',
    py_modules=['netatmo'],
    install_requires=['pillow']
)
'''
finally:
    if stdin.isatty() and stdout.isatty() and stderr.isatty():
        print()
        try:
            with open(path.join(HOME, '.pynetatmo.conf')) as f:
                conf = json.load(f)
                print('Configuration file already exists. Skipping configuration steps.')
        except FileNotFoundError:
            print('Would you like to be guided through the configuration steps (otherwise you will have to create the JSON file on your own)? [y/n] ', end='')
            i, o, e = select([stdin], [], [], 5)
            if i:
                configure = stdin.readline().strip()
            else:
                configure = 'n'
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
'''
