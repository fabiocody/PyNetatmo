# PyNetatmo Thermostat API Reference

## `class netatmo.Thermostat(device_id, log_level='WARNING')`
You have to pass the MAC address of your relay as `device_id`.

## Attributes
- `device_id` - MAC address of the relay;
- `temperature` - current measured temperature;
- `set_temperature` - current set temperature;
- `relay_cmd` - current relay command.

## Methods

### `Thermostat.get_thermostats_data()`
API call. Use this method to get the full data JSON from your relay. Returns a `dict`.

### `Thermostat.get_module_ids()`
Use this method to get the module ID(s) of the thermostat(s) connected to the relay. Returns a `list`.

### `Thermostat.set_therm_point(module_id, setpoint_mode, setpoint_endtime=None, setpoint_temp=None)`
API call. Use this method to set the thermostat.
- `module_id`: MAC address of the thermostat to set.
- `setpoint_mode`: thermostat mode. Choose from `program`, `away`, `hg` (frost guard), `manual`, `off`, `max`.
- `setpoint_endtime`: if `setpoint_mode` is `max` or `manual`, defines the validity of period of the setpoint. Default is `None`.
- `setpoint_temp`: if `setpoint_mode` is `manual`, the temperature setpoint in °C.

It returns the response JSON.

### `Thermostat.switch_schedule(module_id, schedule_id)`
API call. Use this method to switch `module_id`'s current schedule with the one specified by `schedule_id`.

### `Thermostat.create_new_schedule(module_id, zones, timetable, name)`
API call. Use this method to create a new schedule to be stored in the backup list. You can find further information about this method at [dev.netatmo.com](https://dev.netatmo.com/dev/resources/technical/reference/thermostat/createnewschedule).

### `Thermostat.sync_schedule(module_id, zones, timetable)`
API call. Use this method to change the Thermostat weekly schedule. You can find further information about this method at [dev.netatmo.com](https://dev.netatmo.com/dev/resources/technical/reference/thermostat/syncschedule).


# Quick Tutorial

```python
# Import Thermostat class
from netatmo import Thermostat

# Create Thermostat instance
t = Thermostat('70:ee:50:aa:bb:cc')

# Set thermostat to 22°C
t.set_therm_point(t.get_module_ids()[0], 'manual', setpoint_temp=22)

# Print thermostat's measured temperature and set temperature
print(t.temperature, t.set_temperature)
```
