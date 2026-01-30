"""Tests for Dark Sky Times calculations."""

from datetime import date, datetime, time, timezone

import pytest

from accessisky.api.darksky import (
    DarkSkyWindow,
    TwilightType,
    get_dark_sky_window,
    get_darkness_duration,
    is_astronomical_darkness,
)


class TestTwilightType:
    """Tests for twilight type enum."""

    def test_twilight_types_exist(self):
        """Test that all twilight types exist."""
        assert TwilightType.DAY
        assert TwilightType.CIVIL
        assert TwilightType.NAUTICAL
        assert TwilightType.ASTRONOMICAL
        assert TwilightType.NIGHT

    def test_twilight_descriptions(self):
        """Test that twilight types have descriptions."""
        for twilight in TwilightType:
            assert twilight.description


class TestDarkSkyWindow:
    """Tests for DarkSkyWindow dataclass."""

    def test_window_creation(self):
        """Test creating a dark sky window."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 30, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 3, 30, tzinfo=timezone.utc),
            darkness_duration_hours=5.0,
        )
        
        assert window.date == date(2026, 6, 15)
        assert window.darkness_duration_hours == 5.0

    def test_str_representation(self):
        """Test string representation."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 30, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 3, 30, tzinfo=timezone.utc),
            darkness_duration_hours=5.0,
        )
        
        s = str(window)
        assert "22:30" in s or "10:30" in s  # Depends on formatting
        assert "5" in s  # Hours

    def test_is_currently_dark(self):
        """Test is_currently_dark method."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )
        
        # During darkness
        during = datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc)
        assert window.is_currently_dark(during)
        
        # Before darkness
        before = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
        assert not window.is_currently_dark(before)
        
        # After darkness
        after = datetime(2026, 6, 16, 5, 0, tzinfo=timezone.utc)
        assert not window.is_currently_dark(after)


class TestGetDarkSkyWindow:
    """Tests for get_dark_sky_window function."""

    def test_returns_window(self):
        """Test that function returns a DarkSkyWindow."""
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),  # Spring equinox time
            astronomical_twilight_end=datetime(2026, 3, 15, 20, 30, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 3, 16, 5, 30, tzinfo=timezone.utc),
        )
        
        assert isinstance(window, DarkSkyWindow)
        assert window.darkness_duration_hours > 0

    def test_summer_short_nights(self):
        """Test that summer has shorter dark periods (at high latitudes)."""
        # Summer night at high latitude
        summer = get_dark_sky_window(
            latitude=60.0,  # High latitude
            longitude=0,
            target_date=date(2026, 6, 21),  # Summer solstice
            astronomical_twilight_end=datetime(2026, 6, 22, 0, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 6, 22, 2, 0, tzinfo=timezone.utc),
        )
        
        # Winter night
        winter = get_dark_sky_window(
            latitude=60.0,
            longitude=0,
            target_date=date(2026, 12, 21),
            astronomical_twilight_end=datetime(2026, 12, 21, 16, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 12, 22, 8, 0, tzinfo=timezone.utc),
        )
        
        # Winter should have longer dark period
        assert winter.darkness_duration_hours > summer.darkness_duration_hours

    def test_no_darkness_polar_summer(self):
        """Test handling of no true darkness (polar summer)."""
        # In polar summer, there may be no astronomical darkness
        window = get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 6, 21),
            astronomical_twilight_end=None,  # No true darkness
            astronomical_twilight_begin=None,
        )
        
        assert window.darkness_duration_hours == 0
        assert window.no_darkness_reason is not None


class TestGetDarknessDuration:
    """Tests for get_darkness_duration function."""

    def test_calculates_duration(self):
        """Test darkness duration calculation."""
        duration = get_darkness_duration(
            darkness_begins=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        
        assert duration == 8.0  # 8 hours

    def test_handles_midnight_crossing(self):
        """Test that midnight crossing is handled correctly."""
        duration = get_darkness_duration(
            darkness_begins=datetime(2026, 3, 15, 23, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 3, 0, tzinfo=timezone.utc),
        )
        
        assert duration == 4.0


class TestIsAstronomicalDarkness:
    """Tests for is_astronomical_darkness function."""

    def test_during_darkness(self):
        """Test that times during darkness return True."""
        is_dark = is_astronomical_darkness(
            check_time=datetime(2026, 3, 16, 1, 0, tzinfo=timezone.utc),
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        
        assert is_dark is True

    def test_during_twilight(self):
        """Test that times during twilight return False."""
        is_dark = is_astronomical_darkness(
            check_time=datetime(2026, 3, 15, 19, 0, tzinfo=timezone.utc),
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        
        assert is_dark is False

    def test_no_twilight_data(self):
        """Test handling when twilight times are None."""
        is_dark = is_astronomical_darkness(
            check_time=datetime(2026, 6, 21, 1, 0, tzinfo=timezone.utc),
            twilight_end=None,
            twilight_begin=None,
        )
        
        assert is_dark is False  # Assume not dark if no data
