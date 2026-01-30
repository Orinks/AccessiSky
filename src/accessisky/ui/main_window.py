"""Main window for AccessiSky."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import wx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


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

        self._create_menu()
        self._create_ui()
        self._bind_events()
        self._setup_accessibility()

        # Center on screen
        self.Centre()

    def _create_menu(self) -> None:
        """Create the menu bar."""
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_REFRESH, "&Refresh\tCtrl+R", "Refresh all data")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_PREFERENCES, "&Settings\tCtrl+,", "Open settings")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit AccessiSky")
        menubar.Append(file_menu, "&File")

        # View menu
        view_menu = wx.Menu()
        self.iss_menu_item = view_menu.Append(
            wx.ID_ANY, "&ISS Tracker\tF1", "View ISS position and passes"
        )
        self.satellites_menu_item = view_menu.Append(
            wx.ID_ANY, "&Satellites\tF2", "View satellite passes"
        )
        self.moon_menu_item = view_menu.Append(
            wx.ID_ANY, "&Moon Phases\tF3", "View moon phase information"
        )
        self.sun_menu_item = view_menu.Append(
            wx.ID_ANY, "S&un Times\tF4", "View sunrise and sunset"
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
        self.status_label = wx.StaticText(
            panel, label="Welcome to AccessiSky - Loading data..."
        )
        self.status_label.SetFont(
            self.status_label.GetFont().Bold().Scaled(1.2)
        )
        main_sizer.Add(self.status_label, 0, wx.ALL | wx.EXPAND, 10)

        # Notebook for different views
        self.notebook = wx.Notebook(panel)

        # ISS Tab
        self.iss_panel = self._create_iss_panel(self.notebook)
        self.notebook.AddPage(self.iss_panel, "ISS Tracker")

        # Moon Tab
        self.moon_panel = self._create_moon_panel(self.notebook)
        self.notebook.AddPage(self.moon_panel, "Moon Phases")

        # Sun Tab
        self.sun_panel = self._create_sun_panel(self.notebook)
        self.notebook.AddPage(self.sun_panel, "Sun Times")

        main_sizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 10)

        # Location info at bottom
        location_sizer = wx.BoxSizer(wx.HORIZONTAL)
        location_label = wx.StaticText(panel, label="Location:")
        self.location_text = wx.TextCtrl(
            panel, value="Not set - Click to set location", style=wx.TE_READONLY
        )
        self.location_text.SetName("Current location")
        self.set_location_btn = wx.Button(panel, label="Set &Location")
        
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
        pos_label.SetFont(pos_label.GetFont().Bold())
        sizer.Add(pos_label, 0, wx.ALL, 5)

        self.iss_position_text = wx.TextCtrl(
            panel,
            value="Loading ISS position...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 60),
        )
        self.iss_position_text.SetName("ISS current position")
        sizer.Add(self.iss_position_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming passes
        passes_label = wx.StaticText(panel, label="Upcoming Visible Passes")
        passes_label.SetFont(passes_label.GetFont().Bold())
        sizer.Add(passes_label, 0, wx.ALL, 5)

        self.iss_passes_list = wx.ListBox(panel)
        self.iss_passes_list.SetName("ISS pass predictions")
        sizer.Add(self.iss_passes_list, 1, wx.ALL | wx.EXPAND, 5)

        # Refresh button
        refresh_btn = wx.Button(panel, label="&Refresh ISS Data")
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
        phase_label.SetFont(phase_label.GetFont().Bold())
        sizer.Add(phase_label, 0, wx.ALL, 5)

        self.moon_phase_text = wx.TextCtrl(
            panel,
            value="Loading moon data...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 100),
        )
        self.moon_phase_text.SetName("Current moon phase information")
        sizer.Add(self.moon_phase_text, 0, wx.ALL | wx.EXPAND, 5)

        # Upcoming events
        events_label = wx.StaticText(panel, label="Upcoming Lunar Events")
        events_label.SetFont(events_label.GetFont().Bold())
        sizer.Add(events_label, 0, wx.ALL, 5)

        self.moon_events_list = wx.ListBox(panel)
        self.moon_events_list.SetName("Upcoming moon events")
        sizer.Add(self.moon_events_list, 1, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_sun_panel(self, parent: wx.Window) -> wx.Panel:
        """Create the sun times panel."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Today's times
        today_label = wx.StaticText(panel, label="Today's Sun Times")
        today_label.SetFont(today_label.GetFont().Bold())
        sizer.Add(today_label, 0, wx.ALL, 5)

        self.sun_times_text = wx.TextCtrl(
            panel,
            value="Loading sun times...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 150),
        )
        self.sun_times_text.SetName("Today's sunrise and sunset times")
        sizer.Add(self.sun_times_text, 0, wx.ALL | wx.EXPAND, 5)

        # Day length info
        length_label = wx.StaticText(panel, label="Day Length Information")
        length_label.SetFont(length_label.GetFont().Bold())
        sizer.Add(length_label, 0, wx.ALL, 5)

        self.day_length_text = wx.TextCtrl(
            panel,
            value="Calculating...",
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            size=(-1, 80),
        )
        self.day_length_text.SetName("Day length information")
        sizer.Add(self.day_length_text, 0, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(sizer)
        return panel

    def _bind_events(self) -> None:
        """Bind event handlers."""
        self.Bind(wx.EVT_MENU, self._on_refresh, id=wx.ID_REFRESH)
        self.Bind(wx.EVT_MENU, self._on_settings, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self._on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self._on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        
        self.set_location_btn.Bind(wx.EVT_BUTTON, self._on_set_location)

    def _setup_accessibility(self) -> None:
        """Set up accessibility features."""
        # Set accessible names for key controls
        self.notebook.SetName("Sky data views")
        
        # Ensure focus starts in a sensible place
        self.notebook.SetFocus()

    def _on_refresh(self, event: wx.CommandEvent) -> None:
        """Handle refresh request."""
        self.SetStatusText("Refreshing all data...")
        logger.info("Refreshing all data")
        # TODO: Implement data refresh

    def _on_refresh_iss(self, event: wx.CommandEvent) -> None:
        """Handle ISS refresh request."""
        self.SetStatusText("Refreshing ISS data...")
        logger.info("Refreshing ISS data")
        # TODO: Implement ISS data refresh

    def _on_settings(self, event: wx.CommandEvent) -> None:
        """Open settings dialog."""
        wx.MessageBox(
            "Settings dialog coming soon!",
            "Settings",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_set_location(self, event: wx.CommandEvent) -> None:
        """Open location setting dialog."""
        wx.MessageBox(
            "Location dialog coming soon!",
            "Set Location",
            wx.OK | wx.ICON_INFORMATION,
        )

    def _on_about(self, event: wx.CommandEvent) -> None:
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("AccessiSky")
        info.SetVersion("0.1.0")
        info.SetDescription(
            "Accessible sky tracking application.\n\n"
            "Track ISS passes, satellites, moon phases, and more\n"
            "with full screen reader support."
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
        self.Destroy()
