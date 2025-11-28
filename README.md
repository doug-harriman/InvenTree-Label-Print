# About

This project is intended to generate and print labels for InvenTree parts on a Phomemo D35 Bluetooth label printer.

All Phomemo code leveraged directly from: https://github.com/polskafan/phomemo_d30

# Status

* Able to generate labels with part name, num and QR code.
* Able to find BT serial port device for paired printer on Linux.
* Able to send an image to printer, but image is not yet correct.
    * See issues in phomemo.py

# Installation

Requires uv to be installed.

Install w/uv

# Configuration

* Uses keyring to store InvenTree user name and password.
* Set InvenTree server URL in environment variable INVENTREE_URL.

Keyring instructions.


