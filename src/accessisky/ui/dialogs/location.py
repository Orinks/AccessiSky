"""Location settings dialog."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import wx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Common city presets for quick selection
CITY_PRESETS = [
    ("New York, USA", 40.7128, -74.0060),
    ("Los Angeles, USA", 34.0522, -118.2437),
    ("Chicago, USA", 41.8781, -87.6298),
    ("London, UK", 51.5074, -0.1278),
    ("Paris, France", 48.8566, 2.3522),
    ("Berlin, Germany", 52.5200, 13.4050),
    ("Tokyo, Japan", 35.6762, 139.6503),
    ("Sydney, Australia", -33.8688, 151.2093),
    ("Toronto, Canada", 43.6532, -79.3832),
    ("Minneapolis, USA", 44.9778, -93.2650),
]


@dataclass
class Location:
    """User location."""

    latitude: float
    longitude: float
    name: str = ""

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} ({self.latitude:.4f}, {self.longitude:.4f})"
        return f"{self.latitude:.4f}, {self.longitude:.4f}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Location:
        """Create from dictionary."""
        return cls(
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            name=data.get("name", ""),
        )


def get_config_path() -> Path:
    """Get the config file path."""
    # Use user's config directory
    if wx.Platform == "__WXMSW__":
        config_dir = Path.home() / "AppData" / "Local" / "AccessiSky"
    elif wx.Platform == "__WXMAC__":
        config_dir = Path.home() / "Library" / "Application Support" / "AccessiSky"
    else:
        config_dir = Path.home() / ".config" / "accessisky"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "location.json"


def load_location() -> Location | None:
    """Load saved location from config."""
    config_path = get_config_path()
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            data = json.load(f)
            return Location.from_dict(data)
    except Exception as e:
        logger.error(f"Failed to load location: {e}")
        return None


def save_location(location: Location) -> bool:
    """Save location to config."""
    config_path = get_config_path()
    try:
        with open(config_path, "w") as f:
            json.dump(location.to_dict(), f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save location: {e}")
        return False


class LocationDialog(wx.Dialog):
    """Dialog for setting user location."""

    def __init__(self, parent: wx.Window | None, current_location: Location | None = None):
        """Initialize the location dialog."""
        super().__init__(
            parent,
            title="Set Location",
            size=(450, 350),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.location: Location | None = current_location
        self._create_ui()
        self._bind_events()

        if current_location:
            self._populate_from_location(current_location)

        self.Centre()

    def _create_ui(self) -> None:
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Enter your location coordinates or select a city preset.\n"
            "This is used to calculate sunrise/sunset times, ISS passes, etc.",
        )
        instructions.SetName("Location dialog instructions")
        main_sizer.Add(instructions, 0, wx.ALL | wx.EXPAND, 10)

        # City preset dropdown
        preset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        preset_label = wx.StaticText(panel, label="City &Preset:")
        self.preset_choice = wx.Choice(
            panel,
            choices=["Custom"] + [name for name, _, _ in CITY_PRESETS],
        )
        self.preset_choice.SetSelection(0)
        self.preset_choice.SetName("City preset selector")

        preset_sizer.Add(preset_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        preset_sizer.Add(self.preset_choice, 1, wx.EXPAND)
        main_sizer.Add(preset_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Latitude input
        lat_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lat_label = wx.StaticText(panel, label="&Latitude:")
        lat_label.SetMinSize((80, -1))
        self.lat_input = wx.TextCtrl(panel, value="0.0")
        self.lat_input.SetName("Latitude in degrees, negative for south")
        lat_hint = wx.StaticText(panel, label="(-90 to 90)")
        lat_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        lat_sizer.Add(lat_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        lat_sizer.Add(self.lat_input, 1, wx.EXPAND | wx.RIGHT, 5)
        lat_sizer.Add(lat_hint, 0, wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(lat_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        main_sizer.AddSpacer(5)

        # Longitude input
        lon_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lon_label = wx.StaticText(panel, label="L&ongitude:")
        lon_label.SetMinSize((80, -1))
        self.lon_input = wx.TextCtrl(panel, value="0.0")
        self.lon_input.SetName("Longitude in degrees, negative for west")
        lon_hint = wx.StaticText(panel, label="(-180 to 180)")
        lon_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        lon_sizer.Add(lon_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        lon_sizer.Add(self.lon_input, 1, wx.EXPAND | wx.RIGHT, 5)
        lon_sizer.Add(lon_hint, 0, wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(lon_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        main_sizer.AddSpacer(5)

        # Location name (optional)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(panel, label="&Name:")
        name_label.SetMinSize((80, -1))
        self.name_input = wx.TextCtrl(panel, value="")
        self.name_input.SetName("Location name, optional")
        name_hint = wx.StaticText(panel, label="(optional)")
        name_hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        name_sizer.Add(self.name_input, 1, wx.EXPAND | wx.RIGHT, 5)
        name_sizer.Add(name_hint, 0, wx.ALIGN_CENTER_VERTICAL)
        main_sizer.Add(name_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        main_sizer.AddStretchSpacer()

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(panel, wx.ID_OK, "&Save")
        self.ok_btn.SetDefault()
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "&Cancel")

        btn_sizer.AddButton(self.ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.preset_choice.Bind(wx.EVT_CHOICE, self._on_preset_selected)
        self.ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)

    def _on_preset_selected(self, event: wx.CommandEvent) -> None:
        """Handle city preset selection."""
        selection = self.preset_choice.GetSelection()
        if selection > 0:  # Not "Custom"
            name, lat, lon = CITY_PRESETS[selection - 1]
            self.lat_input.SetValue(str(lat))
            self.lon_input.SetValue(str(lon))
            self.name_input.SetValue(name)

    def _populate_from_location(self, loc: Location) -> None:
        """Populate fields from existing location."""
        self.lat_input.SetValue(str(loc.latitude))
        self.lon_input.SetValue(str(loc.longitude))
        self.name_input.SetValue(loc.name)

        # Try to match a preset
        for i, (_name, lat, lon) in enumerate(CITY_PRESETS):
            if abs(lat - loc.latitude) < 0.01 and abs(lon - loc.longitude) < 0.01:
                self.preset_choice.SetSelection(i + 1)
                break

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Handle OK button click."""
        try:
            lat = float(self.lat_input.GetValue())
            lon = float(self.lon_input.GetValue())
        except ValueError:
            wx.MessageBox(
                "Please enter valid numbers for latitude and longitude.",
                "Invalid Input",
                wx.OK | wx.ICON_ERROR,
            )
            return

        # Validate ranges
        if not -90 <= lat <= 90:
            wx.MessageBox(
                "Latitude must be between -90 and 90 degrees.",
                "Invalid Latitude",
                wx.OK | wx.ICON_ERROR,
            )
            self.lat_input.SetFocus()
            return

        if not -180 <= lon <= 180:
            wx.MessageBox(
                "Longitude must be between -180 and 180 degrees.",
                "Invalid Longitude",
                wx.OK | wx.ICON_ERROR,
            )
            self.lon_input.SetFocus()
            return

        self.location = Location(
            latitude=lat,
            longitude=lon,
            name=self.name_input.GetValue().strip(),
        )

        # Save to config
        save_location(self.location)

        self.EndModal(wx.ID_OK)

    def get_location(self) -> Location | None:
        """Get the entered location."""
        return self.location
