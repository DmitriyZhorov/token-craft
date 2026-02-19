"""
Streak & Combo Bonus System

Rewards consistent improvement and multi-category excellence.

Streak System:
- Tracks consecutive sessions with score improvement
- Multiplier increases 1.0x → 1.25x over 6 sessions
- Bonus points scale from +10 → +50 per session
- Breaks if score doesn't improve vs previous session

Combo Bonuses:
- Rewards achieving 80%+ in multiple categories simultaneously
- 2 categories: +25 pts
- 3 categories: +50 pts
- 4 categories: +100 pts
- 5+ categories: +150 pts (MASTERY)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class StreakSystem:
    """Manages consecutive improvement streaks."""

    # Streak progression table
    STREAK_PROGRESSION = [
        {"sessions": 1, "multiplier": 1.00, "bonus_points": 0},
        {"sessions": 2, "multiplier": 1.05, "bonus_points": 10},
        {"sessions": 3, "multiplier": 1.10, "bonus_points": 20},
        {"sessions": 4, "multiplier": 1.15, "bonus_points": 30},
        {"sessions": 5, "multiplier": 1.20, "bonus_points": 40},
        {"sessions": 6, "multiplier": 1.25, "bonus_points": 50},  # Max
    ]

    def __init__(self, user_profile: Optional[Dict] = None):
        """
        Initialize streak system with optional user profile data.

        Args:
            user_profile: User profile dict with streak history
        """
        self.user_profile = user_profile or {}
        self.current_streak = self._load_current_streak()
        self.best_streak = self._load_best_streak()

    def _load_current_streak(self) -> Dict:
        """Load current streak from profile or initialize."""
        if "streak_info" in self.user_profile:
            return self.user_profile["streak_info"].get("current", self._new_streak())
        return self._new_streak()

    def _load_best_streak(self) -> Dict:
        """Load best streak from profile or initialize."""
        if "streak_info" in self.user_profile:
            return self.user_profile["streak_info"].get("best", self._new_streak())
        return self._new_streak()

    @staticmethod
    def _new_streak() -> Dict:
        """Create a new streak record."""
        return {
            "length": 0,
            "start_date": None,
            "last_session_date": None,
            "last_session_score": 0,
            "bonus_points_earned": 0,
        }

    def check_improvement(self, current_score: float, previous_score: float) -> bool:
        """
        Check if current session improved vs previous.

        Args:
            current_score: Current session score
            previous_score: Previous session score

        Returns:
            True if improved (current > previous)
        """
        return current_score > previous_score

    def update_streak(
        self, improved: bool, current_score: float, session_date: Optional[str] = None
    ) -> Dict:
        """
        Update streak based on improvement check.

        Args:
            improved: Whether score improved vs previous session
            current_score: Current session score
            session_date: Date of session (ISO format), defaults to now

        Returns:
            Updated streak info with multiplier and bonus
        """
        if session_date is None:
            session_date = datetime.now().isoformat()

        if improved:
            # Extend streak
            self.current_streak["length"] += 1

            # Cap at max streak (6 sessions)
            if self.current_streak["length"] > 6:
                self.current_streak["length"] = 6

            # Update best streak if needed
            if self.current_streak["length"] > self.best_streak["length"]:
                self.best_streak = dict(self.current_streak)

            # Initialize start date if new streak
            if self.current_streak["start_date"] is None:
                self.current_streak["start_date"] = session_date

            self.current_streak["last_session_date"] = session_date
            self.current_streak["last_session_score"] = current_score
        else:
            # Streak broken - reset current, keep best
            self.current_streak = self._new_streak()

        return self.get_streak_bonus()

    def get_streak_bonus(self) -> Dict:
        """
        Get current streak bonus (multiplier and points).

        Returns:
            Dict with multiplier and bonus_points
        """
        streak_length = self.current_streak["length"]

        # Find matching progression entry
        progression = self.STREAK_PROGRESSION[-1]  # Default to max
        for entry in self.STREAK_PROGRESSION:
            if entry["sessions"] == streak_length:
                progression = entry
                break

        return {
            "streak_length": streak_length,
            "multiplier": progression["multiplier"],
            "bonus_points": progression["bonus_points"],
            "is_active": streak_length > 0,
            "start_date": self.current_streak["start_date"],
            "last_session_date": self.current_streak["last_session_date"],
        }

    def to_dict(self) -> Dict:
        """Serialize streak system to dict for storage."""
        return {
            "current": self.current_streak,
            "best": self.best_streak,
        }


class ComboBonus:
    """Manages multi-category excellence bonuses."""

    # Combo thresholds (80% = excellent in category)
    COMBO_THRESHOLD = 0.80

    # Bonus tiers
    COMBO_TIERS = [
        {"categories": 2, "bonus": 25, "name": "Focused"},
        {"categories": 3, "bonus": 50, "name": "Well-Rounded"},
        {"categories": 4, "bonus": 100, "name": "Proficiency"},
        {"categories": 5, "bonus": 150, "name": "MASTERY"},
    ]

    @staticmethod
    def calculate_category_percentage(score: float, max_score: float) -> float:
        """
        Calculate achievement percentage in a category.

        Args:
            score: Current score in category
            max_score: Maximum possible score in category

        Returns:
            Percentage (0-1)
        """
        if max_score == 0:
            return 0.0
        return min(1.0, score / max_score)

    @classmethod
    def check_combo(cls, category_scores: Dict[str, Dict]) -> Dict:
        """
        Check for combo bonuses across categories.

        Args:
            category_scores: Dict of {category_name: {"score": X, "max_score": Y}}

        Returns:
            Dict with combo status and bonus
        """
        # Calculate percentage for each category
        percentages = {}
        for category, data in category_scores.items():
            pct = cls.calculate_category_percentage(data["score"], data["max_score"])
            percentages[category] = pct

        # Count categories at or above threshold
        excellent_categories = sum(1 for pct in percentages.values() if pct >= cls.COMBO_THRESHOLD)

        # Find matching tier
        bonus_tier = None
        for tier in cls.COMBO_TIERS:
            if excellent_categories >= tier["categories"]:
                bonus_tier = tier

        bonus = 0
        tier_name = "None"
        if bonus_tier:
            bonus = bonus_tier["bonus"]
            tier_name = bonus_tier["name"]

        return {
            "combo_active": excellent_categories >= 2,
            "excellent_categories": excellent_categories,
            "category_percentages": {k: round(v * 100, 1) for k, v in percentages.items()},
            "bonus_points": bonus,
            "tier_name": tier_name,
            "details": {
                "threshold": f"{cls.COMBO_THRESHOLD * 100:.0f}%",
                "excellent_count": excellent_categories,
            },
        }

    @classmethod
    def get_combo_milestones(cls) -> List[Dict]:
        """
        Get all combo bonus milestones for user reference.

        Returns:
            List of combo tier information
        """
        milestones = []
        for tier in cls.COMBO_TIERS:
            milestones.append(
                {
                    "name": tier["name"],
                    "requirement": f"{tier['categories']} categories at {cls.COMBO_THRESHOLD * 100:.0f}%+",
                    "bonus": tier["bonus"],
                    "bonus_description": f"+{tier['bonus']} bonus points",
                }
            )
        return milestones
