#!/usr/bin/env python3

import os
import requests
import json
import logging


'''
~/.pynetatmo.conf
{
    "user": "E-MAIL",
    "password": "PASSWORD",
    "client_id": "CLIENT-ID RETRIEVED FROM dev.netatmo.com",
    "client_secret": "CLIENT-SECRET RETRIEVED FROM dev.netatmo.com",
    "scope": "SPACE-SEPARATED SCOPE (e.g. "read_thermostat write_thermostat")"
}
'''


logger = logging.getLogger('netatmo')
HOME = os.getenv('HOME') + '/'


class Netatmo:

    def __init__(self, log_level='WARNING'):
        logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, log_level))
        try:
            with open(HOME + '.pynetatmo.conf', 'r') as f:
                conf = json.load(f)
        except:
            logger.error('Could not find ~/.pynetatmo.conf')
            exit(1)
        auth_dict = self.auth(conf['user'], conf['password'], conf['client_id'], conf['client_secret'], conf['scope'])
        self.access_token = auth_dict['access_token']
        self.refresh_token = auth_dict['refresh_token']
        self.scope = auth_dict['scope']

    def auth(self, user, password, client_id, client_secret, scope, verbose=False):
        payload = {
            'grant_type': 'password',
            'username': user,
            'password': password,
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': scope
        }
        try:
            response = requests.post("https://api.netatmo.com/oauth2/token", data=payload)
            response.raise_for_status()
            access_token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
            scope = response.json()["scope"]
            if verbose:
                print("Your access token is:", access_token)
                print("Your refresh token is:", refresh_token)
                print("Your scopes are:", scope)
            return {'access_token': access_token, 'refresh_token': refresh_token, 'scope': scope}
        except requests.exceptions.HTTPError as error:
            print(error.response.status_code, error.response.text)


class Thermostat(Netatmo):

    def __init__(self, device_id):
        Netatmo.__init__(self)
        self.device_id = device_id

    def get_thermostat_data(self):
        params = {
            'access_token': self.access_token,
            'device_id': self.device_id
        }
        try:
            response = requests.post("https://api.netatmo.com/api/getthermostatsdata", params=params)
            response.raise_for_status()
            data = response.json()["body"]
            return data
        except requests.exceptions.HTTPError as error:
            print(error.response.status_code, error.response.text)

    def get_current_temperature(self):
        thermostat_data = self.get_thermostat_data()
        temp = thermostat_data['devices'][0]['modules'][0]['measured']['temperature']
        return temp


if __name__ == '__main__':
    NT = Thermostat('70:ee:50:24:1b:6a')
    print(NT.get_current_temperature())
    print(json.dumps(NT.get_thermostat_data(), indent=4))
