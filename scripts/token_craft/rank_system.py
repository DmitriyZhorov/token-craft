"""
Space Exploration Rank System

7 ranks from Cadet to Galactic Legend based on token optimization mastery.
"""

from typing import Dict, Optional


class SpaceRankSystem:
    """Manage space exploration ranks and progression."""

    # Updated for v2.0 - 1350 total points (was 1000)
    RANKS = [
        {
            "name": "Cadet",
            "min": 0,
            "max": 269,
            "description": "Academy training, learning fundamentals",
            "badge_id": "token_craft_cadet",
            "icon": "🎓"
        },
        {
            "name": "Pilot",
            "min": 270,
            "max": 539,
            "description": "First missions, gaining experience",
            "badge_id": "token_craft_pilot",
            "icon": "✈️"
        },
        {
            "name": "Navigator",
            "min": 540,
            "max": 809,
            "description": "Charting efficient courses",
            "badge_id": "token_craft_navigator",
            "icon": "🧭"
        },
        {
            "name": "Commander",
            "min": 810,
            "max": 1079,
            "description": "Leading missions with precision",
            "badge_id": "token_craft_commander",
            "icon": "⭐"
        },
        {
            "name": "Captain",
            "min": 1080,
            "max": 1349,
            "description": "Commanding the ship with mastery",
            "badge_id": "token_craft_captain",
            "icon": "👨‍✈️"
        },
        {
            "name": "Admiral",
            "min": 1350,
            "max": 1619,
            "description": "Fleet command, strategic excellence",
            "badge_id": "token_craft_admiral",
            "icon": "🎖️"
        },
        {
            "name": "Galactic Legend",
            "min": 1620,
            "max": 9999,
            "description": "Explored uncharted territories",
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
        Get numeric rank level (1-7).

        Args:
            score: User's total score

        Returns:
            Rank level from 1 (Cadet) to 7 (Galactic Legend)
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
