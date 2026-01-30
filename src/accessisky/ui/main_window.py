"""Main window for AccessiSky."""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

import wx
import wx.adv

from ..api.aurora import AuroraClient
from ..api.eclipses import EclipseClient, get_upcoming_eclipses
from ..api.iss import ISSClient
from ..api.meteors import MeteorClient, get_active_showers, get_upcoming_showers
from ..api.moon import MoonClient
from ..api.planets import PlanetClient, get_visible_planets
from ..api.sun import SunClient
from .dialogs.location import Location, LocationDialog, load_location

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run an async coroutine from sync code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class MainWindow(wx.Frame):
    """Main application window with full accessibility support."""

    def __init__(self, parent: wx.Window | None):
        """Initialize the main window."""
        super().__init__(
            parent,
            title="AccessiSky - Sky Tracker",
            size=(800, 600),
            style=wx.DEFAULT_FRAME_STYLE,
        )

        # Initialize API clients
        self.iss_client = ISSClient()
        self.sun_client = SunClient()
        self.moon_client = MoonClient()
        self.aurora_client = AuroraClient()
        self.meteor_client = MeteorClient()
        self.planet_client = PlanetClient()
        self.eclipse_client = EclipseClient()

        # Load saved location
        self.location: Location | None = load_location()

        self._create_menu()
        self._create_ui()
        self._bind_events()
        self._setup_accessibility()

        # Center on screen
        self.Centre()

        # Load initial data
        wx.CallAfter(self._load_all_data)

    def _create_menu(self) -> None:
        """Create the menu bar."""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_REFRESH, "&Refresh\tCtrl+R", "Refresh all data")
        file_menu.AppendSeparator()
        self.location_menu_item = file_menu.Append(
            wx.ID_ANY, "Set &Location\tCtrl+L", "Set your location"
        )
        file_menu.Append(wx.ID_PREFERENCES, "&Settings\tCtrl+,", "Open settings")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit AccessiSky")
        menubar.Append(file_menu, "&File")

        # View menu
        view_menu = wx.Menu()
        self.iss_menu_item = view_menu.Append(
            wx.ID_ANY, "&ISS Tracker\tF1", "View ISS position and passes"
        )
        self.moon_menu_item = view_menu.Append(
            wx.ID_ANY, "&Moon Phases\tF2", "View moon phase information"
        )
        self.sun_menu_item = view_menu.Append(
            wx.ID_ANY, "S&un Times\tF3", "View sunrise and sunset"
        )
        self.aurora_menu_item = view_menu.Append(
            wx.ID_ANY, "&Aurora Forecast\tF4", "View space weather and aurora"
        )
        view_menu.AppendSeparator()
        self.meteor_menu_item = view_menu.Append(
            wx.ID_ANY, "&Meteor Showers\tF5", "View meteor shower calendar"
        )
        self.planets_menu_item = view_menu.Append(wx.ID_ANY, "&Planets\tF6", "View visible planets")
        self.eclipse_menu_item = view_menu.Append(
            wx.ID_ANY, "&Eclipses\tF7", "View upcoming eclipses"
        )
        menubar.Append(view_menu, "&View")

        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About", "About AccessiSky")
        menubar.Append(help_menu, "&Help")

        self.SetMenuBar(menubar)

    def _create_ui(self) -> None:
        """Create the main UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Status text at top
        self.status_label = wx.StaticText(panel, label="Welcome to AccessiSky - Loading data...")
        self.status_label.SetName("Application status")
        self.status_label.SetFont(self.status_label.GetFont().Bold().Scaled(1.2))
        main_sizer.Add(self.status_label, 0, wx.ALL | wx.EXPAND, 10)

        # Notebook for different views
        self.notebook = wx.Notebook(panel)
        self.notebook.SetName("Data views - use Ctrl+Tab to switch tabs")

        # ISS Tab
        self.iss_panel = self._create_iss_panel(self.notebook)
        self.notebook.AddPage(self.iss_panel, "ISS Tracker")

        # Moon Tab
        self.moon_panel = self._create_moon_panel(self.notebook)
        self.notebook.AddPage(self.moon_panel, "Moon Phases")

        # Sun Tab
        self.sun_panel = self._create_sun_panel(self.notebook)
        self.notebook.AddPage(self.sun_panel, "Sun Times")

        # Aurora Tab
        self.aurora_panel = self._create_aurora_panel(self.notebook)
        self.notebook.AddPage(self.aurora_panel, "Aurora & Space Weather")

        # Meteor Showers Tab
        self.meteor_panel = self._create_meteor_panel(self.notebook)
        self.notebook.AddPage(self.meteor_panel, "Meteor Showers")

        # Planets Tab
        self.planets_panel = self._create_planets_panel(self.notebook)
        self.notebook.AddPage(self.planets_panel, "Planets")

        # Eclipses Tab
        self.eclipse_panel = self._create_eclipse_panel(self.notebook)
        self.notebook.AddPage(self.eclipse_panel, "Eclipses")

        main_sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 10)

        # Location info at bottom
        location_sizer = wx.BoxSizer(wx.HORIZONTAL)
        location_label = wx.StaticText(panel, label="Location:")
        self.location_text = wx.TextCtrl(
            panel,
            value=str(self.location) if self.location else "Not set - Click Set Location",
            style=wx.TE_READONLY,
        )
        self.location_text.SetName("Current location for calculations")
        self.set_location_btn = wx.Button(panel, label="Set &Location")
        self.set_location_btn.SetName("Open location settings dialog")

        location_sizer.Add(location_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        location_sizer.Add(self.location_text, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        location_sizer.Add(self.set_location_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        main_sizer.Add(location_sizer, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(main_sizer)

        # Status bar
        self.CreateStatusBar()
        self.SetStatusText("Ready")

    def _create_iss_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the ISS tracking panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Current position
        pos_label = wx.StaticText(panel, label="Current ISS Position")
        pos_label.SetName("Section: Current ISS Position")
        pos_label.SetFont(pos_label.GetFont().Bold())
        sizer.Add(pos_label, 0, wx.ALL, 5)

        self.iss_position_text = wx.TextCtrl(
            panel,
            value="Loading ISS position...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80),
        )
        self.iss_position_text.SetName("ISS current position and details")
        sizer.Add(self.iss_position_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming passes
        passes_label = wx.StaticText(panel, label="Upcoming Visible Passes")
        passes_label.SetName("Section: Upcoming Visible Passes")
        passes_label.SetFont(passes_label.GetFont().Bold())
        sizer.Add(passes_label, 0, wx.ALL, 5)

        self.iss_passes_list = wx.ListBox(panel)
        self.iss_passes_list.SetName("List of upcoming ISS pass predictions")
        sizer.Add(self.iss_passes_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh ISS Data")
        refresh_btn.SetName("Refresh ISS position and pass predictions")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_iss)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_moon_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the moon phases panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Current phase
        phase_label = wx.StaticText(panel, label="Current Moon Phase")
        phase_label.SetName("Section: Current Moon Phase")
        phase_label.SetFont(phase_label.GetFont().Bold())
        sizer.Add(phase_label, 0, wx.ALL, 5)

        self.moon_phase_text = wx.TextCtrl(
            panel,
            value="Loading moon data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 120),
        )
        self.moon_phase_text.SetName("Current moon phase, illumination, and details")
        sizer.Add(self.moon_phase_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming events
        events_label = wx.StaticText(panel, label="Upcoming Lunar Events")
        events_label.SetName("Section: Upcoming Lunar Events")
        events_label.SetFont(events_label.GetFont().Bold())
        sizer.Add(events_label, 0, wx.ALL, 5)

        self.moon_events_list = wx.ListBox(panel)
        self.moon_events_list.SetName("List of upcoming moon phases and events")
        sizer.Add(self.moon_events_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Moon Data")
        refresh_btn.SetName("Refresh moon phase information")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_moon)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_sun_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the sun times panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Today's times
        today_label = wx.StaticText(panel, label="Today's Sun Times")
        today_label.SetName("Section: Today's Sun Times")
        today_label.SetFont(today_label.GetFont().Bold())
        sizer.Add(today_label, 0, wx.ALL, 5)

        self.sun_times_text = wx.TextCtrl(
            panel,
            value="Set location to see sun times",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 200),
        )
        self.sun_times_text.SetName("Today's sunrise, sunset, and twilight times")
        sizer.Add(self.sun_times_text, 0, wx.ALL | wx.EXPAND, 5)

        # Day length info
        length_label = wx.StaticText(panel, label="Day Length Information")
        length_label.SetName("Section: Day Length Information")
        length_label.SetFont(length_label.GetFont().Bold())
        sizer.Add(length_label, 0, wx.ALL, 5)

        self.day_length_text = wx.TextCtrl(
            panel,
            value="Calculating...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80),
        )
        self.day_length_text.SetName("Day length and solar information")
        sizer.Add(self.day_length_text, 0, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Sun Data")
        refresh_btn.SetName("Refresh sun times")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_sun)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_aurora_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the aurora/space weather panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Current conditions
        conditions_label = wx.StaticText(panel, label="Current Space Weather")
        conditions_label.SetName("Section: Current Space Weather")
        conditions_label.SetFont(conditions_label.GetFont().Bold())
        sizer.Add(conditions_label, 0, wx.ALL, 5)

        self.aurora_text = wx.TextCtrl(
            panel,
            value="Loading space weather data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 150),
        )
        self.aurora_text.SetName("Current Kp index, geomagnetic activity, and aurora visibility")
        sizer.Add(self.aurora_text, 0, wx.ALL | wx.EXPAND, 5)

        # Solar wind
        solar_label = wx.StaticText(panel, label="Solar Wind Conditions")
        solar_label.SetName("Section: Solar Wind Conditions")
        solar_label.SetFont(solar_label.GetFont().Bold())
        sizer.Add(solar_label, 0, wx.ALL, 5)

        self.solar_wind_text = wx.TextCtrl(
            panel,
            value="Loading solar wind data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80),
        )
        self.solar_wind_text.SetName("Current solar wind speed and density")
        sizer.Add(self.solar_wind_text, 0, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Space Weather")
        refresh_btn.SetName("Refresh aurora and space weather data")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_aurora)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_meteor_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the meteor showers panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Active showers
        active_label = wx.StaticText(panel, label="Active Meteor Showers")
        active_label.SetName("Section: Active Meteor Showers")
        active_label.SetFont(active_label.GetFont().Bold())
        sizer.Add(active_label, 0, wx.ALL, 5)

        self.active_showers_text = wx.TextCtrl(
            panel,
            value="Loading meteor shower data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 100),
        )
        self.active_showers_text.SetName("Currently active meteor showers")
        sizer.Add(self.active_showers_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming showers
        upcoming_label = wx.StaticText(panel, label="Upcoming Meteor Showers")
        upcoming_label.SetName("Section: Upcoming Meteor Showers")
        upcoming_label.SetFont(upcoming_label.GetFont().Bold())
        sizer.Add(upcoming_label, 0, wx.ALL, 5)

        self.meteor_list = wx.ListBox(panel)
        self.meteor_list.SetName("List of upcoming meteor showers with peak dates")
        sizer.Add(self.meteor_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Meteor Data")
        refresh_btn.SetName("Refresh meteor shower information")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_meteors)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_planets_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the planets visibility panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Visible planets
        visible_label = wx.StaticText(panel, label="Visible Planets Tonight")
        visible_label.SetName("Section: Visible Planets Tonight")
        visible_label.SetFont(visible_label.GetFont().Bold())
        sizer.Add(visible_label, 0, wx.ALL, 5)

        self.planets_text = wx.TextCtrl(
            panel,
            value="Loading planet visibility data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 200),
        )
        self.planets_text.SetName("List of planets visible tonight with viewing times")
        sizer.Add(self.planets_text, 0, wx.ALL | wx.EXPAND, 5)

        # Planet list
        self.planets_list = wx.ListBox(panel)
        self.planets_list.SetName("Detailed planet visibility information")
        sizer.Add(self.planets_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Planet Data")
        refresh_btn.SetName("Refresh planet visibility")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_planets)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_eclipse_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the eclipses panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Next eclipse
        next_label = wx.StaticText(panel, label="Next Eclipse")
        next_label.SetName("Section: Next Eclipse")
        next_label.SetFont(next_label.GetFont().Bold())
        sizer.Add(next_label, 0, wx.ALL, 5)

        self.next_eclipse_text = wx.TextCtrl(
            panel,
            value="Loading eclipse data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 100),
        )
        self.next_eclipse_text.SetName("Information about the next upcoming eclipse")
        sizer.Add(self.next_eclipse_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming eclipses list
        upcoming_label = wx.StaticText(panel, label="Upcoming Eclipses (2025-2030)")
        upcoming_label.SetName("Section: Upcoming Eclipses")
        upcoming_label.SetFont(upcoming_label.GetFont().Bold())
        sizer.Add(upcoming_label, 0, wx.ALL, 5)

        self.eclipse_list = wx.ListBox(panel)
        self.eclipse_list.SetName("List of upcoming solar and lunar eclipses")
        sizer.Add(self.eclipse_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh Eclipse Data")
        refresh_btn.SetName("Refresh eclipse calendar")
        refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh_eclipses)
        sizer.Add(refresh_btn, 0, wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.Bind(wx.EVT_MENU, self._on_refresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_MENU, self._on_settings, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self._on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self._on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self._on_set_location, id=self.location_menu_item.GetId())
        self.Bind(wx.EVT_CLOSE, self._on_close)

        # View menu shortcuts
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(0), id=self.iss_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(1), id=self.moon_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(2), id=self.sun_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(3), id=self.aurora_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(4), id=self.meteor_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(5), id=self.planets_menu_item.GetId()
        )
        self.Bind(
            wx.EVT_MENU, lambda e: self.notebook.SetSelection(6), id=self.eclipse_menu_item.GetId()
        )

        self.set_location_btn.Bind(wx.EVT_BUTTON, self._on_set_location)

    def _setup_accessibility(self) -> None:
        """Set up accessibility features."""
        # Ensure focus starts in a sensible place
        self.notebook.SetFocus()

    def _load_all_data(self) -> None:
        """Load all data in background."""
        self.SetStatusText("Loading data...")
        self.status_label.SetLabel("Loading data from APIs...")

        # Run async loading in a background thread
        def load():
            try:
                self._load_iss_data()
                self._load_moon_data()
                self._load_sun_data()
                self._load_aurora_data()
                self._load_meteor_data()
                self._load_planet_data()
                self._load_eclipse_data()
                wx.CallAfter(self._on_data_loaded)
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                wx.CallAfter(self._on_data_error, str(e))

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def _on_data_loaded(self) -> None:
        """Called when all data is loaded."""
        self.status_label.SetLabel("Data loaded successfully")
        self.SetStatusText("Ready")

    def _on_data_error(self, error: str) -> None:
        """Called when data loading fails."""
        self.status_label.SetLabel(f"Error loading data: {error}")
        self.SetStatusText("Error loading data")

    def _load_iss_data(self) -> None:
        """Load ISS data."""

        async def fetch():
            position = await self.iss_client.get_current_position()
            return position

        try:
            position = run_async(fetch())
            if position:
                text = (
                    f"Latitude: {position.latitude:.4f}°\n"
                    f"Longitude: {position.longitude:.4f}°\n"
                    f"Altitude: ~{position.altitude:.0f} km\n"
                    f"Velocity: ~{position.velocity:.2f} km/s\n"
                    f"Updated: {position.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                wx.CallAfter(self.iss_position_text.SetValue, text)

                # Note about passes
                if self.location:
                    wx.CallAfter(
                        self.iss_passes_list.Set,
                        ["Pass predictions require N2YO API key (not implemented)"],
                    )
                else:
                    wx.CallAfter(
                        self.iss_passes_list.Set,
                        ["Set your location to see ISS pass predictions"],
                    )
            else:
                wx.CallAfter(self.iss_position_text.SetValue, "Failed to load ISS position")
        except Exception as e:
            logger.error(f"ISS data error: {e}")
            wx.CallAfter(self.iss_position_text.SetValue, f"Error: {e}")

    def _load_moon_data(self) -> None:
        """Load moon data."""

        async def fetch():
            info = await self.moon_client.get_moon_info()
            events = await self.moon_client.get_upcoming_events(days=30)
            return info, events

        try:
            info, events = run_async(fetch())

            text = (
                f"Phase: {info.phase_emoji} {info.phase.value}\n"
                f"Illumination: {info.illumination_percent}%\n"
                f"Age: {info.age_days:.1f} days since new moon\n"
                f"\n{info}"
            )
            wx.CallAfter(self.moon_phase_text.SetValue, text)

            event_strings = [str(e) for e in events]
            if not event_strings:
                event_strings = ["No upcoming events found"]
            wx.CallAfter(self.moon_events_list.Set, event_strings)

        except Exception as e:
            logger.error(f"Moon data error: {e}")
            wx.CallAfter(self.moon_phase_text.SetValue, f"Error: {e}")

    def _load_sun_data(self) -> None:
        """Load sun data."""
        if not self.location:
            wx.CallAfter(
                self.sun_times_text.SetValue,
                "Please set your location to see sun times.\n\nClick 'Set Location' below or use Ctrl+L.",
            )
            wx.CallAfter(self.day_length_text.SetValue, "Location not set")
            return

        async def fetch():
            return await self.sun_client.get_sun_times(
                self.location.latitude,
                self.location.longitude,
            )

        try:
            times = run_async(fetch())
            if times:
                text = (
                    f"Sunrise: {times.sunrise.strftime('%H:%M:%S UTC')}\n"
                    f"Sunset: {times.sunset.strftime('%H:%M:%S UTC')}\n"
                    f"Solar Noon: {times.solar_noon.strftime('%H:%M:%S UTC')}\n"
                    f"\nTwilight Times:\n"
                    f"Civil: {times.civil_twilight_begin.strftime('%H:%M')} - {times.civil_twilight_end.strftime('%H:%M')}\n"
                    f"Nautical: {times.nautical_twilight_begin.strftime('%H:%M')} - {times.nautical_twilight_end.strftime('%H:%M')}\n"
                    f"Astronomical: {times.astronomical_twilight_begin.strftime('%H:%M')} - {times.astronomical_twilight_end.strftime('%H:%M')}\n"
                    f"\nGolden Hour:\n"
                    f"Morning: until {times.golden_hour_morning_end.strftime('%H:%M')}\n"
                    f"Evening: from {times.golden_hour_evening_start.strftime('%H:%M')}"
                )
                wx.CallAfter(self.sun_times_text.SetValue, text)

                length_text = (
                    f"Day Length: {times.day_length}\n({times.day_length_seconds} seconds)"
                )
                wx.CallAfter(self.day_length_text.SetValue, length_text)
            else:
                wx.CallAfter(self.sun_times_text.SetValue, "Failed to load sun times")
        except Exception as e:
            logger.error(f"Sun data error: {e}")
            wx.CallAfter(self.sun_times_text.SetValue, f"Error: {e}")

    def _load_aurora_data(self) -> None:
        """Load aurora/space weather data."""

        async def fetch():
            forecast = await self.aurora_client.get_aurora_forecast()
            solar_wind = await self.aurora_client.get_solar_wind()
            return forecast, solar_wind

        try:
            forecast, solar_wind = run_async(fetch())

            if forecast:
                text = (
                    f"Current Kp Index: {forecast.kp_current:.1f}\n"
                    f"24-Hour Max Kp: {forecast.kp_24h_max:.1f}\n"
                    f"Activity Level: {forecast.activity.name}\n"
                    f"\n{forecast.description}\n"
                    f"\nAurora Visibility:\n{forecast.can_see_aurora}\n"
                    f"Visible down to ~{forecast.visibility_latitude:.0f}° latitude"
                )
                wx.CallAfter(self.aurora_text.SetValue, text)
            else:
                wx.CallAfter(self.aurora_text.SetValue, "Failed to load aurora forecast")

            if solar_wind:
                elevated = " (ELEVATED!)" if solar_wind.is_elevated else ""
                text = (
                    f"Speed: {solar_wind.speed_km_s:.0f} km/s{elevated}\n"
                    f"Density: {solar_wind.density_p_cm3:.1f} protons/cm³\n"
                    f"Updated: {solar_wind.timestamp.strftime('%H:%M UTC')}"
                )
                wx.CallAfter(self.solar_wind_text.SetValue, text)
            else:
                wx.CallAfter(self.solar_wind_text.SetValue, "Failed to load solar wind data")

        except Exception as e:
            logger.error(f"Aurora data error: {e}")
            wx.CallAfter(self.aurora_text.SetValue, f"Error: {e}")

    def _on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh request."""
        self._load_all_data()

    def _on_refresh_iss(self, event: wx.CommandEvent) -> None:
        """Handle ISS refresh request."""
        self.SetStatusText("Refreshing ISS data...")
        thread = threading.Thread(target=self._load_iss_data, daemon=True)
        thread.start()

    def _on_refresh_moon(self, event: wx.CommandEvent) -> None:
        """Handle moon refresh request."""
        self.SetStatusText("Refreshing moon data...")
        thread = threading.Thread(target=self._load_moon_data, daemon=True)
        thread.start()

    def _on_refresh_sun(self, event: wx.CommandEvent) -> None:
        """Handle sun refresh request."""
        self.SetStatusText("Refreshing sun data...")
        thread = threading.Thread(target=self._load_sun_data, daemon=True)
        thread.start()

    def _on_refresh_aurora(self, event: wx.CommandEvent) -> None:
        """Handle aurora refresh request."""
        self.SetStatusText("Refreshing space weather data...")
        thread = threading.Thread(target=self._load_aurora_data, daemon=True)
        thread.start()

    def _load_meteor_data(self) -> None:
        """Load meteor shower data."""
        try:
            # Get active showers
            active = get_active_showers()
            if active:
                active_text = "\n".join([str(s) for s in active])
            else:
                active_text = "No meteor showers currently active"
            wx.CallAfter(self.active_showers_text.SetValue, active_text)

            # Get upcoming showers
            upcoming = get_upcoming_showers(days=90)
            upcoming_strings = [str(s) for s in upcoming]
            if not upcoming_strings:
                upcoming_strings = ["No upcoming meteor showers in next 90 days"]
            wx.CallAfter(self.meteor_list.Set, upcoming_strings)

        except Exception as e:
            logger.error(f"Meteor data error: {e}")
            wx.CallAfter(self.active_showers_text.SetValue, f"Error: {e}")

    def _on_refresh_meteors(self, event: wx.CommandEvent) -> None:
        """Handle meteor refresh request."""
        self.SetStatusText("Refreshing meteor shower data...")
        thread = threading.Thread(target=self._load_meteor_data, daemon=True)
        thread.start()

    def _load_planet_data(self) -> None:
        """Load planet visibility data."""
        try:
            visible = get_visible_planets()

            if visible:
                summary_lines = []
                detail_lines = []

                for planet in visible:
                    summary_lines.append(f"• {planet.planet.name}: {planet.visibility.value}")
                    detail_lines.append(str(planet))

                summary_text = "Visible Planets Tonight:\n\n" + "\n".join(summary_lines)
                wx.CallAfter(self.planets_text.SetValue, summary_text)
                wx.CallAfter(self.planets_list.Set, detail_lines)
            else:
                wx.CallAfter(
                    self.planets_text.SetValue,
                    "No planets currently visible (all too close to the Sun)",
                )
                wx.CallAfter(self.planets_list.Set, [])

        except Exception as e:
            logger.error(f"Planet data error: {e}")
            wx.CallAfter(self.planets_text.SetValue, f"Error: {e}")

    def _on_refresh_planets(self, event: wx.CommandEvent) -> None:
        """Handle planet refresh request."""
        self.SetStatusText("Refreshing planet visibility...")
        thread = threading.Thread(target=self._load_planet_data, daemon=True)
        thread.start()

    def _load_eclipse_data(self) -> None:
        """Load eclipse data."""
        try:
            upcoming = get_upcoming_eclipses(years=5)

            if upcoming:
                # Show next eclipse details
                next_eclipse = upcoming[0]
                next_text = (
                    f"{next_eclipse.eclipse_type.emoji} {next_eclipse.eclipse_type.value}\n"
                    f"Date: {next_eclipse.date.strftime('%B %d, %Y')}\n"
                    f"Time: {next_eclipse.max_time.strftime('%H:%M UTC')}\n"
                )
                if next_eclipse.duration_minutes:
                    mins = int(next_eclipse.duration_minutes)
                    secs = int((next_eclipse.duration_minutes - mins) * 60)
                    next_text += f"Duration: {mins}m {secs}s\n"
                if next_eclipse.visibility_regions:
                    regions = ", ".join(next_eclipse.visibility_regions[:5])
                    next_text += f"Visible from: {regions}"
                if next_eclipse.notes:
                    next_text += f"\n\nNote: {next_eclipse.notes}"

                wx.CallAfter(self.next_eclipse_text.SetValue, next_text)

                # Show list of all upcoming
                eclipse_strings = [str(e) for e in upcoming]
                wx.CallAfter(self.eclipse_list.Set, eclipse_strings)
            else:
                wx.CallAfter(self.next_eclipse_text.SetValue, "No eclipse data available")
                wx.CallAfter(self.eclipse_list.Set, [])

        except Exception as e:
            logger.error(f"Eclipse data error: {e}")
            wx.CallAfter(self.next_eclipse_text.SetValue, f"Error: {e}")

    def _on_refresh_eclipses(self, event: wx.CommandEvent) -> None:
        """Handle eclipse refresh request."""
        self.SetStatusText("Refreshing eclipse data...")
        thread = threading.Thread(target=self._load_eclipse_data, daemon=True)
        thread.start()

    def _on_settings(self, event: wx.CommandEvent) -> None:
        """Open settings dialog."""
        wx.MessageBox(
            "Settings dialog coming soon!",
            "Settings",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_set_location(self, event: wx.CommandEvent) -> None:
        """Open location setting dialog."""
        dialog = LocationDialog(self, self.location)
        if dialog.ShowModal() == wx.ID_OK:
            self.location = dialog.get_location()
            if self.location:
                self.location_text.SetValue(str(self.location))
                # Reload data that depends on location
                self._load_all_data()
        dialog.Destroy()

    def _on_about(self, event: wx.CommandEvent) -> None:
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("AccessiSky")
        info.SetVersion("0.1.0")
        info.SetDescription(
            "Accessible sky tracking application.\n\n"
            "Track ISS passes, moon phases, sun times,\n"
            "aurora forecasts, meteor showers, planets,\n"
            "eclipses, and more with full screen reader\n"
            "support."
        )
        info.SetCopyright("© 2026 Josh (Orinks)")
        info.SetWebSite("https://github.com/Orinks/AccessiSky")
        info.AddDeveloper("Josh (Orinks)")
        info.SetLicense("MIT License")

        wx.adv.AboutBox(info)

    def _on_exit(self, event: wx.CommandEvent) -> None:
        """Exit the application."""
        self.Close()

    def _on_close(self, event: wx.CloseEvent) -> None:
        """Handle window close."""
        logger.info("Main window closing")

        # Close API clients
        async def cleanup():
            await self.iss_client.close()
            await self.sun_client.close()
            await self.moon_client.close()
            await self.aurora_client.close()
            await self.meteor_client.close()
            await self.planet_client.close()
            await self.eclipse_client.close()

        try:
            run_async(cleanup())
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        self.Destroy()
