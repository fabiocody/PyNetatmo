#!/usr/bin/env python3

import os
import requests
import json
import logging
from io import BytesIO
from PIL import Image


__version__ = '0.0.3'

logger = logging.getLogger('netatmo')
HOME = os.getenv('HOME') + '/'




#######################
#  MODULE EXCEPTIONS  #
#######################


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


class ConfigError(NetatmoError):

    def __init__(self, error):
        if error == 'file':
            self.message = 'Could not find .pynetatmo.conf in your home directory'
        elif error == 'key':
            self.message = 'Your configuration file appears to be invalid. Please check {}.pynetatmo.conf'.format(HOME)
        else:
            self.message = None
        NetatmoError.__init__(self, self.message)




########################
#  NETATMO BASE CLASS  #
########################


class Netatmo(object):

    def __init__(self, log_level):
        logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, log_level))
        try:
            with open(HOME + '.pynetatmo.conf', 'r') as f:
                conf = json.load(f)
                logger.debug('Configuration loaded')
        except FileNotFoundError:
            raise ConfigError('file')
        try:
            auth_dict = self.auth(conf['user'], conf['password'],
                                  conf['client_id'], conf['client_secret'], conf['scope'])
        except KeyError:
            raise ConfigError('key')
        self.access_token = auth_dict['access_token']
        self.refresh_token = auth_dict['refresh_token']
        self.scope = auth_dict['scope']
        logger.debug('Netatmo.__init__ completed')

    def __str__(self):
        string = '••Netatmo Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string

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




####################
#  THERMOSTAT API  #
####################


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

    def __str__(self):
        string = '••Netatmo Thermostat Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string


    def get_thermostats_data(self):
        logger.debug('Getting thermostat data...')
        params = {
            'access_token': self.access_token,
            'device_id': self.device_id
        }
        try:
            response = requests.post('https://api.netatmo.com/api/getthermostatsdata', params=params)
            response.raise_for_status()
            logger.debug('Request completed')
            return response.json()['body']
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def get_module_ids(self):
        logger.debug('Getting modules\' id...')
        modules_ids = list()
        for device in self.get_thermostats_data()['devices']:
            if device['_id'] == self.device_id:
                for module in device['modules']:
                    modules_ids.append(module['_id'])
        return modules_ids

    def get_current_temperatures(self):
        logger.debug('Getting current temperatures...')
        data = {'temp': [], 'setpoint_temp': []}
        for device in self.get_thermostats_data()['devices']:
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
                logger.debug('Request completed')
            except requests.exceptions.HTTPError as error:
                raise APIError(error.response.text)
        else:
            logger.error('Invalid choice for setpoint_mode. Choose from ' +
                         str(allowed_setpoint_modes))
            return False

    def switch_schedule(self, module_id, schedule_id):
        logger.debug('Switching schedule...')
        params = {
            'access_token': self.access_token,
            'device_id': self.device_id,
            'module_id': module_id,
            'schedule_id': schedule_id
        }
        try:
            response = requests.get('https://api.netatmo.com/api/switchschedule', params=params)
            response.raise_for_status()
            logger.debug('Request completed')
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def create_new_schedule(self, module_id, zones, timetable, name):
        logger.debug('Creating new schedule...')
        params = {
            'access-token': self.access_token,
            'device_id': self.device_id,
            'module_id': module_id,
            'zones': zones,
            'timetable': timetable,
            'name': name
        }
        try:
            response = requests.get('https://api.netatmo.com/api/createnewschedule', params=params)
            response.raise_for_status()
            logger.debug('Request completed')
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def sync_schedule(self, module_id, zones, timetable):
        logger.debug('Creating new schedule...')
        params = {
            'access-token': self.access_token,
            'device_id': self.device_id,
            'module_id': module_id,
            'zones': zones,
            'timetable': timetable
        }
        try:
            response = requests.get('https://api.netatmo.com/api/syncschedule', params=params)
            response.raise_for_status()
            logger.debug('Request completed')
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)




#################
#  WEATHER API  #
#################


