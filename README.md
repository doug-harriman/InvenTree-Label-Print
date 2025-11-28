# About

This project is intended to generate and print labels for InvenTree parts on a Phomemo D35 Bluetooth label printer.

All Phomemo code leveraged directly from: https://github.com/polskafan/phomemo_d30

# Status

* InvenTree Python API requires newer version of InvenTree.
    * Upgrade looks like a separate project.
* Falling back to simpler method: cli for PN & description.
* Proto of image generator working, see `inventreelabel.py`
* The code in "phomemo_d30" is capable of printing to the Phomemo D35.
* Would like to get it to auto-connect Bluetooth printer.
* Need to get image converted per the example code in the d30 dir.

# Installation

Requires uv to be installed.

Install w/uv

# Configuration

* Uses keyring to store InvenTree user name and password.
* Set InvenTree server URL in environment variable INVENTREE_URL.

Keyring instructions.


