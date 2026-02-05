"""Tests for AccessiSky app module."""

import pytest


def test_import_app():
    """Test that the app module can be imported."""
    pytest.importorskip("wx", reason="wxPython not installed")
    from accessisky import app

    assert hasattr(app, "main")
    assert hasattr(app, "AccessiSkyApp")


def test_import_iss_client():
    """Test that ISS client can be imported."""
    from accessisky.api.iss import ISSClient, ISSPass, ISSPosition

    assert ISSClient is not None
    assert ISSPosition is not None
    assert ISSPass is not None
