#!/usr/bin/env python3

import os
import requests
import json
import logging
from sys import exit, stdin
from io import BytesIO
from PIL import Image
from platform import python_version_tuple
from getpass import getpass
from time import time
from datetime import timedelta
from pwd import getpwall


__version__ = '0.0.18'

logger = logging.getLogger('netatmo')
logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, 'WARNING'))

PY_VERSION = [int(i) for i in python_version_tuple()]
if PY_VERSION[0] != 3 and PY_VERSION[1] < 4:
    raise RuntimeError('Python 3.4 or higher is required. Aborted')




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
            self.message = 'Your configuration file appears to be invalid. Please check {home}.pynetatmo.conf'.format(home=HOME)
        else:
            self.message = None
        NetatmoError.__init__(self, self.message)




###################
#  CONFIGURATION  #
###################

for p in getpwall():
    HOME = p.pw_dir
    try:
        CONF = None
        with open(os.path.join(HOME, '.pynetatmo.conf'), 'r') as f:
            CONF = json.load(f)
            logger.debug('Configuration loaded')
        break
    except:
        pass
if not CONF:
    HOME = os.getenv('HOME') + '/'
    configure = input('Configuration file not found.\nWould you like to be guided through the configuration steps (otherwise you will have to create the JSON file on your own)? [y/n] ')
    if configure.upper() == 'Y':
        with open(os.path.join(HOME, '.pynetatmo.conf'), 'w') as f:
            try:
                CONF = dict()
                CONF['user'] = input('User: ')
                CONF['password'] = getpass()
                CONF['client_id'] = input('Client ID: ')
                CONF['client_secret'] = input('Client Secret: ')
                CONF['scope'] = input('Scope: ')
                json.dump(CONF, f, indent=4)
                logger.debug('Configuration file created')
            except KeyboardInterrupt:
                os.remove(os.path.join(HOME, '.pynetatmo.conf'))
                logger.error('\nAborted')
                exit(1)
    else:
        logger.error('You can\'t use this module without a configuration file. Aborted')
        exit(1)




########################
#  NETATMO BASE CLASS  #
########################


class Netatmo(object):

    def __init__(self, log_level):
        logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s',  level=getattr(logging, log_level))
        self.auth()
        logger.debug('Netatmo.__init__ completed')

    @property
    def access_token(self):
        return self.__access_token

    @property
    def refresh_token(self):
        return self.__refresh_token

    @property
    def scope(self):
        return self.__scope

    def __str__(self):
        string = '••Netatmo Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string

    def auth(self):
        try:
            auth_dict = self.auth_call(CONF['user'], CONF['password'], CONF['client_id'], CONF['client_secret'], CONF['scope'])
        except KeyError:
            raise ConfigError('key')
        self.__timestamp = time()
        self.__access_token = auth_dict['access_token']
        self.__refresh_token = auth_dict['refresh_token']
        self.__scope = auth_dict['scope']

    def auth_call(self, user, password, client_id, client_secret, scope):
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
            logger.debug('Your access token is: ' + access_token)
            logger.debug('Your refresh token is: ' + refresh_token)
            logger.debug('Your scopes are: ' + str(scope))
            logger.debug('Authorization completed')
            return {'access_token': access_token, 'refresh_token': refresh_token, 'scope': scope}
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def check_token_validity(self):
        if time() - self.__timestamp < timedelta(hours=1).seconds:
            self.auth()




####################
#  THERMOSTAT API  #
####################


