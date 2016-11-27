#!/usr/bin/env python3

import os
import requests
import json
import logging


__version__ = '0.0.1'

logger = logging.getLogger('netatmo')
HOME = os.getenv('HOME') + '/'


class Netatmo:

    def __init__(self, log_level):
        logging.basicConfig(
            format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, log_level))
        try:
            with open(HOME + '.pynetatmo.conf', 'r') as f:
                conf = json.load(f)
                logger.debug('Configuration loaded')
        except:
            logger.error('Could not find ~/.pynetatmo.conf')
            exit(1)
        auth_dict = self.auth(conf['user'], conf['password'], conf[
                              'client_id'], conf['client_secret'], conf['scope'])
        self.access_token = auth_dict['access_token']
        self.refresh_token = auth_dict['refresh_token']
        self.scope = auth_dict['scope']
        logger.debug('Netatmo.__init__ completed')

    def auth(self, user, password, client_id, client_secret, scope, verbose=False):
        logger.debug('Authorizing...')
        payload = {
            'grant_type': 'password',
            'username': user,
            'password': password,
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': scope
        }
        try:
            response = requests.post('https://api.netatmo.com/oauth2/token', data=payload)
            response.raise_for_status()
            access_token = response.json()['access_token']
            refresh_token = response.json()['refresh_token']
            scope = response.json()['scope']
            if verbose:
                print('Your access token is:', access_token)
                print('Your refresh token is:', refresh_token)
                print('Your scopes are:', scope)
            logger.debug('Authorization completed')
            return {'access_token': access_token, 'refresh_token': refresh_token, 'scope': scope}
        except requests.exceptions.HTTPError as error:
            logger.error(error.response.status_code + ' ' + error.response.text)


class Thermostat(Netatmo):

    def __init__(self, device_id, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.device_id = device_id
        logger.debug('Thermostat.__init__ completed')

    def get_thermostat_data(self):
        logger.debug('Getting thermostat data...')
        params = {
            'access_token': self.access_token,
            'device_id': self.device_id
        }
        try:
            response = requests.post(
                'https://api.netatmo.com/api/getthermostatsdata', params=params)
            response.raise_for_status()
            logger.debug('Request completed')
            return response.json()['body']
        except requests.exceptions.HTTPError as error:
            logger.error(error.response.status_code + ' ' + error.response.text)

    def get_module_ids(self):
        logger.debug('Getting modules\' id...')
        data = self.get_thermostat_data()
        modules_ids = list()
        for device in data['devices']:
            if device['_id'] == self.device_id:
                for module in device['modules']:
                    modules_ids.append(module['_id'])
        return modules_ids

    def get_current_temperatures(self):
        logger.debug('Getting current temperatures...')
        thermostat_data = self.get_thermostat_data()
        data = {'temp': [], 'setpoint_temp': []}
        for device in thermostat_data['devices']:
            if device['_id'] == self.device_id:
                for module in device['modules']:
                    data['temp'].append(module['measured']['temperature'])
                    data['setpoint_temp'].append(module['measured']['setpoint_temp'])
        return data

    def set_therm_point(self, module_id, setpoint_mode, setpoint_endtime=None, setpoint_temp=None):
        logger.debug('Setting thermal point...')
        allowed_setpoint_modes = ['program', 'away', 'hg', 'manual', 'off', 'max']
        params = {
            'access_token': self.access_token,
            'device_id': self.device_id,
            'module_id': module_id,
            'setpoint_mode': setpoint_mode,
        }
        if setpoint_endtime:
            params['setpoint_endtime'] = setpoint_endtime
        if setpoint_temp:
            params['setpoint_temp'] = setpoint_temp
        if setpoint_mode in allowed_setpoint_modes:
            try:
                response = requests.post('https://api.netatmo.com/api/setthermpoint', params=params)
                response.raise_for_status()
                data = response.json()
                logger.debug('Request completed')
                return data
            except requests.exceptions.HTTPError as error:
                logger.error(error.response.status_code + ' ' + error.response.text)
        else:
            raise RuntimeError('Invalid choice for setpoint_mode. Choose from ' + str(allowed_setpoint_modes))
