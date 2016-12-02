# PyNetatmo

## Configuration
During the installation process you will be asked to enter some information, including your Netatmo account's credentials and some tokens that you can retrieve when you create an application at dev.netatmo.com.
You can choose not to enter this information on that moment: in this case, in order to use this API wrapper, you have to put in your home directory a file named `.pynetatmo.conf`. Here's an example of how it should look like.
``` json
{
    "user": "E-MAIL",
    "password": "PASSWORD",
    "client_id": "CLIENT-ID RETRIEVED FROM dev.netatmo.com",
    "client_secret": "CLIENT-SECRET RETRIEVED FROM dev.netatmo.com",
    "scope": "SPACE-SEPARATED SCOPES (e.g. read_thermostat write_thermostat')"
}
```
You can find the available scopes and further information on [dev.netatmo.com](https://dev.netatmo.com/dev/resources/technical/reference/smarthomeapi).

# Reference

### `netatmo.Netatmo(log_level)`
Base class used to authenticate and to set logger formatting. Every other "main" class in this wrapper inherits from this one.

### `netatmo.NetatmoError(message=None)`
Base exception class for this module.

### `netatmo.APIError(message=None)`
Inherits from `netatmo.NetatmoError`. Raised when an API error occurs.

### `netatmo.ScopeError(scope)`
Inherits from `netatmo.NetatmoError`. Raised when a scope required to use a class is not found in the configuration.

### `netatmo.ConfigError(error)`
Inherits from `netatmo.NetatmoError`. Raised when the configuration file is not found or when the latter is invalid.

You can find information about other classes in the [respective files](https://github.com/fabiocody/PyNetatmo/tree/master/docs).
