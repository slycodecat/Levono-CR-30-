# Network GPIO interface for Raspberry Pi 4 peripheral

import socket
import json


class Pi4GPIOPin:

    def __init__(self, chip, pin):
        self.chip = chip
        self.pin = pin
        self.cycle_time = 0.100

    def setup_max_duration(self, max_duration):
        pass

    def setup_start_value(self, start_value, shutdown_value):
        self.start_value = start_value
        self.shutdown_value = shutdown_value

    def setup_cycle_time(self, cycle_time, hardware_pwm=False):
        self.cycle_time = cycle_time

    def set_digital(self, print_time, value):
        self.chip.write_gpio(self.pin, 1 if value else 0)

    def set_pwm(self, print_time, value):
        self.chip.write_gpio(self.pin, 1 if value > 0.5 else 0)

    def get_mcu(self):
        return self.chip

    def next_aligned_print_time(self, print_time, allow_early=0.):
        return print_time


class Pi4GPIO:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.host = config.get('host', '192.168.88.20')
        self.port = config.getint('port', 9000)

        ppins = self.printer.lookup_object('pins')
        ppins.register_chip('pi4', self)

    def setup_pin(self, pin_type, pin_params):
        if pin_type not in ('digital_out', 'pwm'):
            raise self.printer.lookup_object('pins').error(
                "pi4_gpio only supports output pins"
            )

        pin = pin_params['pin']

        if not pin.startswith('gpio'):
            raise self.printer.lookup_object('pins').error(
                "pi4 GPIO pin must be named gpio0 through gpio27"
            )

        try:
            gpio = int(pin[4:])
        except ValueError:
            raise self.printer.lookup_object('pins').error(
                "Invalid pi4 GPIO pin: %s" % pin
            )

        if gpio < 0 or gpio > 27:
            raise self.printer.lookup_object('pins').error(
                "pi4 GPIO must be between 0 and 27"
            )

        return Pi4GPIOPin(self, gpio)

    def write_gpio(self, gpio, value):
        request = {
            "action": "write",
            "gpio": gpio,
            "value": value
        }

        data = (json.dumps(request) + "\n").encode()

        try:
            with socket.create_connection(
                (self.host, self.port),
                timeout=2.0
            ) as sock:
                sock.sendall(data)

                response = b""

                while b"\n" not in response:
                    chunk = sock.recv(4096)

                    if not chunk:
                        break

                    response += chunk

        except Exception as e:
            raise self.printer.command_error(
                "pi4 GPIO connection failed: %s" % str(e)
            )

        if not response:
            raise self.printer.command_error(
                "pi4 GPIO server returned no response"
            )

        try:
            result = json.loads(
                response.decode().split("\n", 1)[0]
            )
        except Exception as e:
            raise self.printer.command_error(
                "Invalid response from pi4 GPIO server: %s" % str(e)
            )

        if not result.get("ok"):
            raise self.printer.command_error(
                "pi4 GPIO error: %s"
                % result.get("error", "unknown error")
            )

    def max_nominal_duration(self):
        return 0.

    def min_schedule_time(self):
        return 0.


    def estimated_print_time(self, eventtime):
        return eventtime


def load_config(config):
    return Pi4GPIO(config)
