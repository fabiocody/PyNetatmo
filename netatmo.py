#!/usr/bin/env python3

import os
import requests
import json
import logging
import shutil

__version__ = '0.0.1'

logger = logging.getLogger('netatmo')
HOME = os.getenv('HOME') + '/'


class NetatmoError(Exception):
    pass


class APIError(NetatmoError):

    def __init__(self, message=None):
        self.message = message


class Netatmo:

    def __init__(self, log_level):
        logging.basicConfig(
            format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, log_level))
        try:
            with open(HOME + '.pynetatmo.conf', 'r') as f:
                conf = json.load(f)
                logger.debug('Configuration loaded')
        except FileNotFoundError:
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
            raise APIError(error.response.text)


class Thermostat(Netatmo):

    def __init__(self, device_id, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.device_id = device_id
        self.get_thermostats_data()      # Test call to check if device_id is valid
        logger.debug('Thermostat.__init__ completed')

    def get_thermostats_data(self):
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
            raise APIError(error.response.text)

    def get_module_ids(self):
        logger.debug('Getting modules\' id...')
        data = self.get_thermostats_data()
        modules_ids = list()
        for device in data['devices']:
            if device['_id'] == self.device_id:
                for module in device['modules']:
                    modules_ids.append(module['_id'])
        return modules_ids

    def get_current_temperatures(self):
        logger.debug('Getting current temperatures...')
        thermostat_data = self.get_thermostats_data()
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
                raise APIError(error.response.text)
        else:
            logger.error('Invalid choice for setpoint_mode. Choose from ' +
                         str(allowed_setpoint_modes))


class Weather(Netatmo):
    pass


class Security(Netatmo):

    class _NoDevice(NetatmoError):
        pass

    def __init__(self, name, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.name = name
        self.home_id, self.place = self._get_home_info()

    def _get_home_info(self):
        logger.debug('Getting home info (home_id, place)...')
        data = self.get_home_data()
        return (data['id'], data['place'])

    def get_home_data(self, size=15, home_id=None):
        logger.debug('Getting home data...')
        params = {
            'access_token': self.access_token,
            'home_id': home_id,
            'size': size
        }
        try:
            response = requests.post('https://api.netatmo.com/api/gethomedata', params=params)
            response.raise_for_status()
            data = response.json()['body']['homes']
            logger.debug('Request completed')
            data = [h for h in data if h['name'] == self.name]
            if len(data) == 0:
                raise self._NoDevice('No device with the name provided')
            return data[0]
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def get_cameras(self):
        data = self.get_home_data()
        return data['cameras']

    def get_events(self, numbers_of_events):
        data = self.get_home_data(numbers_of_events)
        return data['events']

    def get_camera_picture(self, event):
        if type(event) is not dict:
            raise TypeError('The input must be a dict containg an event')
        if event['type'] not in ['movement']:
            raise TypeError('The input must be a movement. Only movements have related screenshot')
        logger.debug('Getting event related image...')
        params = {
            'image_id': event['snapshot']['id'],
            'key': event['snapshot']['key']
        }
        try:
            #to be implemented
            response = requests.post('https://api.netatmo.com/api/getcamerapicture', params=params)
            response.raise_for_status()
            data = response
            logger.debug('Request completed')
            return data
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)    
