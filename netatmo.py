#!/usr/bin/env python3

import os
import json
import logging
from io import BytesIO
from platform import python_version_tuple
from getpass import getpass
from time import time
from pwd import getpwall
import requests
from PIL import Image


__version__ = '0.1.1'

logger = logging.getLogger('netatmo')
logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s', level=getattr(logging, 'WARNING'))

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
		logging.basicConfig(format='[*] %(levelname)s : %(module)s : %(message)s', level=getattr(logging, log_level))
		self.__BASE_URL = 'https://api.netatmo.com'
		self.__access_token = None
		self.__refresh_token = None
		self.__expires_in = None
		self.__timestamp = None
		self._auth()
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

	def _api_call(self, resource, payload):
		logger.debug('API call : %s : %s', resource, payload)
		try:
			response = requests.post(self.__BASE_URL + resource, data=payload)
			response.raise_for_status()
			try:
				return response.json()
			except:
				return response.text
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def _auth(self):
		logger.debug('Authorizing...')
		try:
			payload = {
				'grant_type': 'password',
				'username': CONF['user'],
				'password': CONF['password'],
				'client_id': CONF['client_id'],
				'client_secret': CONF['client_secret'],
				'scope': CONF['scope']
			}
			data = self._api_call('/oauth2/token', payload)
			self.__timestamp = time()
			self.__expires_in = data['expires_in']
			self.__access_token = data['access_token']
			self.__refresh_token = data['refresh_token']
			self.__scope = data['scope']
			logger.debug('Your access token is: ' + self.__access_token)
			logger.debug('Your refresh token is: ' + self.__refresh_token)
			logger.debug('Your scopes are: ' + str(self.__scope))
			logger.debug('Authorization completed')
		except KeyError:
			raise ConfigError('key')

	def _refresh(self):
		logger.debug('Refreshing...')
		try:
			payload = {
				'grant_type': 'refresh_token',
				'refresh_token': self.__refresh_token,
				'client_id': CONF['client_id'],
				'client_secret': CONF['client_secret']
			}
			data = self._api_call('/oauth2/token', payload)
			self.__timestamp = time()
			self.__access_token = data['access_token']
			self.__refresh_token = data['refresh_token']
			self.__expires_in = data['expires_in']
		except KeyError:
			raise ConfigError('key')

	def _check_token_validity(self):
		if time() - self.__timestamp < self.__expires_in:
			self._refresh()




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
		self.__cache = None
		self.__cache_timestamp = None
		self.__CACHE_VALIDITY = 600		# seconds = 10 minutes
		self.get_thermostats_data()
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
		logger.debug('Checking cache...')
		if self.__cache and time() - self.__cache_timestamp < self.__CACHE_VALIDITY:
			return self.__cache
		logger.debug('Cache is invalid: getting thermostat data from the api...')
		self._check_token_validity()
		payload = {
			'access_token': self.access_token,
			'device_id': self.device_id
		}
		data = self._api_call('/api/getthermostatsdata', payload)['body']
		self.__cache = data
		self.__cache_timestamp = time()
		return data

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
		self._check_token_validity()
		payload = {
			'access_token': self.access_token,
			'device_id': self.device_id,
			'module_id': module_id,
			'setpoint_mode': setpoint_mode,
		}
		if setpoint_endtime:
			payload['setpoint_endtime'] = setpoint_endtime
		if setpoint_temp:
			payload['setpoint_temp'] = setpoint_temp
		if setpoint_mode in allowed_setpoint_modes:
			return self._api_call('/api/setthermpoint', payload)
		logger.error('Invalid choice for setpoint_mode. Choose from ' + str(allowed_setpoint_modes))
		return False

	def switch_schedule(self, module_id, schedule_id):
		logger.debug('Switching schedule...')
		self._check_token_validity()
		payload = {
			'access_token': self.access_token,
			'device_id': self.device_id,
			'module_id': module_id,
			'schedule_id': schedule_id
		}
		return self._api_call('/api/switchschedule', payload)

	def create_new_schedule(self, module_id, zones, timetable, name):
		logger.debug('Creating new schedule...')
		self._check_token_validity()
		payload = {
			'access-token': self.access_token,
			'device_id': self.device_id,
			'module_id': module_id,
			'zones': zones,
			'timetable': timetable,
			'name': name
		}
		return self._api_call('/api/createnewschedule', payload)

	def sync_schedule(self, module_id, zones, timetable):
		logger.debug('Creating new schedule...')
		self._check_token_validity()
		payload = {
			'access-token': self.access_token,
			'device_id': self.device_id,
			'module_id': module_id,
			'zones': zones,
			'timetable': timetable
		}
		return self._api_call('/api/syncschedule', payload)




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
		self.__stations = None
		self.__cache = None
		self.__cache_timestamp = None
		self.__CACHE_VALIDITY = 600		# seconds = 10 minutes
		logger.debug('Weather.__init__ completed')

	@property
	def stations(self):
		if not self.__stations:
			self.__stations = [self.Station(self, device) for device in self.get_stations_data()['body']['devices']]
		return self.__stations

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
		logger.debug('Checking cache...')
		if self.__cache and time() - self.__cache_timestamp < self.__CACHE_VALIDITY:
			return self.__cache
		logger.debug('Cache is invalid: getting stations data from the api...')
		self._check_token_validity()
		payload = {
			'access_token': self.access_token,
			'get_favorites': str(self.get_favorites).lower()
		}
		if self.device_id:
			payload['device_id'] = self.device_id
		data = self._api_call('/api/getstationsdata', payload)
		self.__cache = data
		self.__cache_timestamp = time()
		return data

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
		if not stations:
			return None
		elif len(stations) == 1:
			return stations[name]
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
							temperatures[module_name] = module['dashboard_data']['Temperature']
					if temperatures:
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
							humidities[module_name] = module['dashboard_data']['Humidity']
					if humidities:
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
							pressures[module_name] = module['dashboard_data']['Pressure']
					if pressures:
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
							noises[module_name] = module['dashboard_data']['Noise']
					if noises:
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
							co2s[module_name] = module['dashboard_data']['CO2']
					if co2s:
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
					if rains:
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
					if winds:
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
					if winds:
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
		self._check_token_validity()
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
			response.connection.close()
			data = [h for h in data if h['name'] == self.name]
			if not data:
				raise self._NoDevice('No device with the name provided')
			return data[0]
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def get_cameras(self):
		return [self.Camera(c) for c in self.get_home_data()['cameras']]

	def get_events(self, numbers_of_events=15):
		return [self.Event(e) for e in self.get_home_data(numbers_of_events)['events']]

	def get_persons(self, name=None, pseudo=False):
		#if type(pseudo) != bool:
		if not isinstance(pseudo, bool):
			raise TypeError('\'pseudo\' must be a boolean value')
		if name != None:
			#if type(name) != str:
			if not isinstance(name, str):
				raise TypeError('\'name\' must be a string')
			return [self.Person(c) for c in self.get_home_data()['persons'] if 'pseudo' in c.keys() and c['pseudo'] == name][0]
		if pseudo:
			return [self.Person(c) for c in self.get_home_data()['persons'] if 'pseudo' in c.keys()]
		return [self.Person(c) for c in self.get_home_data()['persons']]

	def get_camera_picture(self, event, show=False):
		#if type(event) == Security.Event:
		if isinstance(event, Security.Event):
			if event.type not in ['movement', 'person']:
				raise TypeError('The input event must be a movement or a \'person seen event\'. Only these have related screenshots')
		#if type(event) not in [Security.Event, Security.Person]:
		if not isinstance(event, (Security.Event, Security.Person)):
			raise TypeError('The input must be an event or a person object')
		logger.debug('Getting event related image...')
		try:
			self._check_token_validity()
			base_url = 'https://api.netatmo.com/api/getcamerapicture?'
			try:
				url = base_url + 'image_id=' + str(event.snapshot['id']) + '&key=' + str(event.snapshot['key'])
			except AttributeError:
				url = base_url + 'image_id=' + str(event.face['id']) + '&key=' + str(event.face['key'])
			response = requests.get(url)
			response.raise_for_status()
			img = Image.open(BytesIO(response.content))
			response.connection.close()
			logger.debug('Request completed')
			if show:
				img.show()
			return img
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def get_events_until(self, event):
		#if type(event) is not Security.Event:
		if not isinstance(event, Security.Event):
			raise TypeError('Input must be an event obj')
		logger.debug('Getting events...')
		self._check_token_validity()
		params = {
			'access_token': self.access_token,
			'home_id': self.home_id,
			'event_id': event.id
		}
		try:
			response = requests.post('https://api.netatmo.com/api/geteventsuntil', params=params)
			response.raise_for_status()
			data = response.json()['body']['events_list']
			response.connection.close()
			return [self.Event(e) for e in data]
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def set_person_away(self, person=None):
		#if type(person) not in [Security.Person, None]:
		if not isinstance(person, (Security.Person, None)):
			raise TypeError('The input must be a Security.Person object or None if you want to set all people away')
		self._check_token_validity()
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
			data = response.text
			response.connection.close()
			return data
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def Addwebhook(self, url):
		self._check_token_validity()
		params = {
			'access_token': self.access_token,
			'url': url,
			'app_types': 'app_security'
		}

		try:
			response = requests.post('https://api.netatmo.com/api/addwebhook', params=params)
			response.raise_for_status()
			data = response.text
			response.connection.close()
			print(data)
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)

	def Dropwebhook(self):
		self._check_token_validity()
		params = {
			'access_token': self.access_token,
			'app_types': 'app_security'
		}

		try:
			response = requests.post('https://api.netatmo.com/api/dropwebhook', params=params)
			response.raise_for_status()
			data = response.text
			response.connection.close()
			print(data)
		except requests.exceptions.HTTPError as error:
			raise APIError(error.response.text)
