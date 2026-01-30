"""Tests for Viewing Conditions score calculation."""

from accessisky.api.viewing import (
    CloudCover,
    ViewingConditions,
    ViewingScore,
    calculate_viewing_score,
    get_moon_interference,
    get_viewing_conditions,
)


class TestMoonInterference:
    """Tests for moon interference calculation."""

    def test_new_moon_no_interference(self):
        """Test that new moon has minimal interference."""
        # New moon = ~0% illumination
        interference = get_moon_interference(illumination_percent=0)
        assert interference < 0.1  # Very low interference

    def test_full_moon_high_interference(self):
        """Test that full moon has high interference."""
        # Full moon = 100% illumination
        interference = get_moon_interference(illumination_percent=100)
        assert interference > 0.8  # High interference

    def test_half_moon_moderate_interference(self):
        """Test that half moon has moderate interference."""
        interference = get_moon_interference(illumination_percent=50)
        assert 0.3 <= interference <= 0.7  # Moderate

    def test_interference_scales_with_illumination(self):
        """Test that interference scales with illumination."""
        low = get_moon_interference(illumination_percent=20)
        mid = get_moon_interference(illumination_percent=50)
        high = get_moon_interference(illumination_percent=80)

        assert low < mid < high


class TestCloudCover:
    """Tests for cloud cover enum."""

    def test_cloud_cover_values(self):
        """Test cloud cover enum values."""
        assert CloudCover.CLEAR
        assert CloudCover.PARTLY_CLOUDY
        assert CloudCover.MOSTLY_CLOUDY
        assert CloudCover.OVERCAST

    def test_cloud_cover_from_percent(self):
        """Test creating cloud cover from percentage."""
        clear = CloudCover.from_percent(10)
        assert clear == CloudCover.CLEAR

        partly = CloudCover.from_percent(35)
        assert partly == CloudCover.PARTLY_CLOUDY

        overcast = CloudCover.from_percent(95)
        assert overcast == CloudCover.OVERCAST


class TestViewingScore:
    """Tests for viewing score enum."""

    def test_score_values(self):
        """Test viewing score values."""
        assert ViewingScore.EXCELLENT
        assert ViewingScore.GOOD
        assert ViewingScore.FAIR
        assert ViewingScore.POOR
        assert ViewingScore.NOT_RECOMMENDED

    def test_score_from_value(self):
        """Test creating score from numeric value."""
        excellent = ViewingScore.from_value(90)
        assert excellent == ViewingScore.EXCELLENT

        poor = ViewingScore.from_value(30)
        assert poor == ViewingScore.POOR


class TestCalculateViewingScore:
    """Tests for viewing score calculation."""

    def test_perfect_conditions(self):
        """Test score with perfect conditions."""
        score = calculate_viewing_score(
            cloud_cover_percent=0,
            moon_illumination_percent=0,
            is_astronomical_night=True,
        )

        assert score >= 90  # Should be excellent

    def test_terrible_conditions(self):
        """Test score with terrible conditions."""
        score = calculate_viewing_score(
            cloud_cover_percent=100,
            moon_illumination_percent=100,
            is_astronomical_night=False,
        )

        assert score < 30  # Should be poor or not recommended

    def test_cloud_cover_impact(self):
        """Test that cloud cover significantly impacts score."""
        clear = calculate_viewing_score(cloud_cover_percent=0)
        cloudy = calculate_viewing_score(cloud_cover_percent=80)

        assert clear > cloudy + 30  # Significant difference

    def test_moon_impact(self):
        """Test that moon illumination impacts score."""
        new_moon = calculate_viewing_score(moon_illumination_percent=0)
        full_moon = calculate_viewing_score(moon_illumination_percent=100)

        assert new_moon > full_moon + 10  # Noticeable difference

    def test_twilight_impact(self):
        """Test that twilight reduces score."""
        night = calculate_viewing_score(is_astronomical_night=True)
        twilight = calculate_viewing_score(is_astronomical_night=False)

        assert night > twilight


class TestViewingConditions:
    """Tests for ViewingConditions dataclass."""

    def test_conditions_creation(self):
        """Test creating viewing conditions."""
        conditions = ViewingConditions(
            score=ViewingScore.GOOD,
            numeric_score=75,
            cloud_cover=CloudCover.PARTLY_CLOUDY,
            moon_illumination_percent=30,
            is_dark_sky=True,
            summary="Good conditions for observing",
        )

        assert conditions.score == ViewingScore.GOOD
        assert conditions.numeric_score == 75
        assert conditions.is_dark_sky is True

    def test_str_representation(self):
        """Test string representation."""
        conditions = ViewingConditions(
            score=ViewingScore.EXCELLENT,
            numeric_score=95,
            cloud_cover=CloudCover.CLEAR,
            moon_illumination_percent=5,
            is_dark_sky=True,
            summary="Excellent stargazing conditions",
        )

        s = str(conditions)
        assert "Excellent" in s or "excellent" in s.lower()

    def test_recommendations(self):
        """Test that conditions include recommendations."""
        conditions = ViewingConditions(
            score=ViewingScore.FAIR,
            numeric_score=55,
            cloud_cover=CloudCover.PARTLY_CLOUDY,
            moon_illumination_percent=70,
            is_dark_sky=True,
            summary="Fair conditions",
            recommendations=["Moon is bright - best for planets", "Some clouds expected"],
        )

        assert len(conditions.recommendations) == 2


class TestGetViewingConditions:
    """Tests for get_viewing_conditions function."""

    def test_returns_conditions(self):
        """Test that function returns ViewingConditions."""
        conditions = get_viewing_conditions(
            cloud_cover_percent=20,
            moon_illumination_percent=40,
        )

        assert isinstance(conditions, ViewingConditions)

    def test_conditions_has_all_fields(self):
        """Test that conditions has all required fields."""
        conditions = get_viewing_conditions(
            cloud_cover_percent=50,
            moon_illumination_percent=50,
        )

        assert conditions.score is not None
        assert conditions.numeric_score is not None
        assert conditions.cloud_cover is not None
        assert conditions.summary is not None
