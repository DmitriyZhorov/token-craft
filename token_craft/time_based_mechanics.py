"""
Time-Based Mechanics

Implements recency bonuses, inactivity decay, and seasonal resets.

Recency Bonus:
- Same day: +25% multiplier
- 1-7 days: +15% multiplier
- 8-14 days: +5% multiplier
- 15+ days: no bonus

Inactivity Decay:
- 0-3 days: 1.0x (no decay)
- 4-7 days: 0.95x
- 8-14 days: 0.85x
- 15-30 days: 0.70x
- 31+ days: 0.50x

Seasonal Reset:
- Every 30 days, reset current season score
- Keep 50% of season score in lifetime score
- Encourages fresh competition each month
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


class TimeBasedMechanics:
    """Manages time-based score adjustments and seasonal mechanics."""

    @staticmethod
    def get_days_since(date_str: str) -> int:
        """
        Calculate days since a date.

        Args:
            date_str: ISO format date string

        Returns:
            Days elapsed (integer)
        """
        try:
            past_date = datetime.fromisoformat(date_str)
            now = datetime.now()
            delta = now - past_date
            return delta.days
        except (ValueError, TypeError):
            return 999  # Very old if parsing fails

    @classmethod
    def calculate_recency_bonus(cls, session_date: str) -> Dict:
        """
        Calculate recency bonus multiplier.

        Args:
            session_date: ISO format date of session

        Returns:
            Dict with bonus multiplier and days info
        """
        days_ago = cls.get_days_since(session_date)

        if days_ago == 0:
            # Same day
            multiplier = 1.25
            bonus_pct = 25
            description = "Same day improvement - Hot streak!"
        elif days_ago <= 7:
            # Within week
            multiplier = 1.15
            bonus_pct = 15
            description = f"Recent improvement ({days_ago} days ago)"
        elif days_ago <= 14:
            # Within 2 weeks
            multiplier = 1.05
            bonus_pct = 5
            description = f"Earlier this week ({days_ago} days ago)"
        else:
            # Older
            multiplier = 1.0
            bonus_pct = 0
            description = f"Stale improvement ({days_ago} days ago)"

        return {
            "multiplier": multiplier,
            "bonus_pct": bonus_pct,
            "days_ago": days_ago,
            "description": description,
        }

    @classmethod
    def calculate_inactivity_decay(cls, last_session_date: str) -> Dict:
        """
        Calculate inactivity decay multiplier.

        Reduces score if user hasn't played recently.

        Args:
            last_session_date: ISO format date of last session

        Returns:
            Dict with decay multiplier and warning level
        """
        days_inactive = cls.get_days_since(last_session_date)

        if days_inactive <= 3:
            multiplier = 1.0
            decay_pct = 0
            warning_level = "none"
            description = "Active player"
        elif days_inactive <= 7:
            multiplier = 0.95
            decay_pct = 5
            warning_level = "minor"
            description = "Slight activity gap"
        elif days_inactive <= 14:
            multiplier = 0.85
            decay_pct = 15
            warning_level = "moderate"
            description = "Noticeable inactivity"
        elif days_inactive <= 30:
            multiplier = 0.70
            decay_pct = 30
            warning_level = "significant"
            description = "Extended inactivity"
        else:
            multiplier = 0.50
            decay_pct = 50
            warning_level = "critical"
            description = f"Very inactive ({days_inactive} days)"

        return {
            "multiplier": multiplier,
            "decay_pct": decay_pct,
            "days_inactive": days_inactive,
            "warning_level": warning_level,
            "description": description,
        }

    @classmethod
    def calculate_seasonal_reset(cls, last_reset_date: Optional[str] = None) -> Dict:
        """
        Determine if seasonal reset should occur.

        Resets every 30 days.

        Args:
            last_reset_date: ISO format date of last reset

        Returns:
            Dict with reset status and dates
        """
        now = datetime.now()

        if last_reset_date is None:
            # First reset
            return {
                "should_reset": True,
                "reason": "First season",
                "current_season_start": now.isoformat(),
                "next_reset_date": (now + timedelta(days=30)).isoformat(),
                "days_until_reset": 30,
            }

        days_since_reset = cls.get_days_since(last_reset_date)

        if days_since_reset >= 30:
            # Time to reset
            return {
                "should_reset": True,
                "reason": f"30-day season complete ({days_since_reset} days elapsed)",
                "current_season_start": now.isoformat(),
                "next_reset_date": (now + timedelta(days=30)).isoformat(),
                "days_until_reset": 0,
            }
        else:
            # Season ongoing
            next_reset = datetime.fromisoformat(last_reset_date) + timedelta(days=30)
            days_until = max(0, (next_reset - now).days)

            return {
                "should_reset": False,
                "reason": "Season ongoing",
                "current_season_start": last_reset_date,
                "next_reset_date": next_reset.isoformat(),
                "days_until_reset": days_until,
            }

    @classmethod
    def apply_seasonal_reset(
        cls, current_season_score: float, lifetime_score: float
    ) -> Dict:
        """
        Apply seasonal reset to scores.

        Adds 50% of current season to lifetime, resets current to 0.

        Args:
            current_season_score: Current season score
            lifetime_score: Accumulated lifetime score

        Returns:
            Dict with new scores after reset
        """
        season_contribution = current_season_score * 0.50

        return {
            "reset_date": datetime.now().isoformat(),
            "old_season_score": current_season_score,
            "new_season_score": 0,
            "season_contribution_to_lifetime": season_contribution,
            "old_lifetime_score": lifetime_score,
            "new_lifetime_score": lifetime_score + season_contribution,
            "message": f"Season reset! +{round(season_contribution, 1)} added to lifetime score.",
        }

    @classmethod
    def apply_time_modifiers(
        cls,
        base_score: float,
        session_date: str,
        last_session_date: Optional[str] = None,
    ) -> Dict:
        """
        Apply all time-based modifiers to a score.

        Args:
            base_score: Base score before modifiers
            session_date: Date of current session
            last_session_date: Date of last session (for decay calculation)

        Returns:
            Dict with adjusted score and multiplier breakdown
        """
        recency = cls.calculate_recency_bonus(session_date)
        recency_mult = recency["multiplier"]

        decay_mult = 1.0
        decay_info = None
        if last_session_date:
            decay_info = cls.calculate_inactivity_decay(last_session_date)
            decay_mult = decay_info["multiplier"]

        # Combine multipliers
        combined_multiplier = recency_mult * decay_mult
        adjusted_score = base_score * combined_multiplier

        result = {
            "base_score": base_score,
            "adjusted_score": round(adjusted_score, 1),
            "combined_multiplier": round(combined_multiplier, 2),
            "recency": recency,
            "decay": decay_info,
            "breakdown": {
                "recency_multiplier": round(recency_mult, 2),
                "decay_multiplier": round(decay_mult, 2),
            },
        }

        return result

    @classmethod
    def get_time_mechanics_summary(cls) -> Dict:
        """Get summary of all time-based mechanics."""
        return {
            "recency_bonus": {
                "same_day": "1.25x (+25%)",
                "1_7_days": "1.15x (+15%)",
                "8_14_days": "1.05x (+5%)",
                "15_plus_days": "1.0x (no bonus)",
            },
            "inactivity_decay": {
                "0_3_days": "1.0x (no decay)",
                "4_7_days": "0.95x (-5%)",
                "8_14_days": "0.85x (-15%)",
                "15_30_days": "0.70x (-30%)",
                "31_plus_days": "0.50x (-50%)",
            },
            "seasonal_reset": {
                "frequency": "Every 30 days",
                "retention": "50% of season score → lifetime score",
                "effect": "Encourages monthly competition, prevents score hoarding",
            },
        }
