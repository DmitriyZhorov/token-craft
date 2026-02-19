"""
Difficulty Modifier System

Adjusts scoring thresholds based on user rank, creating progressive difficulty
that rewards sustained excellence over time. Rank 1 (Cadet) has baseline thresholds,
while Rank 10 (Galactic Legend) requires 50% more efficiency to earn the same points.
"""

from typing import Dict, Optional


class DifficultyModifier:
    """Manages rank-based difficulty progression."""

    # Difficulty tiers by rank - defines baseline token consumption targets
    # Legend baseline (20k) is 43% harder than Cadet baseline (35k)
    RANK_BASELINES = {
        1: {"name": "Cadet", "tokens_per_session": 35000, "multiplier": 1.00},
        2: {"name": "Navigator", "tokens_per_session": 33500, "multiplier": 0.96},
        3: {"name": "Pilot", "tokens_per_session": 32000, "multiplier": 0.91},
        4: {"name": "Explorer", "tokens_per_session": 30000, "multiplier": 0.86},
        5: {"name": "Captain", "tokens_per_session": 28000, "multiplier": 0.80},
        6: {"name": "Commander", "tokens_per_session": 26000, "multiplier": 0.74},
        7: {"name": "Admiral", "tokens_per_session": 24000, "multiplier": 0.69},
        8: {"name": "Commodore", "tokens_per_session": 22000, "multiplier": 0.63},
        9: {"name": "Fleet Admiral", "tokens_per_session": 21000, "multiplier": 0.60},
        10: {"name": "Galactic Legend", "tokens_per_session": 20000, "multiplier": 0.57},
    }

    # Cache hit rate targets by rank (%)
    CACHE_HIT_TARGETS = {
        1: 10,   # Cadet: 10% cache hits expected
        2: 15,   # Navigator: 15%
        3: 20,   # Pilot: 20%
        4: 25,   # Explorer: 25%
        5: 30,   # Captain: 30%
        6: 35,   # Commander: 35%
        7: 40,   # Admiral: 40%
        8: 45,   # Commodore: 45%
        9: 50,   # Fleet Admiral: 50%
        10: 55,  # Legend: 55%
    }

    # Optimization adoption thresholds by rank (%)
    OPTIMIZATION_THRESHOLDS = {
        1: 0.30,   # Cadet: 30% adoption expected
        2: 0.35,
        3: 0.40,
        4: 0.45,
        5: 0.50,   # Captain: 50%
        6: 0.55,
        7: 0.60,   # Admiral: 60%
        8: 0.65,
        9: 0.70,
        10: 0.75,  # Legend: 75%
    }

    # Session focus (message clustering) targets by rank
    # Higher ranks need tighter focus (fewer, more productive messages)
    SESSION_FOCUS_TARGETS = {
        1: (2, 15),     # Cadet: 2-15 messages per session
        2: (2, 14),
        3: (2, 13),
        4: (2, 12),
        5: (2, 11),     # Captain: 2-11 messages
        6: (2, 10),
        7: (2, 9),      # Admiral: 2-9 messages
        8: (2, 8),
        9: (2, 7),
        10: (2, 6),     # Legend: 2-6 messages (extreme focus)
    }

    @classmethod
    def get_difficulty(cls, rank: int) -> Dict:
        """
        Get difficulty modifiers for a specific rank.

        Args:
            rank: User's current rank (1-10)

        Returns:
            Dict with difficulty parameters for this rank
        """
        # Clamp rank to valid range
        rank = max(1, min(10, rank))

        baseline_info = cls.RANK_BASELINES.get(rank, cls.RANK_BASELINES[1])

        return {
            "rank": rank,
            "rank_name": baseline_info["name"],
            "tokens_per_session": baseline_info["tokens_per_session"],
            "multiplier": baseline_info["multiplier"],
            "cache_hit_target": cls.CACHE_HIT_TARGETS.get(rank, 10),
            "optimization_threshold": cls.OPTIMIZATION_THRESHOLDS.get(rank, 0.30),
            "session_focus_target": cls.SESSION_FOCUS_TARGETS.get(rank, (2, 15)),
        }

    @classmethod
    def apply_token_efficiency_difficulty(
        cls, score: float, user_ratio: float, rank: int
    ) -> float:
        """
        Apply difficulty-based adjustment to token efficiency score.

        For higher ranks, tighten the scoring bands so the same ratio earns fewer points.
        E.g., 1.5x baseline = 200 pts at Cadet, but only 150 pts at Admiral.

        Args:
            score: Current score
            user_ratio: User's efficiency ratio (avg_tokens / baseline_tokens)
            rank: Current rank

        Returns:
            Adjusted score
        """
        # Get rank-specific baseline
        difficulty = cls.get_difficulty(rank)
        multiplier = difficulty["multiplier"]

        # Higher ranks see tighter scoring bands
        # At Legend (0.57x), the curve is more aggressive
        if user_ratio <= 1.0:
            # Already at or below baseline - no penalty
            return score
        elif user_ratio <= 1.5:
            # Slight overage - apply difficulty modifier
            return score * multiplier
        else:
            # More significant overage - apply stronger modifier
            return score * (multiplier ** 1.5)

    @classmethod
    def apply_optimization_difficulty(
        cls, score: float, adoption_rate: float, rank: int
    ) -> float:
        """
        Apply difficulty-based adjustment to optimization adoption score.

        Higher ranks need higher adoption rates to earn full points.

        Args:
            score: Current score
            adoption_rate: User's optimization adoption rate (0-1)
            rank: Current rank

        Returns:
            Adjusted score
        """
        threshold = cls.OPTIMIZATION_THRESHOLDS.get(rank, 0.30)

        # If above threshold for this rank, full points
        if adoption_rate >= threshold:
            return score

        # Below threshold, reduce proportionally
        return score * (adoption_rate / threshold)

    @classmethod
    def get_difficulty_comparison(cls) -> Dict:
        """
        Get comparison of difficulty across all ranks.

        Useful for showing user progression curve.

        Returns:
            Dict with difficulty comparison data
        """
        comparison = {}

        for rank in range(1, 11):
            difficulty = cls.get_difficulty(rank)
            baseline_info = cls.RANK_BASELINES[rank]

            comparison[rank] = {
                "rank_name": baseline_info["name"],
                "tokens_baseline": baseline_info["tokens_per_session"],
                "difficulty_increase_pct": round((1 - difficulty["multiplier"]) * 100, 1),
                "cache_target": difficulty["cache_hit_target"],
                "optimization_target": round(difficulty["optimization_threshold"] * 100, 1),
            }

        return comparison
