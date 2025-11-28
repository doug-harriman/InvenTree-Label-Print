# phomemo.py
# Phomemo Bluetooth printer interface for Linux.
#
# Supports D30 and D35 models.
# Device should previously be paired and set up to auto start RFCOMM service.
#

# ISSUES:
# * Text is not printing at all
# * Have to send image twice to get it to print.
# * QR code is printing on both ends of label
# * Image fills full label, need a margin.

import subprocess
import PIL
from PIL import Image
import serial
import math
from pathlib import Path


# Helper functions from phomemo_d30/image_helper.py
def split_image(image):
    chunks = image.height // 255

    for chunk in range(chunks + 1):
        i = image.crop((0, chunk * 255, image.width, chunk * 255 + 255))
        yield i


def image_to_bits(image: Image.Image, threshold: int = 127):
    return [
        bytearray(
            [1 if image.getpixel((x, y)) > threshold else 0 for x in range(image.width)]
        )
        for y in range(image.height)
    ]


class Phomemo:
    """Class representing a Phomemo Bluetooth printer."""

    # Specifically supported devices
    NAMES = ["D30", "D35"]

    WIDTH = 320
    HEIGHT = 96

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

    def print_file(self, filename: str):
        """Print an image file to the printer."""

        if not Path(filename).is_file():
            raise FileNotFoundError(f"File not found: {filename}")

        img = Image.open(filename)
        self.print_image(img)

    def print_image(self, img: Image):
        """Print an image to the printer."""

        if not self.is_connected:
            raise RuntimeError("Printer not connected")

        port = self.port
        if port is None:
            raise RuntimeError("Printer port not found")

        # Resize aspect ratio assumes landscape orientation
        img_w, img_h = img.size
        # if img_w < img_h:
        #     # Rotate to landscape
        #     img = img.rotate(270)
        #     img_w, img_h = img.size

        # Check image size and resize as needed.
        # From phomemo_d30/image_helper.py:preprocess_image
        # aspect = img_w / img_h
        # new_size = (self.HEIGHT, math.floor(self.HEIGHT / aspect))
        # img = img.resize(new_size)

        # Invert
        # img = PIL.ImageOps.invert(img.convert("RGB")).convert("1")

        # Now rotate to portrait for printing
        # img = img.rotate(270)

        # Open serial port
        with serial.Serial(port, timeout=10) as ser:
            # Send header
            # from phomemo_30/print_text.py:header()
            job_header = [
                "1f1138",
                "1f11121f1113",
                "1f1109",
                "1f1111",
                "1f1119",
                "1f1107",
                "1f110a1f110202",
            ]

            for packet in job_header:
                ser.write(bytes.fromhex(packet))
                ser.flush()

            # Print image
            # from phomemo_30/print_text.py:print_image()
            for chunk in split_image(img):
                data = bytearray.fromhex("1f1124001b401d7630000c004001")
                bits = image_to_bits(chunk)
                for line in bits:
                    for byte_num in range(self.HEIGHT // 8):
                        byte = 0
                        for bit in range(8):
                            pixel = line[byte_num * 8 + bit]
                            byte |= (pixel & 0x01) << (7 - bit)
                        data.append(byte)

                ser.write(data)
                ser.flush()
                data = ""


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
