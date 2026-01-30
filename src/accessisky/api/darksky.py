"""Dark Sky Times calculations for astrophotography.

Calculates when true astronomical darkness begins and ends,
which is essential for deep sky astrophotography.

Astronomical twilight ends when the Sun is 18° below the horizon.
Before this, the sky still has some residual glow that can
affect sensitive observations and long-exposure photography.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum


class TwilightType(Enum):
    """Types of twilight/darkness."""

    DAY = "Daytime"
    CIVIL = "Civil Twilight"
    NAUTICAL = "Nautical Twilight"
    ASTRONOMICAL = "Astronomical Twilight"
    NIGHT = "Astronomical Night"

    @property
    def description(self) -> str:
        """Get description of this twilight type."""
        descriptions = {
            TwilightType.DAY: "Sun above horizon - full daylight",
            TwilightType.CIVIL: "Sun 0-6° below horizon - outdoor activities possible without artificial light",
            TwilightType.NAUTICAL: "Sun 6-12° below horizon - horizon still visible, bright stars appear",
            TwilightType.ASTRONOMICAL: "Sun 12-18° below horizon - sky still faintly lit, faint stars visible",
            TwilightType.NIGHT: "Sun 18°+ below horizon - true darkness, no twilight glow",
        }
        return descriptions[self]

    @property
    def sun_angle_range(self) -> tuple[float, float]:
        """Get sun angle range below horizon (degrees)."""
        ranges = {
            TwilightType.DAY: (0, 0),
            TwilightType.CIVIL: (0, 6),
            TwilightType.NAUTICAL: (6, 12),
            TwilightType.ASTRONOMICAL: (12, 18),
            TwilightType.NIGHT: (18, 90),
        }
        return ranges[self]


@dataclass
class DarkSkyWindow:
    """Information about the dark sky window for a night."""

    date: date  # The evening date (darkness may extend into next day)
    darkness_begins: datetime | None  # When astronomical twilight ends
    darkness_ends: datetime | None  # When astronomical twilight begins (morning)
    darkness_duration_hours: float

    # Additional info
    no_darkness_reason: str | None = None  # E.g., "Polar day - no true darkness"
    best_viewing_time: datetime | None = None  # Midpoint of darkness
    moon_rise: datetime | None = None
    moon_set: datetime | None = None

    def is_currently_dark(self, check_time: datetime) -> bool:
        """Check if it's currently astronomical darkness."""
        if self.darkness_begins is None or self.darkness_ends is None:
            return False

        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=timezone.utc)

        return self.darkness_begins <= check_time <= self.darkness_ends

    def time_until_darkness(self, from_time: datetime) -> timedelta | None:
        """Get time until darkness begins."""
        if self.darkness_begins is None:
            return None

        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=timezone.utc)

        if from_time >= self.darkness_begins:
            return timedelta(0)

        return self.darkness_begins - from_time

    def time_remaining(self, from_time: datetime) -> timedelta | None:
        """Get time remaining in darkness window."""
        if self.darkness_ends is None:
            return None

        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=timezone.utc)

        if from_time >= self.darkness_ends:
            return timedelta(0)

        if self.darkness_begins and from_time < self.darkness_begins:
            return self.darkness_ends - self.darkness_begins

        return self.darkness_ends - from_time

    def __str__(self) -> str:
        if self.no_darkness_reason:
            return f"Dark Sky: {self.no_darkness_reason}"

        if self.darkness_begins is None or self.darkness_ends is None:
            return "Dark Sky: No data available"

        begin_str = self.darkness_begins.strftime("%H:%M UTC")
        end_str = self.darkness_ends.strftime("%H:%M UTC")
        hours = int(self.darkness_duration_hours)
        mins = int((self.darkness_duration_hours - hours) * 60)

        return f"Dark Sky: {begin_str} to {end_str} ({hours}h {mins}m of true darkness)"


def get_darkness_duration(
    darkness_begins: datetime,
    darkness_ends: datetime,
) -> float:
    """
    Calculate duration of darkness in hours.

    Args:
        darkness_begins: When astronomical twilight ends
        darkness_ends: When astronomical twilight begins (morning)

    Returns:
        Duration in hours
    """
    delta = darkness_ends - darkness_begins
    return delta.total_seconds() / 3600.0