class Thermostat(Netatmo):

    def __init__(self, device_id, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.__class_scope = ['read_thermostat', 'write_thermostat']
        for scope in self.__class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
        self.__device_id = device_id
        self.get_thermostats_data()      # Test call to check if device_id is valid
        logger.debug('Thermostat.__init__ completed')

    @property
    def device_id(self):
        return self.__device_id

    @property
    def temperature(self):
        return self.get_thermostats_data()['devices'][0]['modules'][0]['measured']['temperature']

    @property
    def set_temperature(self):
        return self.get_thermostats_data()['devices'][0]['modules'][0]['measured']['setpoint_temp']

    @property
    def relay_cmd(self):
        return self.get_thermostats_data()['devices'][0]['modules'][0]['therm_relay_cmd']

    def __str__(self):
        string = '••Netatmo Thermostat Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string


    def get_thermostats_data(self):
        logger.debug('Getting thermostat data...')
        Netatmo.check_token_validity(self)
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

    def set_therm_point(self, module_id, setpoint_mode, setpoint_endtime=None, setpoint_temp=None):
        logger.debug('Setting thermal point...')
        allowed_setpoint_modes = ['program', 'away', 'hg', 'manual', 'off', 'max']
        Netatmo.check_token_validity(self)
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
                return response.text
            except requests.exceptions.HTTPError as error:
                raise APIError(error.response.text)
        else:
            logger.error('Invalid choice for setpoint_mode. Choose from ' +
                         str(allowed_setpoint_modes))
            return False

    def switch_schedule(self, module_id, schedule_id):
        logger.debug('Switching schedule...')
        Netatmo.check_token_validity(self)
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
            return response.text
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def create_new_schedule(self, module_id, zones, timetable, name):
        logger.debug('Creating new schedule...')
        Netatmo.check_token_validity(self)
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
            return response.text
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)

    def sync_schedule(self, module_id, zones, timetable):
        logger.debug('Creating new schedule...')
        Netatmo.check_token_validity(self)
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
            return response.text
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)




#################
#  WEATHER API  #
#################


