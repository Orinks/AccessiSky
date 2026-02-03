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

    def test_naive_check_time_gets_utc(self):
        """Test that naive datetime gets UTC timezone added."""
        is_dark = is_astronomical_darkness(
            check_time=datetime(2026, 3, 16, 1, 0),  # naive
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        assert is_dark is True


class TestTwilightTypeSunAngleRange:
    """Tests for TwilightType.sun_angle_range property."""

    def test_day_range(self):
        assert TwilightType.DAY.sun_angle_range == (0, 0)

    def test_civil_range(self):
        assert TwilightType.CIVIL.sun_angle_range == (0, 6)

    def test_nautical_range(self):
        assert TwilightType.NAUTICAL.sun_angle_range == (6, 12)

    def test_astronomical_range(self):
        assert TwilightType.ASTRONOMICAL.sun_angle_range == (12, 18)

    def test_night_range(self):
        assert TwilightType.NIGHT.sun_angle_range == (18, 90)

    def test_all_types_have_ranges(self):
        """Every twilight type should return a tuple of two floats."""
        for t in TwilightType:
            r = t.sun_angle_range
            assert isinstance(r, tuple)
            assert len(r) == 2


class TestDarkSkyWindowTimeUntilDarkness:
    """Tests for DarkSkyWindow.time_until_darkness method."""

    def _make_window(self):
        return DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

    def test_returns_none_when_no_darkness(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        assert window.time_until_darkness(datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)) is None

    def test_before_darkness(self):
        window = self._make_window()
        result = window.time_until_darkness(datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc))
        assert result == timedelta(hours=2)

    def test_after_darkness_begins(self):
        window = self._make_window()
        result = window.time_until_darkness(datetime(2026, 6, 15, 23, 0, tzinfo=timezone.utc))
        assert result == timedelta(0)

    def test_naive_datetime_gets_utc(self):
        window = self._make_window()
        result = window.time_until_darkness(datetime(2026, 6, 15, 20, 0))  # naive
        assert result == timedelta(hours=2)


class TestDarkSkyWindowTimeRemaining:
    """Tests for DarkSkyWindow.time_remaining method."""

    def _make_window(self):
        return DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

    def test_returns_none_when_no_darkness_end(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        assert window.time_remaining(datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc)) is None

    def test_after_darkness_ends(self):
        window = self._make_window()
        result = window.time_remaining(datetime(2026, 6, 16, 5, 0, tzinfo=timezone.utc))
        assert result == timedelta(0)

    def test_during_darkness(self):
        window = self._make_window()
        result = window.time_remaining(datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc))
        assert result == timedelta(hours=3)

    def test_before_darkness_returns_full_duration(self):
        window = self._make_window()
        result = window.time_remaining(datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc))
        assert result == timedelta(hours=6)

    def test_naive_datetime_gets_utc(self):
        window = self._make_window()
        result = window.time_remaining(datetime(2026, 6, 16, 1, 0))  # naive
        assert result == timedelta(hours=3)


class TestDarkSkyWindowStr:
    """Tests for DarkSkyWindow.__str__ edge cases."""

    def test_str_with_no_darkness_reason(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
            no_darkness_reason="Polar twilight - no true darkness during summer",
        )
        assert str(window) == "Dark Sky: Polar twilight - no true darkness during summer"

    def test_str_with_no_data(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        assert str(window) == "Dark Sky: No data available"

    def test_str_with_partial_hours(self):
        """Test formatting with fractional hours (e.g., 5h 30m)."""
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 3, 30, tzinfo=timezone.utc),
            darkness_duration_hours=5.5,
        )
        s = str(window)
        assert "22:00 UTC" in s
        assert "03:30 UTC" in s
        assert "5h 30m" in s


