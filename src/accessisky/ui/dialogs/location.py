"""Location settings dialog with geocoding search."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import wx

from ...api.geocoding import GeocodingResult, search_location

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


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
    """Dialog for setting user location with search."""

    def __init__(self, parent: wx.Window | None, current_location: Location | None = None):
        """Initialize the location dialog."""
        super().__init__(
            parent,
            title="Set Location",
            size=(500, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        self.location: Location | None = current_location
        self.search_results: list[GeocodingResult] = []
        self._create_ui()
        self._bind_events()

        if current_location:
            self._show_current_location(current_location)

        self.Centre()
        self.search_input.SetFocus()

    def _create_ui(self) -> None:
        """Create the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Search for a city or location. Select from results below.",
        )
        instructions.SetName("Location search instructions")
        main_sizer.Add(instructions, 0, wx.ALL, 10)

        # Search box
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        search_label = wx.StaticText(panel, label="&Search:")
        self.search_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_input.SetName("Enter city or location name")
        self.search_btn = wx.Button(panel, label="&Find")

        search_sizer.Add(search_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        search_sizer.Add(self.search_input, 1, wx.EXPAND | wx.RIGHT, 5)
        search_sizer.Add(self.search_btn, 0)
        main_sizer.Add(search_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        main_sizer.AddSpacer(10)

        # Results list
        results_label = wx.StaticText(panel, label="&Results:")
        main_sizer.Add(results_label, 0, wx.LEFT | wx.RIGHT, 10)

        self.results_list = wx.ListBox(panel)
        self.results_list.SetName("Search results, select a location")
        main_sizer.Add(self.results_list, 1, wx.ALL | wx.EXPAND, 10)

        # Current selection display
        self.selection_text = wx.StaticText(panel, label="No location selected")
        self.selection_text.SetName("Currently selected location")
        main_sizer.Add(self.selection_text, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        main_sizer.AddSpacer(10)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        self.ok_btn = wx.Button(panel, wx.ID_OK, "&Save")
        self.ok_btn.SetDefault()
        self.ok_btn.Enable(False)  # Disabled until location selected
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "&Cancel")

        btn_sizer.AddButton(self.ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(main_sizer)

    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.search_btn.Bind(wx.EVT_BUTTON, self._on_search)
        self.search_input.Bind(wx.EVT_TEXT_ENTER, self._on_search)
        self.results_list.Bind(wx.EVT_LISTBOX, self._on_result_selected)
        self.results_list.Bind(wx.EVT_LISTBOX_DCLICK, self._on_result_double_click)
        self.ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)

    def _show_current_location(self, loc: Location) -> None:
        """Show the current location."""
        self.selection_text.SetLabel(f"Current: {loc}")
        self.ok_btn.Enable(True)

    def _on_search(self, event: wx.CommandEvent) -> None:
        """Handle search request."""
        query = self.search_input.GetValue().strip()
        if not query:
            return

        self.search_btn.Enable(False)
        self.search_btn.SetLabel("Searching...")
        self.results_list.Clear()

        # Run async search
        try:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(search_location(query))
            loop.close()

            self.search_results = results

            if results:
                for result in results:
                    self.results_list.Append(result.display_name)
                self.results_list.SetSelection(0)
                self._on_result_selected(None)
            else:
                self.results_list.Append("No results found")
                self.search_results = []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.results_list.Append(f"Search failed: {e}")
            self.search_results = []

        finally:
            self.search_btn.Enable(True)
            self.search_btn.SetLabel("&Find")

    def _on_result_selected(self, event: wx.CommandEvent | None) -> None:
        """Handle result selection."""
        selection = self.results_list.GetSelection()
        if selection == wx.NOT_FOUND or selection >= len(self.search_results):
            return

        result = self.search_results[selection]
        self.location = Location(
            latitude=result.latitude,
            longitude=result.longitude,
            name=result.display_name,
        )
        self.selection_text.SetLabel(
            f"Selected: {result.display_name}\n"
            f"Coordinates: {result.latitude:.4f}, {result.longitude:.4f}"
        )
        self.ok_btn.Enable(True)

    def _on_result_double_click(self, event: wx.CommandEvent) -> None:
        """Handle double-click on result - select and close."""
        self._on_result_selected(event)
        if self.location:
            self._on_ok(event)

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Handle OK button click."""
        if self.location:
            save_location(self.location)
            self.EndModal(wx.ID_OK)

    def get_location(self) -> Location | None:
        """Get the selected location."""
        return self.location