class Weather(Netatmo):

    def __init__(self, device_id=None, get_favorites=False, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.__class_scope = ['read_station']
        for scope in self.__class_scope:
            if scope not in self.scope:
                raise ScopeError(scope)
        self.__device_id = device_id
        self.get_favorites = get_favorites
        #self.stations = [self.Station(device) for device in self.get_stations_data()['body']['devices']]
        #self.my_stations = [station for station in self.stations if station.id == self.device_id]
        logger.debug('Weather.__init__ completed')

    @property
    def stations(self):
        return [self.Station(self, device) for device in self.get_stations_data()['body']['devices']]

    @property
    def my_station(self):
        for station in self.stations:
            if station.id == self.device_id:
                return station
        return None

    @property
    def device_id(self):
        return self.__device_id

    def __str__(self):
        string = '••Netatmo Weather Object••\n\n'
        for k in self.__dict__:
            string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
        return string


    def get_stations_data(self):
        logger.debug('Getting stations\' data...')
        Netatmo.check_token_validity(self)
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

        def __init__(self, weather, raw_data):
            self.__weather = weather    # Weather class that created the current Station instance
            self.__raw_data = raw_data
            self.__name = raw_data['station_name']
            self.__id = raw_data['_id']
            self.__data_type = list(set([t for module in raw_data['modules'] for t in module['data_type']] + raw_data['data_type']))
            self.__data_type.sort()
            self.__modules = raw_data['modules']
            logger.debug('Station.__init__ completed')

        @property
        def name(self):
            return self.__name

        @property
        def id(self):
            return self.__id

        @property
        def data_type(self):
            return self.__data_type

        @property
        def modules(self):
            m = list(set([module['module_name'] for module in self.__raw_data['modules']] + [self.__raw_data['module_name']]))
            m.sort()
            return m

        @property
        def temperature(self):
            if 'Temperature' in self.data_type:
                if self.refresh():
                    temperatures = dict()
                    if 'Temperature' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        temperatures[module_name] = self.__raw_data['dashboard_data']['Temperature']
                    for module in self.__modules:
                        if 'Temperature' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            temperatures[module_name]=  module['dashboard_data']['Temperature']
                    if len(temperatures):
                        return temperatures
            return None

        @property
        def humidity(self):
            if 'Humidity' in self.data_type:
                if self.refresh():
                    humidities = dict()
                    if 'Humidity' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        humidities[module_name] = self.__raw_data['dashboard_data']['Humidity']
                    for module in self.__modules:
                        if 'Humidity' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            humidities[module_name]=  module['dashboard_data']['Humidity']
                    if len(humidities):
                        return humidities
            return None

        @property
        def pressure(self):
            if 'Pressure' in self.data_type:
                if self.refresh():
                    pressures = dict()
                    if 'Pressure' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        pressures[module_name] = self.__raw_data['dashboard_data']['Pressure']
                    for module in self.__modules:
                        if 'Pressure' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            pressures[module_name]=  module['dashboard_data']['Pressure']
                    if len(pressures):
                        return pressures
            return None

        @property
        def noise(self):
            if 'Noise' in self.data_type:
                if self.refresh():
                    noises = dict()
                    if 'Noise' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        noises[module_name] = self.__raw_data['dashboard_data']['Noise']
                    for module in self.__modules:
                        if 'Noise' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            noises[module_name]=  module['dashboard_data']['Noise']
                    if len(noises):
                        return noises
            return None

        @property
        def co2(self):
            if 'CO2' in self.data_type:
                if self.refresh():
                    co2s = dict()
                    if 'CO2' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        co2s[module_name] = self.__raw_data['dashboard_data']['CO2']
                    for module in self.__modules:
                        if 'CO2' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            co2s[module_name]=  module['dashboard_data']['CO2']
                    if len(co2s):
                        return co2s
            return None

        @property
        def rain(self):
            if 'Rain' in self.data_type:
                if self.refresh():
                    rains = dict()
                    if 'Rain' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        rains[module_name] = self.__raw_data['dashboard_data']['Rain']
                    for module in self.__modules:
                        if 'Rain' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            rains[module_name] = module['dashboard_data']['Rain']
                    if len(rains):
                        return rains
            return None

        @property
        def wind_strength(self):
            if 'Wind' in self.data_type:
                if self.refresh():
                    winds = dict()
                    if 'WindStrength' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        winds[module_name] = self.__raw_data['dashboard_data']['WindStrength']
                    for module in self.__modules:
                        if 'WindStrength' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            winds[module_name] = module['dashboard_data']['WindStrength']
                    if len(winds):
                        return winds
            return None

        @property
        def wind_angle(self):
            if 'Wind' in self.data_type:
                if self.refresh():
                    winds = dict()
                    if 'WindAngle' in self.__raw_data['dashboard_data']:
                        if 'module_name' in self.__raw_data:
                            module_name = self.__raw_data['module_name']
                        else:
                            module_name = self.name
                        winds[module_name] = self.__raw_data['dashboard_data']['WindAngle']
                    for module in self.__modules:
                        if 'WindAngle' in module['dashboard_data']:
                            if 'module_name' in module:
                                module_name = module['module_name']
                            else:
                                module_name = self.name
                            winds[module_name] = module['dashboard_data']['WindAngle']
                    if len(winds):
                        return winds
            return None

        def __str__(self):
            string = '••Netatmo Weather.Station Object••\n\n'
            for k in self.__dict__:
                if k != 'raw_data':
                    string += k + '  ::  ' + str(self.__dict__[k]) + '\n'
            return string

        def refresh(self):
            name = self.name
            weather = self.__weather
            for device in self.__weather.get_stations_data()['body']['devices']:
                if device['station_name'] == name:
                    self.__init__(weather, device)
                    return True
            return False




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

    @property
    def cameras(self):
        return self.get_cameras()

    @property
    def events(self):
        return self.get_events()

    @property
    def persons(self):
        return self.get_persons()

    def __init__(self, name, log_level='WARNING'):
        Netatmo.__init__(self, log_level)
        self.__class_scope = ['read_camera', 'access_camera', 'write_camera']
        for scope in self.__class_scope:
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
        Netatmo.check_token_validity(self)
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
            Netatmo.check_token_validity(self)
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
        logger.debug('Getting events...')
        Netatmo.check_token_validity(self)
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
        Netatmo.check_token_validity(self)
        params = {
            'access_token': self.access_token,
            'home_id': self.home_id
        }
        if person != None:
            params['person_id'] = person.id
        logger.debug('Setting person status...')
        try:
            response = requests.post('https://api.netatmo.com/api/setpersonsaway', params=params)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as error:
            raise APIError(error.response.text)
