"""Moon phase API using USNO (US Naval Observatory) with local calculation fallback."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class MoonPhase(Enum):
    """Moon phase names."""

    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"


@dataclass
class MoonInfo:
    """Moon information for a specific date."""

    date: date
    phase: MoonPhase
    illumination: float  # 0.0 to 1.0
    age_days: float  # Days since new moon (0-29.53)
    source: str = "local"  # "usno" or "local"

    @property
    def illumination_percent(self) -> int:
        """Get illumination as percentage."""
        return round(self.illumination * 100)

    @property
    def phase_emoji(self) -> str:
        """Get emoji for current phase."""
        emojis = {
            MoonPhase.NEW_MOON: "🌑",
            MoonPhase.WAXING_CRESCENT: "🌒",
            MoonPhase.FIRST_QUARTER: "🌓",
            MoonPhase.WAXING_GIBBOUS: "🌔",
            MoonPhase.FULL_MOON: "🌕",
            MoonPhase.WANING_GIBBOUS: "🌖",
            MoonPhase.LAST_QUARTER: "🌗",
            MoonPhase.WANING_CRESCENT: "🌘",
        }
        return emojis.get(self.phase, "🌙")

    def __str__(self) -> str:
        return f"{self.phase_emoji} {self.phase.value} ({self.illumination_percent}% illuminated)"


@dataclass
class MoonEvent:
    """A significant moon event (full moon, new moon, etc.)."""

    datetime: datetime
    phase: MoonPhase
    source: str = "local"

    def __str__(self) -> str:
        return f"{self.phase.value}: {self.datetime.strftime('%Y-%m-%d %H:%M UTC')}"


# Synodic month (new moon to new moon) in days
SYNODIC_MONTH = 29.53058867

# Reference new moon (known new moon date for calculations)
# January 6, 2000 at 18:14 UTC was a new moon
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

# USNO API endpoint
USNO_MOON_PHASES_API = "https://aa.usno.navy.mil/api/moon/phases"


def _days_since_reference(dt: datetime) -> float:
    """Get days since reference new moon."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = dt - REFERENCE_NEW_MOON
    return delta.total_seconds() / 86400


def get_moon_age(dt: datetime) -> float:
    """
    Get moon age in days (0 = new moon, ~14.76 = full moon).

    Args:
        dt: DateTime to check

    Returns:
        Age in days (0 to 29.53)
    """
    days = _days_since_reference(dt)
    return days % SYNODIC_MONTH


def get_moon_illumination(dt: datetime) -> float:
    """
    Get approximate moon illumination (0.0 to 1.0).

    This uses a simple cosine approximation.

    Args:
        dt: DateTime to check

    Returns:
        Illumination fraction (0.0 to 1.0)
    """
    age = get_moon_age(dt)
    # Convert age to angle (0 at new moon, π at full moon)
    angle = (age / SYNODIC_MONTH) * 2 * math.pi
    # Illumination follows a (1 - cos) / 2 curve
    return (1 - math.cos(angle)) / 2


def get_moon_phase(dt: datetime) -> MoonPhase:
    """
    Get the moon phase for a given datetime.

    Args:
        dt: DateTime to check

    Returns:
        MoonPhase enum value
    """
    age = get_moon_age(dt)
    # Each phase is ~3.69 days
    phase_length = SYNODIC_MONTH / 8

    if age < phase_length:
        return MoonPhase.NEW_MOON
    elif age < 2 * phase_length:
        return MoonPhase.WAXING_CRESCENT
    elif age < 3 * phase_length:
        return MoonPhase.FIRST_QUARTER
    elif age < 4 * phase_length:
        return MoonPhase.WAXING_GIBBOUS
    elif age < 5 * phase_length:
        return MoonPhase.FULL_MOON
    elif age < 6 * phase_length:
        return MoonPhase.WANING_GIBBOUS
    elif age < 7 * phase_length:
        return MoonPhase.LAST_QUARTER
    else:
        return MoonPhase.WANING_CRESCENT


