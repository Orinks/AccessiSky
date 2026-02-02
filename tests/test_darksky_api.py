"""Tests for Dark Sky Times calculations."""

from datetime import date, datetime, timedelta, timezone

import pytest

from accessisky.api.darksky import (
    DarkSkyClient,
    DarkSkyWindow,
    TwilightType,
    get_dark_sky_window,
    get_darkness_duration,
    get_twilight_type,
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

    def test_sun_angle_ranges(self):
        """Test sun angle ranges for each twilight type."""
        assert TwilightType.DAY.sun_angle_range == (0, 0)
        assert TwilightType.CIVIL.sun_angle_range == (0, 6)
        assert TwilightType.NAUTICAL.sun_angle_range == (6, 12)
        assert TwilightType.ASTRONOMICAL.sun_angle_range == (12, 18)
        assert TwilightType.NIGHT.sun_angle_range == (18, 90)


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

    def test_str_no_data(self):
        """Test string representation with no data."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0.0,
        )

        assert str(window) == "Dark Sky: No data available"

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

    def test_time_until_darkness(self):
        """Test time_until_darkness method for all paths."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

        before = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
        assert window.time_until_darkness(before) == timedelta(hours=2)

        during = datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc)
        assert window.time_until_darkness(during) == timedelta(0)

        no_data = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0.0,
        )
        assert no_data.time_until_darkness(before) is None

    def test_time_remaining(self):
        """Test time_remaining method for all paths."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

        before = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
        assert window.time_remaining(before) == timedelta(hours=6)

        during = datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc)
        assert window.time_remaining(during) == timedelta(hours=3)

        after = datetime(2026, 6, 16, 5, 0, tzinfo=timezone.utc)
        assert window.time_remaining(after) == timedelta(0)

        no_data = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=None,
            darkness_duration_hours=0.0,
        )
        assert no_data.time_remaining(during) is None


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

    def test_no_twilight_non_polar(self):
        """Test missing twilight data at non-polar latitude."""
        window = get_dark_sky_window(
            latitude=40.0,
            longitude=0,
            target_date=date(2026, 6, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )

        assert window.darkness_duration_hours == 0
        assert window.no_darkness_reason == "Twilight data not available"


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


class TestGetTwilightType:
    """Tests for get_twilight_type function."""

    def test_all_twilight_types(self):
        """Test all twilight type return values."""
        assert get_twilight_type(1.0) == TwilightType.DAY
        assert get_twilight_type(0.0) == TwilightType.DAY
        assert get_twilight_type(-3.0) == TwilightType.CIVIL
        assert get_twilight_type(-9.0) == TwilightType.NAUTICAL
        assert get_twilight_type(-15.0) == TwilightType.ASTRONOMICAL
        assert get_twilight_type(-25.0) == TwilightType.NIGHT


class TestDarkSkyClient:
    """Tests for DarkSkyClient async wrapper methods."""

    @pytest.mark.asyncio
    async def test_get_dark_sky_window(self):
        """Test async wrapper for get_dark_sky_window."""
        client = DarkSkyClient()
        window = await client.get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(2026, 3, 15, 20, 30, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 3, 16, 5, 30, tzinfo=timezone.utc),
        )

        assert isinstance(window, DarkSkyWindow)
        assert window.darkness_duration_hours > 0

    @pytest.mark.asyncio
    async def test_is_astronomical_darkness(self):
        """Test async wrapper for is_astronomical_darkness."""
        client = DarkSkyClient()
        is_dark = await client.is_astronomical_darkness(
            check_time=datetime(2026, 3, 16, 1, 0, tzinfo=timezone.utc),
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )

        assert is_dark is True

    @pytest.mark.asyncio
    async def test_close(self):
        """Test async close no-op."""
        client = DarkSkyClient()
        assert await client.close() is None
