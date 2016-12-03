# PyNetatmo Security API Reference

## `class netatmo.Security(home_name, log_level='WARNING')`
Since Netatmo's Security API works on a home-based structure you have to pass the home's name as `device_id`.

## Methods

### `Security.get_home_data()`
Use this method to get the full data JSON from your home. Returns a `dict`.

### `Security.get_cameras()`
Use this method to get all information about cameras in you home. It returns a `list` of `objects`.

### `Security.get_events(number_of_events=15)`
Use this method to get all home's available events. It returns a `list` of `objects`.

### `Security.get_events_until(event_obj)`
Use this method to get all home's available events until the given one. It returns a `list` of `objects`.

### `Security.get_camera_picture(event, show=False)`
Use this method to get the picture of a specific event. Set `show` to `True` if you want to open the picture in the default pictures handler.

### `set_person_away(self, person=None)`
Use this method to set people's status away. If no person obj is passed to the method, it will set all home's users to away.
