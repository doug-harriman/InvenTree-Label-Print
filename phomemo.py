# phomemo.py
# Phomemo Bluetooth printer interface for Linux.
#
# Supports D30 and D35 models.
# Device should previously be paired and set up to auto start RFCOMM service.
#

import subprocess


class Phomemo:
    """Class representing a Phomemo Bluetooth printer."""

    # Specifically supported devices
    NAMES = ["D30", "D35"]

    def __init__(self):
        self._name = "Printer Not Found"
        self._mac = "<MAC Address Not Found>"

        self.find()

    def find(self) -> bool:
        """
        Find the MAC address of the Phomemo printer.
        If found, store the MAC address in self.mac and return True.
        If not found, return False.

        Returns:
            bool: True if printer found, False otherwise.
        """

        devs = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True,
            text=True,
        )

        for line in devs.stdout.strip().split("\n"):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                mac = parts[1]
                name = parts[2]

                if name in self.NAMES:
                    self._name = name
                    self._mac = mac

        return self._mac is not None

    @property
    def mac(self):
        """Get the MAC address of the printer."""

        # Try auto connect
        if self._mac is None:
            self.find()

        return self._mac

    @property
    def name(self):
        """Get the name of the printer."""
        return self._name

    def __str__(self):
        s = f"Phomemo({self.name},mac={self.mac}"

        port = self.port
        if port:
            s += f",port={port}"

        s += ")"
        return s

    def __repr__(self):
        return self.__str__()

    @property
    def info(self):
        """Get information about the printer."""
        if self.mac is None:
            return None

        result = subprocess.run(
            ["bluetoothctl", "info", self._mac],
            capture_output=True,
            text=True,
        )

        return result.stdout

    @property
    def is_connected(self) -> bool:
        """Check if the printer is connected."""

        # Returns none if no connection
        info = self.info
        if not info:
            return False

        # Must actually be connected
        conn = "Connected: yes" in self.info
        if not conn:
            return False

        # Must also be connected to the Serial Port service
        return "UUID: Serial Port" in info

    @property
    def port(self) -> str | None:
        """Get the RFCOMM port of the printer."""
        if not self.is_connected:
            return None

        result = subprocess.run(
            ["rfcomm", "--device", self._mac],
            capture_output=True,
            text=True,
        )

        port = None
        for line in result.stdout.strip().split("\n"):
            if self._mac in line:
                parts = line.split(":", 1)
                if len(parts) >= 2:
                    port = parts[0].strip()

        if port:
            port = "/dev/" + port

        return port


if __name__ == "__main__":
    import sys

    printer = Phomemo()

    if not printer.is_connected:
        print("Printer not connected")
        sys.exit(1)

    port = printer.port
    if port:
        print(f"Phomemo {printer.name} connected on RFCOMM port: {port}")
    else:
        print(f"Phomemo printer not connected, check Bluetooth connection")
