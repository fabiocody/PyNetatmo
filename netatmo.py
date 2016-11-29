#!/usr/bin/env python3

import os
import requests
import json
import logging
import shutil
from io import BytesIO
from PIL import Image


__version__ = '0.0.1'

logger = logging.getLogger('netatmo')
HOME = os.getenv('HOME') + '/'


class NetatmoError(Exception):

    def __init__(self, message=None):
        if message:
            Exception.__init__(self, message)
        else:
            Exception.__init__(self)


class APIError(NetatmoError):

    def __init__(self, message=None):
        NetatmoError.__init__(self, message)


class ScopeError(NetatmoError):

    def __init__(self, scope):
        self.message = 'Could not find \'' + scope + '\' in your scope'
        NetatmoError.__init__(self, self.message)


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
        self.class_scope = ['read_thermostat', 'write_thermostat']
        for scope in self.class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
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

    def __init__(self, device_id=None, get_favorites=False, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.class_scope = ['read_station']
        for scope in self.class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
        self.device_id = device_id
        self.get_favorites = get_favorites
        self.stations = [Station(device) for device in self.get_stations_data()['body']['devices']]
        self.my_stations = [station for station in self.stations if station.id == self.device_id]
        logger.debug('Weather.__init__ completed')

    def get_stations_data(self):
        logger.debug('Getting stations\' data...')
        params = {
            'access_token': self.access_token,
            'get_favorites': str(self.get_favorites).lower()
        }
        if self.device_id:
            params['device_id'] = self.device_id
        try:
            response = requests.post('https://api.netatmo.com/api/getstationsdata', params=params)
            response.raise_for_status()
            data = response.json()
            logger.debug('Request completed')
            return data
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def get_station_from_id(self, ID):
        for device in self.stations:
            if device.id == ID:
                return device
        return None

    def get_stations_from_name(self, name):
        stations = dict()
        for device in self.stations:
            if device.name == name:
                stations[name] = device
        if len(stations) == 0:
            return None
        elif len(stations) == 1:
            return stations[name]
        else:
            return stations


class Station(Netatmo):

    def __init__(self, raw_data, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.raw_data = raw_data
        self.name = raw_data['station_name']
        self.id = raw_data['_id']
        self.type = [t for module in raw_data['modules'] for t in module['data_type']]
        self.modules = self.raw_data['modules']
        for module in self.modules:
            if 'Temperature' in module['dashboard_data']:
                self.temperature = module['dashboard_data']['Temperature']
            if 'Humidity' in module['dashboard_data']:
                self.humidity = module['dashboard_data']['Humidity']
            if 'Rain' in module['dashboard_data']:
                self.rain = module['dashboard_data']['Rain']
            if 'WindStrength' in module['dashboard_data']:
                self.wind_strength = module['dashboard_data']['WindStrength']
                self.wind_angle = module['dashboard_data']['WindAngle']
        logger.debug('Station.__init__ completed')


class Security(Netatmo):

    class _NoDevice(NetatmoError):
        pass

    def __init__(self, name, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.class_scope = ['read_camera', 'access_camera']
        for scope in self.class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
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

    def get_events(self, numbers_of_events=15):
        data = self.get_home_data(numbers_of_events)
        return data['events']

    def get_camera_picture(self, event, visualize=False):
        if type(event) is not dict:
            raise TypeError('The input must be a dict containg an event')
        if event['type'] not in ['movement']:
            raise TypeError('The input must be a movement. Only movements have related screenshot')
        logger.debug('Getting event related image...')
        try:
            # to be implemented
            BASE_URL = 'https://api.netatmo.com/api/getcamerapicture?'
            URL = BASE_URL + 'image_id=' + str(event['snapshot']['id']) + '&key=' + str(event['snapshot']['key'])
            response = requests.get(URL)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            logger.debug('Request completed')
            if visualize == True:
                Image._show(img)
            return img
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)