def _parse_usno_phase(phase_str: str) -> MoonPhase:
    """Parse USNO phase string to MoonPhase enum."""
    mapping = {
        "New Moon": MoonPhase.NEW_MOON,
        "First Quarter": MoonPhase.FIRST_QUARTER,
        "Full Moon": MoonPhase.FULL_MOON,
        "Last Quarter": MoonPhase.LAST_QUARTER,
    }
    return mapping.get(phase_str, MoonPhase.NEW_MOON)


def _parse_usno_curphase(phase_str: str) -> MoonPhase:
    """Parse USNO current phase string to MoonPhase enum."""
    mapping = {
        "New Moon": MoonPhase.NEW_MOON,
        "Waxing Crescent": MoonPhase.WAXING_CRESCENT,
        "First Quarter": MoonPhase.FIRST_QUARTER,
        "Waxing Gibbous": MoonPhase.WAXING_GIBBOUS,
        "Full Moon": MoonPhase.FULL_MOON,
        "Waning Gibbous": MoonPhase.WANING_GIBBOUS,
        "Last Quarter": MoonPhase.LAST_QUARTER,
        "Waning Crescent": MoonPhase.WANING_CRESCENT,
    }
    return mapping.get(phase_str, get_moon_phase(datetime.now(timezone.utc)))


def get_moon_info(target_date: date | datetime) -> MoonInfo:
    """
    Get moon information for a specific date (local calculation).

    Args:
        target_date: Date to check

    Returns:
        MoonInfo with phase, illumination, and age
    """
    if isinstance(target_date, date) and not isinstance(target_date, datetime):
        # Use noon UTC for date-only input
        dt = datetime.combine(
            target_date, datetime.min.time().replace(hour=12), tzinfo=timezone.utc
        )
    else:
        dt = target_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    return MoonInfo(
        date=dt.date() if isinstance(dt, datetime) else target_date,
        phase=get_moon_phase(dt),
        illumination=get_moon_illumination(dt),
        age_days=get_moon_age(dt),
        source="local",
    )


def find_next_phase(
    after: datetime,
    target_phase: MoonPhase,
    max_days: int = 60,
) -> datetime | None:
    """
    Find the next occurrence of a specific moon phase.

    Args:
        after: Start searching after this time
        target_phase: Phase to find
        max_days: Maximum days to search

    Returns:
        DateTime of the phase or None if not found
    """
    if after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    # Binary search within synodic month to find phase transition
    # First, estimate when the phase should occur
    age = get_moon_age(after)

    # Calculate target age based on phase
    phase_ages = {
        MoonPhase.NEW_MOON: 0,
        MoonPhase.WAXING_CRESCENT: SYNODIC_MONTH / 8,
        MoonPhase.FIRST_QUARTER: SYNODIC_MONTH / 4,
        MoonPhase.WAXING_GIBBOUS: 3 * SYNODIC_MONTH / 8,
        MoonPhase.FULL_MOON: SYNODIC_MONTH / 2,
        MoonPhase.WANING_GIBBOUS: 5 * SYNODIC_MONTH / 8,
        MoonPhase.LAST_QUARTER: 3 * SYNODIC_MONTH / 4,
        MoonPhase.WANING_CRESCENT: 7 * SYNODIC_MONTH / 8,
    }

    target_age = phase_ages[target_phase]
    days_until = target_age - age
    if days_until <= 0:
        days_until += SYNODIC_MONTH

    # Estimate datetime
    estimated = after + timedelta(days=days_until)

    # Refine with binary search
    low = estimated - timedelta(hours=12)
    high = estimated + timedelta(hours=12)

    for _ in range(20):  # ~minute precision after 20 iterations
        mid = low + (high - low) / 2
        if get_moon_phase(mid) == target_phase:
            # Found the phase, now find the start
            if get_moon_phase(low) == target_phase:
                return low
            high = mid
        else:
            low = mid

    return low


def get_upcoming_events(
    after: datetime | None = None,
    days: int = 30,
) -> list[MoonEvent]:
    """
    Get upcoming significant moon events (new and full moons).

    Args:
        after: Start time (defaults to now)
        days: Number of days to look ahead

    Returns:
        List of MoonEvent objects
    """
    if after is None:
        after = datetime.now(timezone.utc)
    elif after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    events = []

    for target_phase in [
        MoonPhase.NEW_MOON,
        MoonPhase.FULL_MOON,
        MoonPhase.FIRST_QUARTER,
        MoonPhase.LAST_QUARTER,
    ]:
        event_time = find_next_phase(after, target_phase)
        if event_time and (event_time - after).days <= days:
            events.append(MoonEvent(datetime=event_time, phase=target_phase))

    # Sort by date
    events.sort(key=lambda e: e.datetime)
    return events


