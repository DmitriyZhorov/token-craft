"""
Space Exploration Rank System

10 ranks from Cadet to Galactic Legend based on token optimization mastery.
Updated for v3.0 - 2300 total points (exponential progression, 3-6 months to max).
"""

from typing import Dict, Optional


class SpaceRankSystem:
    """Manage space exploration ranks and progression."""

    # Updated for v3.0 - 2300 total points, 10 ranks, exponential curve
    # Time to max: ~3-6 months of sustained excellence (vs 2 weeks in v2.0)
    RANKS = [
        {
            "name": "Cadet",
            "min": 0,
            "max": 99,
            "description": "Academy training, learning fundamentals",
            "badge_id": "token_craft_cadet",
            "icon": "🎓"
        },
        {
            "name": "Navigator",
            "min": 100,
            "max": 199,
            "description": "Charting efficient courses",
            "badge_id": "token_craft_navigator",
            "icon": "🧭"
        },
        {
            "name": "Pilot",
            "min": 200,
            "max": 349,
            "description": "First missions, gaining experience",
            "badge_id": "token_craft_pilot",
            "icon": "✈️"
        },
        {
            "name": "Explorer",
            "min": 350,
            "max": 549,
            "description": "Venturing into uncharted space",
            "badge_id": "token_craft_explorer",
            "icon": "🚀"
        },
        {
            "name": "Captain",
            "min": 550,
            "max": 799,
            "description": "Commanding missions with excellence",
            "badge_id": "token_craft_captain",
            "icon": "👨‍✈️"
        },
        {
            "name": "Commander",
            "min": 800,
            "max": 1099,
            "description": "Leading with precision and strategy",
            "badge_id": "token_craft_commander",
            "icon": "⭐"
        },
        {
            "name": "Admiral",
            "min": 1100,
            "max": 1449,
            "description": "Fleet command, strategic excellence",
            "badge_id": "token_craft_admiral",
            "icon": "🎖️"
        },
        {
            "name": "Commodore",
            "min": 1450,
            "max": 1849,
            "description": "Supreme commander of fleets",
            "badge_id": "token_craft_commodore",
            "icon": "👑"
        },
        {
            "name": "Fleet Admiral",
            "min": 1850,
            "max": 2299,
            "description": "Master of token optimization",
            "badge_id": "token_craft_fleet_admiral",
            "icon": "⚔️"
        },
        {
            "name": "Galactic Legend",
            "min": 2300,
            "max": 9999,
            "description": "Explored uncharted territories, achieved mastery",
            "badge_id": "token_craft_legend",
            "icon": "🌌"
        },
    ]

    @classmethod
    def get_rank(cls, score: int) -> Dict:
        """
        Get current rank information based on score.

        Args:
            score: User's total score

        Returns:
            Dict with rank details including name, range, progress
        """
        for rank in cls.RANKS:
            if rank["min"] <= score <= rank["max"]:
                progress_in_rank = score - rank["min"]
                rank_range = rank["max"] - rank["min"] + 1
                progress_pct = (progress_in_rank / rank_range) * 100

                return {
                    **rank,
                    "current_score": score,
                    "progress_in_rank": progress_in_rank,
                    "rank_range": rank_range,
                    "progress_pct": progress_pct
                }

        # If score exceeds all ranks, return max rank
        return {
            **cls.RANKS[-1],
            "current_score": score,
            "progress_in_rank": score - cls.RANKS[-1]["min"],
            "rank_range": 1,
            "progress_pct": 100
        }

    @classmethod
    def get_next_rank(cls, score: int) -> Optional[Dict]:
        """
        Get next rank and points needed.

        Args:
            score: User's total score

        Returns:
            Dict with next rank info, or None if at max rank
        """
        current_rank = cls.get_rank(score)

        # Find next rank in list
        for i, rank in enumerate(cls.RANKS):
            if rank["name"] == current_rank["name"]:
                if i + 1 < len(cls.RANKS):
                    next_rank = cls.RANKS[i + 1]
                    points_needed = next_rank["min"] - score

                    return {
                        **next_rank,
                        "points_needed": points_needed
                    }
                else:
                    return None  # Already at max rank

        return None

    @classmethod
    def get_progress_bar(cls, score: int, width: int = 50, filled_char: str = "█", empty_char: str = "░") -> str:
        """
        Generate ASCII progress bar for current rank.

        Args:
            score: User's total score
            width: Width of progress bar in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion

        Returns:
            ASCII progress bar string
        """
        rank_info = cls.get_rank(score)
        progress_pct = rank_info["progress_pct"]

        filled = int((progress_pct / 100) * width)
        empty = width - filled

        return f"{filled_char * filled}{empty_char * empty}"

    @classmethod
    def get_rank_badge_ascii(cls, rank_name: str) -> str:
        """
        Get ASCII art badge for rank.

        Args:
            rank_name: Name of the rank

        Returns:
            ASCII art representation
        """
        rank = next((r for r in cls.RANKS if r["name"] == rank_name), None)
        if not rank:
            return ""

        icon = rank["icon"]
        name = rank["name"].upper()

        # Create ASCII badge
        border_len = max(len(name) + 4, 20)
        border = "=" * border_len

        badge = f"""
{border}
  {icon}  {name}  {icon}
{border}
"""
        return badge.strip()

    @classmethod
    def calculate_rank_level(cls, score: int) -> int:
        """
        Get numeric rank level (1-10).

        Args:
            score: User's total score

        Returns:
            Rank level from 1 (Cadet) to 10 (Galactic Legend)
        """
        rank_info = cls.get_rank(score)
        for i, rank in enumerate(cls.RANKS):
            if rank["name"] == rank_info["name"]:
                return i + 1
        return 1

    @classmethod
    def get_all_ranks(cls) -> list:
        """Get list of all ranks."""
        return cls.RANKS.copy()

    @classmethod
    def get_rank_by_name(cls, name: str) -> Optional[Dict]:
        """Get rank details by name."""
        return next((r for r in cls.RANKS if r["name"].lower() == name.lower()), None)
