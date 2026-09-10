#!/usr/bin/env python3

import socket
import json
import gpiod
from gpiod.line import Direction, Value
from gpiod.line_settings import LineSettings

HOST = "0.0.0.0"
PORT = 9000
CHIP = "/dev/gpiochip0"

output_requests = {}
input_requests = {}
output_values = {}


def write_gpio(gpio, value):
    if gpio not in output_requests:
        output_requests[gpio] = gpiod.request_lines(
            CHIP,
            consumer="pi4-gpio",
            config={
                gpio: LineSettings(
                    direction=Direction.OUTPUT,
                    output_value=Value.ACTIVE if value else Value.INACTIVE
                )
            },
        )
    else:
        output_requests[gpio].set_value(
            gpio,
            Value.ACTIVE if value else Value.INACTIVE
        )

    output_values[gpio] = value


def read_gpio(gpio):
    if gpio in output_values:
        return output_values[gpio]

    if gpio not in input_requests:
        input_requests[gpio] = gpiod.request_lines(
            CHIP,
            consumer="pi4-gpio",
            config={
                gpio: LineSettings(direction=Direction.INPUT)
            },
        )

    value = input_requests[gpio].get_value(gpio)
    return 1 if value == Value.ACTIVE else 0


def handle(request):
    action = request.get("action")
    gpio = request.get("gpio")

    if not isinstance(gpio, int) or gpio < 0 or gpio > 27:
        return {"ok": False, "error": "GPIO must be an integer from 0 to 27"}

    if action == "write":
        value = request.get("value")

        if value not in (0, 1):
            return {"ok": False, "error": "value must be 0 or 1"}

        write_gpio(gpio, value)

        return {
            "ok": True,
            "gpio": gpio,
            "value": value
        }

    if action == "read":
        return {
            "ok": True,
            "gpio": gpio,
            "value": read_gpio(gpio)
        }

    return {
        "ok": False,
        "error": "action must be read or write"
    }


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)

        print(
            f"pi4 GPIO server listening on {HOST}:{PORT}",
            flush=True
        )

        while True:
            conn, addr = server.accept()

            with conn:
                print(f"Connection from {addr}", flush=True)

                buffer = b""

                while True:
                    data = conn.recv(4096)

                    if not data:
                        break

                    buffer += data

                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)

                        if not line:
                            continue

                        try:
                            request = json.loads(line.decode())
                            response = handle(request)

                        except Exception as e:
                            response = {
                                "ok": False,
                                "error": str(e)
                            }

                        conn.sendall(
                            (json.dumps(response) + "\n").encode()
                        )


if __name__ == "__main__":
    main()