class TestDarkSkyWindowIsCurrentlyDark:
    """Additional tests for is_currently_dark."""

    def test_no_darkness_data(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        assert not window.is_currently_dark(datetime(2026, 6, 16, 1, 0, tzinfo=timezone.utc))

    def test_naive_datetime_gets_utc(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 15),
            darkness_begins=datetime(2026, 6, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 6, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )
        assert window.is_currently_dark(datetime(2026, 6, 16, 1, 0))  # naive


class TestGetTwilightType:
    """Tests for get_twilight_type function."""

    def test_daytime(self):
        assert get_twilight_type(10.0) == TwilightType.DAY

    def test_horizon(self):
        assert get_twilight_type(0.0) == TwilightType.DAY

    def test_civil_twilight(self):
        assert get_twilight_type(-3.0) == TwilightType.CIVIL

    def test_civil_boundary(self):
        assert get_twilight_type(-6.0) == TwilightType.CIVIL

    def test_nautical_twilight(self):
        assert get_twilight_type(-9.0) == TwilightType.NAUTICAL

    def test_nautical_boundary(self):
        assert get_twilight_type(-12.0) == TwilightType.NAUTICAL

    def test_astronomical_twilight(self):
        assert get_twilight_type(-15.0) == TwilightType.ASTRONOMICAL

    def test_astronomical_boundary(self):
        assert get_twilight_type(-18.0) == TwilightType.ASTRONOMICAL

    def test_night(self):
        assert get_twilight_type(-25.0) == TwilightType.NIGHT

    def test_deep_night(self):
        assert get_twilight_type(-90.0) == TwilightType.NIGHT


class TestGetDarkSkyWindowEdgeCases:
    """Additional tests for get_dark_sky_window edge cases."""

    def test_non_polar_missing_twilight(self):
        """Non-polar latitude with missing twilight data."""
        window = get_dark_sky_window(
            latitude=40.0,
            longitude=-74.0,
            target_date=date(2026, 6, 15),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.no_darkness_reason == "Twilight data not available"
        assert window.darkness_duration_hours == 0

    def test_polar_winter_missing_twilight(self):
        """Polar latitude in winter with missing twilight data."""
        window = get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 12, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.no_darkness_reason == "Unable to determine twilight times"

    def test_polar_summer_missing_twilight(self):
        """Polar latitude in summer with missing twilight data."""
        window = get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 6, 15),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert "summer" in window.no_darkness_reason.lower()

    def test_best_viewing_time_calculated(self):
        """best_viewing_time should be the midpoint of darkness."""
        begin = datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc)
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=begin,
            astronomical_twilight_begin=end,
        )
        expected_midpoint = datetime(2026, 3, 16, 0, 0, tzinfo=timezone.utc)
        assert window.best_viewing_time == expected_midpoint

    def test_moon_times_passed_through(self):
        """Moon rise/set should be stored on the window."""
        moon_rise = datetime(2026, 3, 15, 19, 0, tzinfo=timezone.utc)
        moon_set = datetime(2026, 3, 16, 6, 0, tzinfo=timezone.utc)
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
            moon_rise=moon_rise,
            moon_set=moon_set,
        )
        assert window.moon_rise == moon_rise
        assert window.moon_set == moon_set

    def test_south_polar_summer(self):
        """Southern hemisphere polar summer (Dec-Jan)."""
        window = get_dark_sky_window(
            latitude=-70.0,
            longitude=0,
            target_date=date(2026, 12, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        # December is summer in southern hemisphere, but month check is 5,6,7
        # so this should fall to "Unable to determine twilight times"
        assert window.no_darkness_reason == "Unable to determine twilight times"


class TestDarkSkyClient:
    """Tests for DarkSkyClient async wrapper."""

    @pytest.mark.asyncio
    async def test_get_dark_sky_window(self):
        client = DarkSkyClient()
        window = await client.get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            astronomical_twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        assert isinstance(window, DarkSkyWindow)
        assert window.darkness_duration_hours == 8.0

    @pytest.mark.asyncio
    async def test_is_astronomical_darkness(self):
        client = DarkSkyClient()
        result = await client.is_astronomical_darkness(
            check_time=datetime(2026, 3, 16, 1, 0, tzinfo=timezone.utc),
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_is_astronomical_darkness_false(self):
        client = DarkSkyClient()
        result = await client.is_astronomical_darkness(
            check_time=datetime(2026, 3, 15, 19, 0, tzinfo=timezone.utc),
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_close_noop(self):
        client = DarkSkyClient()
        await client.close()  # Should not raise
