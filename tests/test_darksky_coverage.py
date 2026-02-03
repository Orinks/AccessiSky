"""Comprehensive tests for Dark Sky module to improve coverage.

Covers:
- TwilightType.sun_angle_range property
- DarkSkyWindow.time_until_darkness() - all paths
- DarkSkyWindow.time_remaining() - all paths
- DarkSkyWindow.__str__() edge cases
- get_twilight_type() function
- DarkSkyClient async wrapper methods
- Non-polar latitude with missing twilight data
- Naive datetime handling (no tzinfo)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from accessisky.api.darksky import (
    DarkSkyClient,
    DarkSkyWindow,
    TwilightType,
    get_dark_sky_window,
    get_twilight_type,
    is_astronomical_darkness,
)

# ---------------------------------------------------------------------------
# TwilightType.sun_angle_range
# ---------------------------------------------------------------------------


class TestTwilightTypeSunAngleRange:
    """Tests for the sun_angle_range property."""

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


# ---------------------------------------------------------------------------
# get_twilight_type()
# ---------------------------------------------------------------------------


class TestGetTwilightType:
    """Tests for get_twilight_type function."""

    def test_day(self):
        assert get_twilight_type(10.0) == TwilightType.DAY

    def test_day_at_horizon(self):
        assert get_twilight_type(0.0) == TwilightType.DAY

    def test_civil_just_below(self):
        assert get_twilight_type(-0.1) == TwilightType.CIVIL

    def test_civil_boundary(self):
        assert get_twilight_type(-6.0) == TwilightType.CIVIL

    def test_nautical_just_below(self):
        assert get_twilight_type(-6.1) == TwilightType.NAUTICAL

    def test_nautical_boundary(self):
        assert get_twilight_type(-12.0) == TwilightType.NAUTICAL

    def test_astronomical_just_below(self):
        assert get_twilight_type(-12.1) == TwilightType.ASTRONOMICAL

    def test_astronomical_boundary(self):
        assert get_twilight_type(-18.0) == TwilightType.ASTRONOMICAL

    def test_night(self):
        assert get_twilight_type(-18.1) == TwilightType.NIGHT

    def test_deep_night(self):
        assert get_twilight_type(-45.0) == TwilightType.NIGHT


# ---------------------------------------------------------------------------
# DarkSkyWindow.time_until_darkness()
# ---------------------------------------------------------------------------


class TestTimeUntilDarkness:
    """Tests for DarkSkyWindow.time_until_darkness method."""

    def _make_window(self):
        return DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=datetime(2026, 3, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

    def test_returns_none_when_no_darkness(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 21),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
            no_darkness_reason="Polar day",
        )
        result = window.time_until_darkness(
            datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
        )
        assert result is None

    def test_before_darkness(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc)
        result = window.time_until_darkness(from_time)
        assert result == timedelta(hours=2)

    def test_after_darkness_begins_returns_zero(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 16, 1, 0, tzinfo=timezone.utc)
        result = window.time_until_darkness(from_time)
        assert result == timedelta(0)

    def test_exactly_at_darkness_begins(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 15, 22, 0, tzinfo=timezone.utc)
        result = window.time_until_darkness(from_time)
        assert result == timedelta(0)

    def test_naive_datetime_treated_as_utc(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 15, 20, 0)  # naive
        result = window.time_until_darkness(from_time)
        assert result == timedelta(hours=2)


# ---------------------------------------------------------------------------
# DarkSkyWindow.time_remaining()
# ---------------------------------------------------------------------------


class TestTimeRemaining:
    """Tests for DarkSkyWindow.time_remaining method."""

    def _make_window(self):
        return DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=datetime(2026, 3, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )

    def test_returns_none_when_no_darkness_ends(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 21),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        result = window.time_remaining(
            datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
        )
        assert result is None

    def test_after_darkness_ends_returns_zero(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 16, 5, 0, tzinfo=timezone.utc)
        result = window.time_remaining(from_time)
        assert result == timedelta(0)

    def test_exactly_at_darkness_ends(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc)
        result = window.time_remaining(from_time)
        assert result == timedelta(0)

    def test_before_darkness_begins_returns_full_duration(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc)
        result = window.time_remaining(from_time)
        assert result == timedelta(hours=6)

    def test_during_darkness(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 16, 1, 0, tzinfo=timezone.utc)
        result = window.time_remaining(from_time)
        assert result == timedelta(hours=3)

    def test_naive_datetime_treated_as_utc(self):
        window = self._make_window()
        from_time = datetime(2026, 3, 16, 1, 0)  # naive
        result = window.time_remaining(from_time)
        assert result == timedelta(hours=3)

    def test_no_darkness_begins_but_has_ends(self):
        """When darkness_begins is None but darkness_ends exists."""
        window = DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=None,
            darkness_ends=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=0,
        )
        from_time = datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc)
        result = window.time_remaining(from_time)
        # darkness_begins is None so the branch falls through
        assert result == timedelta(hours=8)


# ---------------------------------------------------------------------------
# DarkSkyWindow.__str__() edge cases
# ---------------------------------------------------------------------------


class TestDarkSkyWindowStr:
    """Tests for __str__ edge cases."""

    def test_str_with_no_darkness_reason(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 21),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
            no_darkness_reason="Polar twilight - no true darkness during summer",
        )
        result = str(window)
        assert result == "Dark Sky: Polar twilight - no true darkness during summer"

    def test_str_with_no_data(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 21),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        result = str(window)
        assert result == "Dark Sky: No data available"

    def test_str_normal_window(self):
        window = DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=datetime(2026, 3, 15, 22, 30, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 3, 0, tzinfo=timezone.utc),
            darkness_duration_hours=4.5,
        )
        result = str(window)
        assert "22:30 UTC" in result
        assert "03:00 UTC" in result
        assert "4h 30m" in result

    def test_str_fractional_minutes(self):
        window = DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=datetime(2026, 3, 15, 21, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 4, 15, tzinfo=timezone.utc),
            darkness_duration_hours=7.25,
        )
        result = str(window)
        assert "7h 15m" in result


# ---------------------------------------------------------------------------
# DarkSkyWindow.is_currently_dark - extra edge cases
# ---------------------------------------------------------------------------


class TestIsCurrentlyDarkEdgeCases:
    """Additional edge-case tests for is_currently_dark."""

    def test_returns_false_when_no_darkness(self):
        window = DarkSkyWindow(
            date=date(2026, 6, 21),
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
        )
        assert not window.is_currently_dark(
            datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
        )

    def test_naive_datetime(self):
        window = DarkSkyWindow(
            date=date(2026, 3, 15),
            darkness_begins=datetime(2026, 3, 15, 22, 0, tzinfo=timezone.utc),
            darkness_ends=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
            darkness_duration_hours=6.0,
        )
        # naive datetime should be treated as UTC
        assert window.is_currently_dark(datetime(2026, 3, 16, 1, 0))


# ---------------------------------------------------------------------------
# is_astronomical_darkness - naive datetime
# ---------------------------------------------------------------------------


class TestIsAstronomicalDarknessNaive:
    """Test is_astronomical_darkness with naive datetime."""

    def test_naive_check_time(self):
        result = is_astronomical_darkness(
            check_time=datetime(2026, 3, 16, 1, 0),  # naive
            twilight_end=datetime(2026, 3, 15, 20, 0, tzinfo=timezone.utc),
            twilight_begin=datetime(2026, 3, 16, 4, 0, tzinfo=timezone.utc),
        )
        assert result is True


# ---------------------------------------------------------------------------
# get_dark_sky_window - non-polar missing twilight & edge cases
# ---------------------------------------------------------------------------


class TestGetDarkSkyWindowEdgeCases:
    """Edge cases for get_dark_sky_window."""

    def test_non_polar_missing_twilight(self):
        """Non-polar latitude with missing twilight data."""
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.no_darkness_reason == "Twilight data not available"
        assert window.darkness_duration_hours == 0

    def test_polar_winter_missing_twilight(self):
        """Polar latitude in winter."""
        window = get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 12, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.no_darkness_reason == "Unable to determine twilight times"

    def test_polar_summer_missing_twilight(self):
        """Polar latitude in summer."""
        window = get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 6, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.no_darkness_reason == (
            "Polar twilight - no true darkness during summer"
        )

    def test_best_viewing_time_is_midpoint(self):
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(
                2026, 3, 15, 20, 0, tzinfo=timezone.utc
            ),
            astronomical_twilight_begin=datetime(
                2026, 3, 16, 4, 0, tzinfo=timezone.utc
            ),
        )
        expected_midpoint = datetime(2026, 3, 16, 0, 0, tzinfo=timezone.utc)
        assert window.best_viewing_time == expected_midpoint

    def test_moon_times_passed_through(self):
        moon_rise = datetime(2026, 3, 15, 23, 0, tzinfo=timezone.utc)
        moon_set = datetime(2026, 3, 16, 5, 0, tzinfo=timezone.utc)
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(
                2026, 3, 15, 20, 0, tzinfo=timezone.utc
            ),
            astronomical_twilight_begin=datetime(
                2026, 3, 16, 4, 0, tzinfo=timezone.utc
            ),
            moon_rise=moon_rise,
            moon_set=moon_set,
        )
        assert window.moon_rise == moon_rise
        assert window.moon_set == moon_set

    def test_only_end_missing(self):
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=datetime(
                2026, 3, 16, 4, 0, tzinfo=timezone.utc
            ),
        )
        assert window.darkness_duration_hours == 0
        assert window.no_darkness_reason is not None

    def test_only_begin_missing(self):
        window = get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(
                2026, 3, 15, 20, 0, tzinfo=timezone.utc
            ),
            astronomical_twilight_begin=None,
        )
        assert window.darkness_duration_hours == 0
        assert window.no_darkness_reason is not None

    def test_southern_polar_summer(self):
        """Southern hemisphere polar latitude in Dec (summer there)."""
        window = get_dark_sky_window(
            latitude=-70.0,
            longitude=0,
            target_date=date(2026, 12, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        # abs(-70) > 66.5, December is not in [5,6,7]
        assert window.no_darkness_reason == "Unable to determine twilight times"


# ---------------------------------------------------------------------------
# DarkSkyClient async methods
# ---------------------------------------------------------------------------


class TestDarkSkyClient:
    """Tests for DarkSkyClient async wrapper."""

    @pytest.mark.asyncio
    async def test_get_dark_sky_window(self):
        client = DarkSkyClient()
        window = await client.get_dark_sky_window(
            latitude=45.0,
            longitude=-75.0,
            target_date=date(2026, 3, 15),
            astronomical_twilight_end=datetime(
                2026, 3, 15, 20, 0, tzinfo=timezone.utc
            ),
            astronomical_twilight_begin=datetime(
                2026, 3, 16, 4, 0, tzinfo=timezone.utc
            ),
        )
        assert isinstance(window, DarkSkyWindow)
        assert window.darkness_duration_hours == 8.0

    @pytest.mark.asyncio
    async def test_get_dark_sky_window_no_twilight(self):
        client = DarkSkyClient()
        window = await client.get_dark_sky_window(
            latitude=70.0,
            longitude=0,
            target_date=date(2026, 6, 21),
            astronomical_twilight_end=None,
            astronomical_twilight_begin=None,
        )
        assert window.darkness_duration_hours == 0
        assert window.no_darkness_reason is not None

    @pytest.mark.asyncio
    async def test_is_astronomical_darkness_true(self):
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
    async def test_close(self):
        client = DarkSkyClient()
        await client.close()  # Should not raise
