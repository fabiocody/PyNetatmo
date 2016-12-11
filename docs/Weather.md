# PyNetatmo Weather API Reference

## `class netatmo.Weather(device_id=None, get_favorites=False, log_level='WARNING')`
If you have a Netatmo Weather Station, you can pass its MAC address as `device_id`. Otherwise, you can access to your favorites stations setting `get_favorites` to True. You can set one of these or both, but if you don't set any, your Weather class will be quite useless.

## Attributes
- `device_id` - MAC address of the station;
- `stations` - list of stations;
- `my_station` - if `device_id` is provided, the station whose ID corresponds to the device_id provided;
- `get_favorites` - whether to retrieve data from favorite stations or not.

## Methods

### `Weather.get_stations_data()`
API call. Use this method to get the full data JSON from the weather station(s). Returns a `dict`.

### `Weather.get_station_from_id(ID)`
Use this method to return the station identified by `ID`.

### `Weather.get_stations_from_name(name)`
Use this method to return all the stations identified by `name`. Returns a `dict` indexed by names.

### `class Weather.Station(raw_data)`
#### Attributes
- `raw_data`: complete dict returned by `get_station_from_id`.
- `name`: station's name.
- `id`: station's ID (MAC address).
- `type`: list of station's data types.
- `modules`: list of modules installed in the station.
- `temperature`: temperature measured by the station.
- `humidity`: humidity measured by the station.
- `rain`: rain measured by the station.
- `wind_strength`: wind strength measured by the station.
- `wind angle`: wind angle measured by the station.


# Quick Tutorial

```python
# Import Weather class
from netatmo import Weather

# Create Weather instance
w = Weather('70:ee:50:aa:bb:cc')

# Get station
s = w.my_station

# Print data
print(s.name, s.temperature, s.humidity)
```
