# PyNetatmo [![Build Status](https://travis-ci.org/fabiocody/PyNetatmo.svg?branch=master)](https://travis-ci.org/fabiocody/PyNetatmo)
Netatmo SmartHome API wrapper written in Python

This wrapper is still under active development.

## Configuration
In order to use this API wrapper you have to put in your home directory a file named `.pynetatmo.conf`. Here's an example of how it should look like.
``` json
{
    "user": "E-MAIL",
    "password": "PASSWORD",
    "client_id": "CLIENT-ID RETRIEVED FROM dev.netatmo.com",
    "client_secret": "CLIENT-SECRET RETRIEVED FROM dev.netatmo.com",
    "scope": "SPACE-SEPARATED SCOPES (e.g. read_thermostat write_thermostat')"
}
```
You can find the available scopes and more information on [dev.netatmo.com](https://dev.netatmo.com/dev/resources/technical/reference/smarthomeapi).

## Credits
I would like to thank [Alessandro Nichelini](https://github.com/Alenichel) for writing the `Welcome` class.
