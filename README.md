# HID Helper Syntax

```python
hid_helpers.py [options] config.yml
```

## Options

```python
-l | --list_devices

    Shows the current connected HID devices matched against the configuration file.

-a | --list_all

    Enumerates all HID devices currently connected to the host in config file YAML format.

-h | --help

    Shows this help text.
```

## Arguments

```python
config.yml

    Default value here is `config.yml`. If you have a custom path to your config file, pass it as the last argument to the script.
```

## Examples

```python
    $ python3 hid_helpers.py config.yml

    # Starts the controller in a loop, scanning for devices on the configuration and sending the specified bytes from the configuration.

    ##########################################

    $ python3 hid_helpers.py -a
        # OR
    $ python3 hid_helpers.py --list_all

    # Prints all connected devices in YAML format

    ##########################################

    $ python3 hid_helpers.py -l config.yml
        # OR
    $ python3 hid_helpers.py --list_devices config.yml

    # Prints the connected devices matching what is present on the config file under `devices`

    ##########################################

    $ python3 hid_helpers.py -l
        # OR
    $ python3 hid_helpers.py --list_devices

    # If no config file is passed with the list_devices parameter, all connected devices are printed instead
```