class Weather(Netatmo):

    def __init__(self, device_id=None, get_favorites=False, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.class_scope = ['read_station']
        for scope in self.class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
        self.device_id = device_id
        self.get_favorites = get_favorites
        self.stations = [self.Station(device) for device in self.get_stations_data()['body']['devices']]
        self.my_stations = [station for station in self.stations if station.id == self.device_id]
        logger.debug('Weather.__init__ completed')

    def __str__(self):
        string = '••Netatmo Weather Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string


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
            logger.debug('Request completed')
            return response.json()
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


    class Station(object):

        def __init__(self, raw_data):
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

        def __str__(self):
            string = '••Netatmo Weather.Station Object••\n\n'
            for k in self.__dict__:
                if k != 'raw_data':
                    string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
            return string





##################
#  SECURITY API  #
##################


class Security(Netatmo):

    class _NoDevice(NetatmoError):

        def __init__(self, message=None):
            NetatmoError.__init__(self, message)


    class Camera(object):

        def __init__(self, source_dictionary):
            self.__dict__.update(source_dictionary)

        def __str__(self):
            string = '••Netatmo Secutiry.Camera Object••\n\n'
            for k in self.__dict__:
                string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
            return string


    class Person(object):

        def __init__(self, source_dictionary):
            self.__dict__.update(source_dictionary)

        def __str__(self):
            string = '••Netatmo Security.Person Object••\n\n'
            for k in self.__dict__:
                string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
            return string

    class Event(object):

        def __init__(self, source_dictionary):
            self.__dict__.update(source_dictionary)

        def __str__(self):
            string = '••Netatmo Security.Event Object••\n\n'
            for k in self.__dict__:
                string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
            return string


    def __init__(self, name, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.class_scope = ['read_camera', 'access_camera', 'write_camera']
        for scope in self.class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
        self.name = name
        self.home_id, self.place = self._get_home_info()

    def __str__(self):
        string = '••Netatmo Security Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string


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
        return [self.Camera(c) for c in self.get_home_data()['cameras']]

    def get_events(self, numbers_of_events=15):
        return [self.Event(e) for e in self.get_home_data(numbers_of_events)['events']]

    def get_persons(self, name=None):
        if name != None:
            return [self.Person(c) for c in self.get_home_data()['persons'] if 'pseudo' in c.keys() and c['pseudo'] == name][0]
        return [self.Person(c) for c in self.get_home_data()['persons']]

    def get_camera_picture(self, event, show=False):
        if type(event) == Security.Event:
            if event.type not in ['movement', 'person']:
                raise TypeError('The input event must be a movement or a \'person seen event\'. Only these have related screenshots')
        if type(event) not in [Security.Event, Security.Person]:
            raise TypeError('The input must be an event or a person object')
        logger.debug('Getting event related image...')
        try:
            base_url = 'https://api.netatmo.com/api/getcamerapicture?'
            try:
                url = base_url + 'image_id=' + str(event.snapshot['id']) + '&key=' + str(event.snapshot['key'])
            except AttributeError:
                url = base_url + 'image_id=' + str(event.face['id']) + '&key=' + str(event.face['key'])
            response = requests.get(url)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            logger.debug('Request completed')
            if show == True:
                img.show()
            return img
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def get_events_until(self, event):
        if type(event) is not Security.Event:
            raise TypeError('Input must be an event obj')
        logger.debug('Getting events')
        params = {
            'access_token': self.access_token,
            'home_id': self.home_id,
            'event_id': event.id
        }
        try:
            response = requests.post('https://api.netatmo.com/api/geteventsuntil', params=params)
            response.raise_for_status()
            data = response.json()['body']['events_list']
            return [self.Event(e) for e in data]
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def set_person_away(self, person=None):
        if type(person) not in [Security.Person, None]:
            raise TypeError('The input must be a Security.Person object or None if you want to set all people away')
        params = {
            'access_token': self.access_token,
            'home_id': self.home_id
        }
        if person != None:
            params.update({'person_id': person.id})
        logger.debug('Setting person status...')
        try:
            response = requests.post('https://api.netatmo.com/api/setpersonsaway', params=params)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)
