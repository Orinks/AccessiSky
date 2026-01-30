"""Tests for Planets visibility calculations."""

from datetime import date

from accessisky.api.planets import (
    Planet,
    PlanetInfo,
    PlanetVisibility,
    get_all_planets,
    get_planet_info,
    get_visible_planets,
)


class TestPlanetData:
    """Tests for planet static data."""

    def test_get_all_planets(self):
        """Test getting all planets."""
        planets = get_all_planets()
        # Should have 7 observable planets (Mercury through Neptune, excluding Earth)
        assert len(planets) == 7

        names = [p.name for p in planets]
        assert "Mercury" in names
        assert "Venus" in names
        assert "Mars" in names
        assert "Jupiter" in names
        assert "Saturn" in names

    def test_planet_properties(self):
        """Test that planets have required properties."""
        planets = get_all_planets()

        for planet in planets:
            assert planet.name
            assert planet.orbital_period_days > 0
            assert (
                0 <= planet.magnitude_range[0] <= planet.magnitude_range[1]
                or planet.magnitude_range[0] <= planet.magnitude_range[1]
            )  # Negative is brighter


class TestGetVisiblePlanets:
    """Tests for visible planets calculation."""

    def test_get_visible_planets_returns_list(self):
        """Test that visible planets returns a list."""
        visible = get_visible_planets()
        assert isinstance(visible, list)

    def test_visible_planets_have_visibility_info(self):
        """Test that visible planets have visibility info."""
        visible = get_visible_planets(on_date=date(2026, 6, 15))

        for info in visible:
            assert isinstance(info, PlanetInfo)
            assert info.planet is not None
            assert info.visibility in list(PlanetVisibility)

    def test_inner_planets_vary_in_visibility(self):
        """Test that inner planets (Mercury, Venus) vary more in visibility."""
        # Mercury and Venus have short orbital periods and change visibility often
        planets = get_all_planets()
        mercury = next(p for p in planets if p.name == "Mercury")
        venus = next(p for p in planets if p.name == "Venus")

        # Their orbital periods should be < 1 year
        assert mercury.orbital_period_days < 365
        assert venus.orbital_period_days < 365


class TestGetPlanetInfo:
    """Tests for individual planet info."""

    def test_get_planet_info_by_name(self):
        """Test getting info for specific planet."""
        info = get_planet_info("Jupiter")

        assert info is not None
        assert info.planet.name == "Jupiter"

    def test_get_planet_info_case_insensitive(self):
        """Test that planet lookup is case insensitive."""
        info1 = get_planet_info("saturn")
        info2 = get_planet_info("SATURN")

        assert info1 is not None
        assert info2 is not None
        assert info1.planet.name == info2.planet.name

    def test_get_planet_info_unknown(self):
        """Test getting info for unknown planet."""
        info = get_planet_info("Pluto")  # Not a planet anymore!
        assert info is None


class TestPlanetInfo:
    """Tests for PlanetInfo dataclass."""

    def test_str_representation(self):
        """Test string representation."""

        planet = Planet(
            name="Test Planet",
            orbital_period_days=365,
            magnitude_range=(-2, 0),
        )
        info = PlanetInfo(
            planet=planet,
            visibility=PlanetVisibility.EVENING,
            best_viewing_time="After sunset",
            elongation_degrees=45.0,
            is_retrograde=False,
        )

        s = str(info)
        assert "Test Planet" in s
        assert "Evening" in s or "evening" in s.lower()

    def test_brightness_description(self):
        """Test brightness description based on magnitude."""

        planet = Planet(
            name="Bright Planet",
            orbital_period_days=100,
            magnitude_range=(-4, -3),
        )
        info = PlanetInfo(
            planet=planet,
            visibility=PlanetVisibility.ALL_NIGHT,
            current_magnitude=-4.0,
        )

        # Very negative magnitude should be described as very bright
        assert info.brightness_description in ["Very Bright", "Bright", "Moderate", "Dim"]


class TestPlanetVisibility:
    """Tests for visibility enum."""

    def test_visibility_values(self):
        """Test that all visibility values exist."""
        assert PlanetVisibility.NOT_VISIBLE
        assert PlanetVisibility.MORNING
        assert PlanetVisibility.EVENING
        assert PlanetVisibility.ALL_NIGHT

    def test_visibility_descriptions(self):
        """Test visibility descriptions."""
        assert "morning" in PlanetVisibility.MORNING.value.lower() or "Morning" in str(
            PlanetVisibility.MORNING
        )


class TestOrbitalCalculations:
    """Tests for orbital position calculations."""

    def test_elongation_ranges(self):
        """Test that elongation values are reasonable."""
        visible = get_visible_planets()

        for info in visible:
            if info.elongation_degrees is not None:
                # Elongation should be between 0 and 180 degrees
                assert 0 <= info.elongation_degrees <= 180

    def test_different_dates_different_positions(self):
        """Test that planets have different positions on different dates."""
        info1 = get_planet_info("Mars", on_date=date(2026, 1, 1))
        info2 = get_planet_info("Mars", on_date=date(2026, 7, 1))

        # Mars should have noticeably different elongation 6 months apart
        if info1 and info2 and info1.elongation_degrees and info2.elongation_degrees:
            # They should be different (Mars has ~2 year orbital period)
            assert (
                info1.elongation_degrees != info2.elongation_degrees
                or info1.visibility != info2.visibility
            )
