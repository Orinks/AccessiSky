"""Viewing conditions score calculation.

Combines weather (clouds), moon brightness, and darkness level
into an overall "stargazing score" for tonight.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CloudCover(Enum):
    """Cloud cover categories."""

    CLEAR = "Clear skies"
    PARTLY_CLOUDY = "Partly cloudy"
    MOSTLY_CLOUDY = "Mostly cloudy"
    OVERCAST = "Overcast"

    @classmethod
    def from_percent(cls, percent: float) -> CloudCover:
        """Create CloudCover from percentage."""
        if percent < 25:
            return cls.CLEAR
        elif percent < 50:
            return cls.PARTLY_CLOUDY
        elif percent < 75:
            return cls.MOSTLY_CLOUDY
        else:
            return cls.OVERCAST


class ViewingScore(Enum):
    """Overall viewing score categories."""

    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    NOT_RECOMMENDED = "Not Recommended"

    @classmethod
    def from_value(cls, value: float) -> ViewingScore:
        """Create ViewingScore from numeric value (0-100)."""
        if value >= 80:
            return cls.EXCELLENT
        elif value >= 60:
            return cls.GOOD
        elif value >= 40:
            return cls.FAIR
        elif value >= 20:
            return cls.POOR
        else:
            return cls.NOT_RECOMMENDED


@dataclass
class ViewingConditions:
    """Complete viewing conditions assessment."""

    score: ViewingScore
    numeric_score: int  # 0-100
    cloud_cover: CloudCover
    moon_illumination_percent: int
    is_dark_sky: bool
    summary: str
    recommendations: list[str] = field(default_factory=list)

    # Optional detailed info
    bortle_scale: int | None = None  # 1-9 light pollution scale
    transparency: str | None = None
    seeing: str | None = None  # Atmospheric stability

    def __str__(self) -> str:
        rec_str = ""
        if self.recommendations:
            rec_str = " | " + "; ".join(self.recommendations[:2])
        return f"{self.score.value} ({self.numeric_score}/100): {self.summary}{rec_str}"


def get_moon_interference(
    illumination_percent: float,
    is_moon_up: bool = True,
) -> float:
    """
    Calculate moon interference factor (0.0 to 1.0).

    Args:
        illumination_percent: Moon illumination (0-100)
        is_moon_up: Whether moon is above horizon

    Returns:
        Interference factor where 0 = no interference, 1 = maximum
    """
    if not is_moon_up:
        return 0.0

    # Moon interference scales non-linearly with illumination
    # A 50% illuminated moon isn't half as bad as a full moon
    # Use a power function to model this
    normalized = illumination_percent / 100.0

    # Power of 0.7 makes the curve slightly concave
    # meaning partial moons are more impactful than linear
    return normalized**0.7


def calculate_viewing_score(
    cloud_cover_percent: float = 0,
    moon_illumination_percent: float = 0,
    is_astronomical_night: bool = True,
    is_moon_up: bool = True,
    light_pollution_factor: float = 0.0,  # 0-1, 0 = dark site
) -> int:
    """
    Calculate an overall viewing score (0-100).

    The score is weighted:
    - Cloud cover: 50% (most important)
    - Moon brightness: 25%
    - Sky darkness: 15%
    - Light pollution: 10%

    Args:
        cloud_cover_percent: Cloud cover 0-100
        moon_illumination_percent: Moon illumination 0-100
        is_astronomical_night: True if sun is >18° below horizon
        is_moon_up: Whether moon is above horizon
        light_pollution_factor: Light pollution 0-1

    Returns:
        Score from 0 to 100
    """
    # Cloud cover score (0-100, inverted: clear = 100)
    cloud_score = 100 - cloud_cover_percent

    # Moon score (0-100, inverted: new moon = 100)
    moon_interference = get_moon_interference(moon_illumination_percent, is_moon_up)
    moon_score = 100 * (1 - moon_interference)

    # Darkness score (0-100)
    darkness_score = 100 if is_astronomical_night else 40

    # Light pollution score (0-100, inverted)
    lp_score = 100 * (1 - light_pollution_factor)

    # Weighted combination
    total = cloud_score * 0.50 + moon_score * 0.25 + darkness_score * 0.15 + lp_score * 0.10

    return int(round(total))


def _generate_recommendations(
    cloud_cover_percent: float,
    moon_illumination_percent: float,
    is_astronomical_night: bool,
    is_moon_up: bool,
) -> list[str]:
    """Generate viewing recommendations based on conditions."""
    recommendations = []

    # Cloud recommendations
    if cloud_cover_percent > 75:
        recommendations.append("Heavy cloud cover - wait for clearer skies")
    elif cloud_cover_percent > 50:
        recommendations.append("Significant clouds - viewing may be intermittent")
    elif cloud_cover_percent > 25:
        recommendations.append("Some clouds - find gaps for observing")

    # Moon recommendations
    if moon_illumination_percent > 80 and is_moon_up:
        recommendations.append("Bright moon - best for planets and the Moon itself")
    elif moon_illumination_percent > 50 and is_moon_up:
        recommendations.append("Moon is up - deep sky objects may be washed out")
    elif moon_illumination_percent < 20:
        recommendations.append("Dark moon - great for galaxies and nebulae")

    # Darkness recommendations
    if not is_astronomical_night:
        recommendations.append("Not fully dark - brighter objects only")

    # Positive reinforcement for good conditions
    if cloud_cover_percent < 20 and moon_illumination_percent < 30:
        recommendations.append("Excellent for deep sky observing!")

    return recommendations


def _generate_summary(score: ViewingScore, cloud_cover: CloudCover) -> str:
    """Generate a summary description."""
    summaries = {
        ViewingScore.EXCELLENT: "Outstanding stargazing conditions",
        ViewingScore.GOOD: "Good conditions for astronomy",
        ViewingScore.FAIR: "Acceptable viewing with some limitations",
        ViewingScore.POOR: "Challenging conditions for observing",
        ViewingScore.NOT_RECOMMENDED: "Not suitable for stargazing",
    }

    base = summaries[score]

    if cloud_cover == CloudCover.OVERCAST:
        return "Overcast skies - wait for better conditions"
    elif cloud_cover == CloudCover.MOSTLY_CLOUDY:
        return f"{base} - clouds may interfere"

    return base


def get_viewing_conditions(
    cloud_cover_percent: float = 0,
    moon_illumination_percent: float = 0,
    is_astronomical_night: bool = True,
    is_moon_up: bool = True,
    light_pollution_factor: float = 0.0,
) -> ViewingConditions:
    """
    Get complete viewing conditions assessment.

    Args:
        cloud_cover_percent: Cloud cover 0-100
        moon_illumination_percent: Moon illumination 0-100
        is_astronomical_night: True if sun is >18° below horizon
        is_moon_up: Whether moon is above horizon
        light_pollution_factor: Light pollution 0-1

    Returns:
        ViewingConditions with score and recommendations
    """
    # Calculate numeric score
    numeric_score = calculate_viewing_score(
        cloud_cover_percent=cloud_cover_percent,
        moon_illumination_percent=moon_illumination_percent,
        is_astronomical_night=is_astronomical_night,
        is_moon_up=is_moon_up,
        light_pollution_factor=light_pollution_factor,
    )

    # Determine categorical score
    score = ViewingScore.from_value(numeric_score)

    # Determine cloud cover category
    cloud_cover = CloudCover.from_percent(cloud_cover_percent)

    # Generate recommendations
    recommendations = _generate_recommendations(
        cloud_cover_percent=cloud_cover_percent,
        moon_illumination_percent=moon_illumination_percent,
        is_astronomical_night=is_astronomical_night,
        is_moon_up=is_moon_up,
    )

    # Generate summary
    summary = _generate_summary(score, cloud_cover)

    return ViewingConditions(
        score=score,
        numeric_score=numeric_score,
        cloud_cover=cloud_cover,
        moon_illumination_percent=int(round(moon_illumination_percent)),
        is_dark_sky=is_astronomical_night and light_pollution_factor < 0.3,
        summary=summary,
        recommendations=recommendations,
    )


class ViewingClient:
    """Client interface for viewing conditions (for consistency with other API clients)."""

    async def get_viewing_conditions(
        self,
        cloud_cover_percent: float = 0,
        moon_illumination_percent: float = 0,
        is_astronomical_night: bool = True,
        is_moon_up: bool = True,
        light_pollution_factor: float = 0.0,
    ) -> ViewingConditions:
        """Get viewing conditions assessment."""
        return get_viewing_conditions(
            cloud_cover_percent=cloud_cover_percent,
            moon_illumination_percent=moon_illumination_percent,
            is_astronomical_night=is_astronomical_night,
            is_moon_up=is_moon_up,
            light_pollution_factor=light_pollution_factor,
        )

    async def close(self) -> None:
        """No-op for API consistency."""
        pass
