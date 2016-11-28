# Netatmo Thermostat API Reference

# `netatmo.Thermostat(device_id, log_level='WARNING')`
You have to pass the MAC address of your relay as `device_id`.

## Methods

### `Thermostat.get_thermostats_data()`
Use this method to get the full data JSON from your relay. Returns a `dict`.

### `Thermostat.get_module_ids()`
Use this method to get the module ID(s) of the thermostat(s) connected to the relay. Returns a `list`.

### `Thermostat.get_current_temperatures()`
Use this method to get the measured and the set temperature from every thermostats connected to the relay. Returns a `dict` in the form `'temp': list(), 'setpoint_temp': list()`.

### `Thermostat.set_therm_point(module_id, setpoint_mode, setpoint_endtime=None, setpoint_temp=None)`
Use this method to set the thermostat.
- `module_id`: MAC address of the thermostat to set.
- `setpoint_mode`: thermostat mode. Choose from `program`, `away`, `hg` (frost guard), `manual`, `off`, `max`.
- `setpoint_endtime`: if `setpoint_mode` is `max` or `manual`, defines the validity of period of the setpoint. Default is `None`. 
- `setpoint_temp`: if `setpoint_mode` is `manual`, the temperature setpoint in °C.
Returns the response JSON.