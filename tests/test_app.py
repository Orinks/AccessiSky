"""Tests for AccessiSky app module."""

import os
import sys

import pytest

# Skip wxPython tests on headless Linux (no display)
skip_no_display = pytest.mark.skipif(
    sys.platform == "linux" and not os.environ.get("DISPLAY"),
    reason="wxPython requires DISPLAY on Linux",
)


@skip_no_display
def test_import_app():
    """Test that the app module can be imported."""
    from accessisky import app

    assert hasattr(app, "main")
    assert hasattr(app, "AccessiSkyApp")


def test_import_iss_client():
    """Test that ISS client can be imported."""
    from accessisky.api.iss import ISSClient, ISSPass, ISSPosition

    assert ISSClient is not None
    assert ISSPosition is not None
    assert ISSPass is not None