class MoonClient:
    """Client for moon data using USNO API with local calculation fallback."""

    def __init__(self, timeout: float = 10.0):
        """Initialize the moon client."""
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_moon_info(
        self,
        target_date: date | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> MoonInfo:
        """
        Get moon info for a date using USNO API with local fallback.

        Args:
            target_date: Date to get info for (defaults to today)
            latitude: Observer latitude (optional, for USNO API)
            longitude: Observer longitude (optional, for USNO API)

        Returns:
            MoonInfo object with phase and illumination
        """
        if target_date is None:
            target_date = date.today()

        # Try USNO API if we have coordinates
        if latitude is not None and longitude is not None:
            try:
                client = await self._get_client()
                response = await client.get(
                    "https://aa.usno.navy.mil/api/rstt/oneday",
                    params={
                        "date": target_date.isoformat(),
                        "coords": f"{latitude},{longitude}",
                    },
                )
                response.raise_for_status()
                data = response.json()

                if "error" not in data:
                    props = data.get("properties", {}).get("data", {})
                    curphase = props.get("curphase", "")
                    fracillum_str = props.get("fracillum", "0%")

                    # Parse illumination (format: "93%")
                    try:
                        illumination = float(fracillum_str.replace("%", "")) / 100.0
                    except (ValueError, AttributeError):
                        illumination = get_moon_illumination(
                            datetime.combine(target_date, datetime.min.time().replace(hour=12), tzinfo=timezone.utc)
                        )

                    phase = _parse_usno_curphase(curphase)

                    # Estimate age from phase and illumination
                    dt = datetime.combine(target_date, datetime.min.time().replace(hour=12), tzinfo=timezone.utc)

                    return MoonInfo(
                        date=target_date,
                        phase=phase,
                        illumination=illumination,
                        age_days=get_moon_age(dt),
                        source="usno",
                    )
            except Exception as e:
                logger.warning(f"USNO API failed, using local calculation: {e}")

        # Fallback to local calculation
        return get_moon_info(target_date)

    async def get_upcoming_events(
        self,
        days: int = 30,
        after: datetime | None = None,
    ) -> list[MoonEvent]:
        """
        Get upcoming moon events using USNO API with local fallback.

        Args:
            days: Number of days to look ahead
            after: Start time (defaults to now)

        Returns:
            List of MoonEvent objects
        """
        if after is None:
            after = datetime.now(timezone.utc)
        elif after.tzinfo is None:
            after = after.replace(tzinfo=timezone.utc)

        # Calculate number of phases needed (roughly 4 per month)
        num_phases = max(4, (days // 7) + 4)

        try:
            client = await self._get_client()
            response = await client.get(
                f"{USNO_MOON_PHASES_API}/date",
                params={
                    "date": after.date().isoformat(),
                    "nump": min(num_phases, 99),  # API max is 99
                },
            )
            response.raise_for_status()
            data = response.json()

            if "error" not in data and "phasedata" in data:
                events = []
                end_date = after + timedelta(days=days)

                for phase_data in data["phasedata"]:
                    try:
                        # Parse date and time from USNO response
                        phase_dt = datetime(
                            year=phase_data["year"],
                            month=phase_data["month"],
                            day=phase_data["day"],
                            hour=int(phase_data["time"].split(":")[0]),
                            minute=int(phase_data["time"].split(":")[1]),
                            tzinfo=timezone.utc,
                        )

                        if after <= phase_dt <= end_date:
                            events.append(
                                MoonEvent(
                                    datetime=phase_dt,
                                    phase=_parse_usno_phase(phase_data["phase"]),
                                    source="usno",
                                )
                            )
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse USNO phase data: {e}")
                        continue

                if events:
                    events.sort(key=lambda e: e.datetime)
                    return events

        except Exception as e:
            logger.warning(f"USNO API failed, using local calculation: {e}")

        # Fallback to local calculation
        return get_upcoming_events(after=after, days=days)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
