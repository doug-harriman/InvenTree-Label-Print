# inventree.py
# REST Access to v0.13 InvenTree API and generation of Part Label with QR Code.

import tomllib
import keyring
import requests
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap


class InvenTreeAPI:
    """Class to interact with InvenTree API."""

    def __init__(self, cfg_file="config.toml"):
        # Defaults
        self.config_load(cfg_file)

    def config_load(self, cfg_file: str = "config.toml") -> None:
        """Load configuration from TOML file."""

        if not Path(cfg_file).is_file():
            raise FileNotFoundError(f"Config file not found: {cfg_file}")

        with open(cfg_file, "rb") as fp:
            config = tomllib.load(fp)

        # Quick clean of URL
        config["server"]["url"] = config["server"]["url"].rstrip("/")

        self._config = config

        # Get user credentials from keyring
        kr_system = config["keyring"]["system"]
        kr_field_user = config["keyring"]["field_username"]
        kr_field_pass = config["keyring"]["field_password"]
        user = keyring.get_password(kr_system, kr_field_user)
        passwd = keyring.get_password(kr_system, kr_field_pass)

        # Generate headers
        url = config["server"]["url"]
        resp = requests.get(f"{url}/api/user/token/", auth=(user, passwd))
        resp.raise_for_status()
        token = resp.json()["token"]

        self._headers = {"Authorization": f"Token {token}"}

    def parts(self) -> dict:
        """Get list of parts from InvenTree server."""

        # TODO: convert to part objects & return list of those.

        url = self._config["server"]["url"]
        parts_resp = requests.get(f"{url}/api/part/", headers=self._headers)
        parts_resp.raise_for_status()
        return parts_resp.json()

    def part(self, part_num: int) -> dict:
        """Get specific part details from InvenTree server."""

        url = self._config["server"]["url"]
        try:
            part_resp = requests.get(
                f"{url}/api/part/{part_num}/#", headers=self._headers
            )
            part_resp.raise_for_status()
        except requests.HTTPError as exc:
            raise ValueError(f"Part {part_num} not found on server: {url}") from exc
        return part_resp.json()


class InvenTreePart:
    """Class for InvenTree parts."""

    def __init__(self, num: int | None = None):
        if num is not None:
            self.num = num
        self._data = None

    @property
    def num(self) -> int:
        """Get part number."""
        return self._num

    @num.setter
    def num(self, value: int) -> None:
        """Set part number."""

        value = int(value)
        if value < 0:
            raise ValueError("Part number must be non-negative integer")

        self._num = value

        # Force a reload
        self.load()

    @property
    def name(self) -> str:
        """Get part name."""

        return self.data["name"]

    def __str__(self) -> str:
        """String representation of part."""
        return f"PN {self.num}: {self.name}"

    def __repr__(self) -> str:
        """Representation of part."""
        return f"InvenTreePart(num={self.num}, name='{self.name}')"

    def load(self) -> dict:
        """Load part data from server and return."""
        api = InvenTreeAPI()
        self._data = api.part(self._num)
        return self._data

    @property
    def data(self) -> dict:
        """Part data."""

        if self._data is None:
            self._data = self.load()

        return self._data


class PartLabel:
    """Class to generate part labels with QR codes."""

    WIDTH = 320  # 288
    HEIGHT = 96  # 88
    COLOR = "white"
    FONT_SIZE = 24

    def __init__(self, part: InvenTreePart):
        """Initialize part label."""

        if part is None:
            raise ValueError("Part must be provided to generate label")
        if not isinstance(part, InvenTreePart):
            raise TypeError("part must be an instance of InvenTreePart")
        self._part = part

        # Load up server info to get URL
        self.api = InvenTreeAPI()
        self._url = self.api._config["server"]["url"]

        # Other defaults
        self.font_size = self.FONT_SIZE
        self.font_name = "NotoSansMono-Regular"

        self._img = None

    @property
    def part(self) -> InvenTreePart:
        """Get InvenTreePart object."""

        return self._part

    @property
    def font_size(self) -> int:
        """Get default font size."""
        return self._font_size

    @font_size.setter
    def font_size(self, size: int) -> None:
        """Set default font size."""
        size = int(size)
        if size <= 0:
            raise ValueError("Font size must be positive integer")
        if size > 72:
            raise ValueError("Font size too large.  Maximum is 72.")
        self._font_size = size

    @property
    def font_name(self) -> str:
        """Get font name."""

        return self._font_name

    @font_name.setter
    def font_name(self, name: str) -> None:
        """Set font name."""

        if not isinstance(name, str):
            raise TypeError("Font name must be a string")

        try:
            font = ImageFont.load_default(size=self.font_size)
            font = ImageFont.truetype(name + ".ttf", self.font_size)
        except Exception as exc:
            raise ValueError(f"Could not load font: {name}") from exc

        self._font_name = name
        self._font = font

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        """Get font object."""

        return self._font

    def qr_gen(self, size: int | None = None) -> Image.Image:
        """Generate InvenTree QR code image for part."""

        height = self.HEIGHT
        if size is not None:
            height = size

        qr = qrcode.QRCode(
            box_size=20, border=1, error_correction=qrcode.constants.ERROR_CORRECT_H
        )
        data = '{"part":' + str(self.part.num) + "}"
        qr.add_data(data, optimize=1)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        img_qr = img_qr.resize((height, height))
        return img_qr

    @property
    def label_image(self) -> Image.Image:
        """Part label image with QR code."""

        # Base image
        self._img = Image.new(
            mode="RGB", size=(self.WIDTH, self.HEIGHT), color=self.COLOR
        )

        # Paste QR code onto base image
        img_qr = self.qr_gen(size=self.HEIGHT)
        self._img.paste(img_qr, (0, 0))

        # Part name text
        draw = ImageDraw.Draw(self._img)  # draw context

        # Line 1 and 2
        lines = wrap(self.part.name, width=12)
        if len(lines) > 2:
            lines = lines[:2]
        draw.text((self.HEIGHT + 2, 2), text=lines[0], font=self.font, fill=0)
        if len(lines) > 1:
            draw.text(
                (self.HEIGHT + 2, self.HEIGHT / 3),
                text=lines[1],
                font=self.font,
                fill=0,
            )

        # Line 3
        txt = f"PN: {self.part.num}"
        draw.text(
            (self.HEIGHT + 2, 2 * self.HEIGHT / 3), text=txt, font=self.font, fill=0
        )

        return self._img

    def to_file(self, filename: str | None = None) -> str:
        """Save part label image to file."""

        if filename is None:
            filename = f"QR-part-{self.part.num}.png"

        img = self.label_image
        img.save(filename)
        return filename
