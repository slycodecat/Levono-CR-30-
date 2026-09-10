# Klipper M700 + Pi 4 GPIO

## Architecture

Lenovo ThinkCentre M700 runs Ubuntu and hosts:
- Klipper
- Moonraker
- Mainsail
- Three printers

Raspberry Pi 4 is a network GPIO peripheral only.
It does NOT run Klipper.

## Network

M700: 192.168.88.17
Pi 4: 192.168.88.20
Pi 4 GPIO server: TCP port 9000

## Pi 4 GPIO

GPIO14: CR-30 main fan
GPIO15: CR-30 hotend fan

## Pi 4 server

/opt/pi4-gpio/server.py
/etc/systemd/system/pi4-gpio.service

## M700 Klipper integration

/home/fabian/klipper/klippy/extras/pi4_gpio.py

CR-30 configuration uses:

[pi4_gpio]
host: 192.168.88.20
port: 9000

## Important

Do not commit passwords, SSH keys, tokens, logs, databases, or gcode files.