def is_astronomical_darkness(
    check_time: datetime,
    twilight_end: datetime | None,
    twilight_begin: datetime | None,
) -> bool:
    """
    Check if a given time is during astronomical darkness.

    Args:
        check_time: Time to check
        twilight_end: When astronomical twilight ends (evening)
        twilight_begin: When astronomical twilight begins (morning)

    Returns:
        True if currently in astronomical darkness
    """
    if twilight_end is None or twilight_begin is None:
        return False

    if check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=timezone.utc)

    return twilight_end <= check_time <= twilight_begin


def get_dark_sky_window(
    latitude: float,
    longitude: float,
    target_date: date,
    astronomical_twilight_end: datetime | None,
    astronomical_twilight_begin: datetime | None,
    moon_rise: datetime | None = None,
    moon_set: datetime | None = None,
) -> DarkSkyWindow:
    """
    Get the dark sky window for astrophotography.

    This calculates the window of true astronomical darkness,
    when the Sun is more than 18° below the horizon.

    Args:
        latitude: Observer latitude
        longitude: Observer longitude
        target_date: Date for the evening
        astronomical_twilight_end: When twilight ends (from sun API)
        astronomical_twilight_begin: When twilight begins next morning
        moon_rise: Optional moon rise time
        moon_set: Optional moon set time

    Returns:
        DarkSkyWindow with darkness timing information
    """
    # Handle polar day/night cases
    if astronomical_twilight_end is None or astronomical_twilight_begin is None:
        # Check if polar region
        if abs(latitude) > 66.5:
            if target_date.month in [5, 6, 7]:  # Summer months
                reason = "Polar twilight - no true darkness during summer"
            else:
                reason = "Unable to determine twilight times"
        else:
            reason = "Twilight data not available"

        return DarkSkyWindow(
            date=target_date,
            darkness_begins=None,
            darkness_ends=None,
            darkness_duration_hours=0,
            no_darkness_reason=reason,
        )

    # Calculate duration
    duration = get_darkness_duration(astronomical_twilight_end, astronomical_twilight_begin)

    # Calculate best viewing time (midpoint)
    total_seconds = (astronomical_twilight_begin - astronomical_twilight_end).total_seconds()
    best_time = astronomical_twilight_end + timedelta(seconds=total_seconds / 2)

    return DarkSkyWindow(
        date=target_date,
        darkness_begins=astronomical_twilight_end,
        darkness_ends=astronomical_twilight_begin,
        darkness_duration_hours=duration,
        best_viewing_time=best_time,
        moon_rise=moon_rise,
        moon_set=moon_set,
    )


def get_twilight_type(sun_altitude: float) -> TwilightType:
    """
    Determine twilight type based on Sun's altitude.

    Args:
        sun_altitude: Sun's altitude in degrees (negative = below horizon)

    Returns:
        TwilightType for current conditions
    """
    if sun_altitude >= 0:
        return TwilightType.DAY
    elif sun_altitude >= -6:
        return TwilightType.CIVIL
    elif sun_altitude >= -12:
        return TwilightType.NAUTICAL
    elif sun_altitude >= -18:
        return TwilightType.ASTRONOMICAL
    else:
        return TwilightType.NIGHT


class DarkSkyClient:
    """Client interface for dark sky data (for consistency with other API clients)."""

    async def get_dark_sky_window(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
        astronomical_twilight_end: datetime | None,
        astronomical_twilight_begin: datetime | None,
    ) -> DarkSkyWindow:
        """Get dark sky window for astrophotography."""
        return get_dark_sky_window(
            latitude=latitude,
            longitude=longitude,
            target_date=target_date,
            astronomical_twilight_end=astronomical_twilight_end,
            astronomical_twilight_begin=astronomical_twilight_begin,
        )

    async def is_astronomical_darkness(
        self,
        check_time: datetime,
        twilight_end: datetime | None,
        twilight_begin: datetime | None,
    ) -> bool:
        """Check if currently in astronomical darkness."""
        return is_astronomical_darkness(check_time, twilight_end, twilight_begin)

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
