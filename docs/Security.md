# PyNetatmo Security API Reference

## `class netatmo.Security(home_name, log_level='WARNING')`
Since Netatmo's Security API works on a home-based structure you have to pass the home's name as `device_id`.

## Methods

### `Security.get_home_data()`
Use this method to get the full data JSON from your home. Returns a `dict`.

### `Security.get_cameras()`
Use this method to get all information about cameras in you home. Returns a `list` of `dict`.

### `Security.get_events(number_of_events=15)`
Use this method to get a `list` of `dict` each containing an event.

### `Security.get_camera_picture(event, show=False)`
Use this method to get the picture of a specific events. Set `show` to `True` if you want to open the picture in the default pictures handler.
