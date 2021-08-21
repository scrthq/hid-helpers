import sys
import getopt
import hid
import yaml
import logging
from sys import exc_info
from time import sleep
from os import path

class HIDController(object):
    def __init__(self,config_file=r'config.yml'):
        self.log = []
        self.tasks = []
        self.device_list = []
        self.import_config(config_file)
        self.setup_logger()

    def parse_user_buf(self, raw_buffer, buffer_size):
        buf = [0] * buffer_size
        try:
            raw_buffer = eval(raw_buffer, {})
            print('raw_buffer:', raw_buffer)
            if type(raw_buffer) is list or type(raw_buffer) is tuple:
                for i in range(0, len(buf)):
                    if type(buf[i]) is str:
                        buf[i] = 0
            else:
                self.logger.info("Parse error: input is not a list")
        except Exception as e:
            self.logger.info(f"Parse error: {e}")
            return []
        for i in range(0, min(buffer_size, len(raw_buffer))):
            buf[i] = raw_buffer[i]
        return buf

    def setup_logger(self):
        self.logger = logging.getLogger('hid_helpers')
        self.logger.setLevel(self.config.get('log_level',logging.INFO))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setLevel(self.config.get('log_level', logging.INFO))
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        if self.config.get('log_file') is not None:
            fh = logging.FileHandler(self.config.get('log_file'))
            fh.setLevel(self.config.get('log_level', logging.INFO))
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
        else:
            self.logger.debug('log_file not specified on the config')

    def import_config(self,config_file):
        with open(config_file) as c:
            self.config = yaml.load(c, Loader=yaml.FullLoader)

    def scan_devices(self, verbose=True):
        if verbose:
            self.logger.info("~ ~ ~ STARTING DEVICE SCAN ~ ~ ~")
        self.device_list = []
        try:
            for device in self.config['devices']:
                for i in hid.enumerate():
                    if (
                        ('manufacturer_string' in device.keys() and i['manufacturer_string'] == device['manufacturer_string']) and
                        ('product_string' in device.keys() and i['product_string'] == device['product_string'])
                    ):
                        if verbose:
                            self.logger.info(
                                f"MATCHED DEVICE: {i['manufacturer_string']} {i['product_string']}  vid/pid:{i['vendor_id']}/{i['product_id']} usage:{i['usage_page']}/{i['usage']} ")
                        for k, v in device.items():
                            if k not in i.keys():
                                if verbose:
                                    self.logger.debug(
                                        f"Adding property to device from configuration: {k} = {v}"
                                    )
                                i[k] = v
                        self.device_list.append(i)
        except KeyboardInterrupt:
            sys.exit()

    def status(self, message):
        self.logger.info(message)

    def start_reporter_tasks(self, device_list=[], polling_frequency_ms=2000):
        self.logger.debug(
            f"Starting {polling_frequency_ms}ms loop")
        device = None
        polling_secs = polling_frequency_ms / 1000
        i = 0
        while True:
            try:
                if (i % 2) == 0:
                    self.scan_devices()
                i = i+1
                for d in device_list:
                    self.logger.info(
                        f"{d['manufacturer_string']} {d['product_string']}  vid/pid:{d['vendor_id']}/{d['product_id']} usage:{d['usage_page']}/{d['usage']} ")
                    device = hid.device()
                    device.open_path(d['path'])
                    for raw_buffer in d['byte_strings']:
                        buf = self.parse_user_buf(
                            raw_buffer, raw_buffer.split(',').__len__())
                        device.write(buf)
                    device.close()
                sleep(polling_secs)
            except KeyboardInterrupt:
                sys.exit()
            except:
                e = exc_info()[0]
                self.logger.info(f"Send out report error: {e}")
                if device is not None:
                    device.close()
                sleep(polling_secs)
                break

    def start(self):
        self.scan_devices()
        while True:
            self.logger.info("Starting reporter tasks")
            self.start_reporter_tasks(
                device_list=self.device_list,
                polling_frequency_ms=self.config.get(
                    'polling_frequency_ms', 2000),
            )

def show_help(full:bool = True):
    info = """
HID Helper Syntax:

    hid_helpers.py [options] config.yml

Options:
"""
    if full:
        info += """
    -l | --list_devices

        Shows the current connected HID devices matched against the configuration file.

    -a | --list_all

        Enumerates all HID devices currently connected to the host in config file YAML format.

    -h | --help

        Shows this help text.

Examples:

    $ python3 hid_helpers.py config.yml

    # Starts the controller in a loop, scanning for devices on the configuration and sending the specified bytes from the configuration.

    --------------------------------

    $ python3 hid_helpers.py -a
        # OR
    $ python3 hid_helpers.py --list_all

    # Prints all connected devices in YAML format

    --------------------------------

    $ python3 hid_helpers.py -l config.yml
        # OR
    $ python3 hid_helpers.py --list_devices config.yml

    # Prints the connected devices matching what is present on the config file under `devices`

    --------------------------------

    $ python3 hid_helpers.py -l
        # OR
    $ python3 hid_helpers.py --list_devices

    # If no config file is passed with the list_devices parameter, all connected devices are printed instead

"""
    else:
        info += """
    [-l|--list_devices] | [-a|--list_all] | [-h|--help]

"""
    print(info)

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],"lash",["list_devices","list_all","start","help"])
    except getopt.GetoptError:
        print('\nSomething went wrong!!\n')
        show_help(full=False)
        sys.exit(2)
    if len(args) == 0 and path.exists('config.yml'):
        args.append('config.yml')
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_help()
            sys.exit()
    while True:
        try:
            for opt, arg in opts:
                if opt in ('-a','--list_all','-l','--list_devices'):
                    if opt in ('-a','--list_all') or len(args) == 0:
                        if len(args) == 0:
                            print("Config file not passed as an argument! Enumerating all devices instead")
                        dev_list = hid.enumerate()
                    elif opt in ("-l", "--list_devices"):
                        controller = HIDController(args[0])
                        controller.scan_devices(False)
                        dev_list = controller.device_list
                    config_yaml = {
                        'log_file': 'hid_helpers.log',
                        'log_level': 'INFO',
                        'polling_frequency_ms': 2000,
                        'devices': sorted(dev_list, key = lambda i: i['product_string']),
                    }
                    print(yaml.dump(config_yaml,sort_keys = False))
                    sys.exit()
            controller = HIDController(args[0])
            controller.start()
        except KeyboardInterrupt:
            sys.exit()
        except:
            raise
