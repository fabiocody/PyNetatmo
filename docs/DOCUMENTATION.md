# PyNetatmo

## Configuration
In order to use this API wrapper you have to put in your home directory a file named `.pynetatmo.conf`. Here's an example of how it should look like.
``` json
{
    "user": "E-MAIL",
    "password": "PASSWORD",
    "client_id": "CLIENT-ID RETRIEVED FROM dev.netatmo.com",
    "client_secret": "CLIENT-SECRET RETRIEVED FROM dev.netatmo.com",
    "scope": "SPACE-SEPARATED SCOPES (e.g. read_thermostat write_thermostat')"
}
```
You can find the available scopes and more information on [dev.netatmo.com](https://dev.netatmo.com/dev/resources/technical/reference/smarthomeapi).

# Reference

### `netatmo.**Netatmo**(log_level)`
Base class used to authenticate and to set logger formatting. Every other class in this wrapper inherits from this one.

### `netatmo.**NetatmoError**`
Base exception class for this module.

### `netatmo.**APIError**`
Inherits from netatmo.**NetatmoError**. Raised when an API error occurs.

Information about other classes at **link**