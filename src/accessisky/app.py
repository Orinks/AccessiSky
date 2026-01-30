"""AccessiSky main application entry point."""

from __future__ import annotations

import logging
import sys

import wx

from .ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class AccessiSkyApp(wx.App):
    """Main AccessiSky application."""

    def OnInit(self) -> bool:
        """Initialize the application."""
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Create and show main window
        self.main_window = MainWindow(None)
        self.main_window.Show()
        self.SetTopWindow(self.main_window)

        logger.info("AccessiSky started")
        return True

    def OnExit(self) -> int:
        """Clean up on application exit."""
        logger.info("AccessiSky shutting down")
        return 0


def main() -> int:
    """Main entry point."""
    app = AccessiSkyApp()
    app.MainLoop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
