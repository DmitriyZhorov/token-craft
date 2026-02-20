"""
Achievement System

Gamification engine tracking 34 achievements across 8 categories:
- Progression (5): Rank milestones
- Excellence (5): Category mastery
- Streaks (3): Consecutive improvement rewards
- Combos (3): Multi-category excellence
- Exploration (4): Session volume milestones
- Special (9): Unique challenges and best practices
- Sustainability (5): Healthy optimization patterns
- Adaptability (New): Multi-tool and multi-model efficiency
"""

from typing import Any, Dict, List, Optional
from datetime import datetime


class Achievement:
    """Individual achievement definition."""

    def __init__(
        self,
        achievement_id: str,
        name: str,
        category: str,
        description: str,
        requirement: str,
        points: int,
        badge_icon: str,
    ):
        """Initialize achievement."""
        self.achievement_id = achievement_id
        self.name = name
        self.category = category
        self.description = description
        self.requirement = requirement
        self.points = points
        self.badge_icon = badge_icon

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "id": self.achievement_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "requirement": self.requirement,
            "points": self.points,
            "icon": self.badge_icon,
        }


class AchievementEngine:
    """Manages achievement tracking and unlocking."""

    # All available achievements (as Achievement objects)
    _ACHIEVEMENT_OBJECTS = [
        # Progression (5) - Rank milestones
        Achievement(
            "rank_cadet",
            "Cadet",
            "Progression",
            "Start your journey",
            "Reach Cadet rank",
            20,
            "🎓",
        ),
        Achievement(
            "rank_navigator",
            "Navigator",
            "Progression",
            "First journey complete",
            "Reach Navigator rank (100 pts)",
            50,
            "🧭",
        ),
        Achievement(
            "rank_captain",
            "Captain",
            "Progression",
            "Leading missions",
            "Reach Captain rank (550 pts)",
            100,
            "👨‍✈️",
        ),
        Achievement(
            "rank_admiral",
            "Admiral",
            "Progression",
            "Fleet command achieved",
            "Reach Admiral rank (1100 pts)",
            150,
            "🎖️",
        ),
        Achievement(
            "rank_legend",
            "Galactic Legend",
            "Progression",
            "Explored uncharted territories",
            "Reach Galactic Legend rank (2300 pts)",
            200,
            "🌌",
        ),
        # Excellence (5) - Category mastery
        Achievement(
            "excellence_efficiency",
            "Efficiency Expert",
            "Excellence",
            "Master token optimization",
            "80%+ on Token Efficiency (200+ pts)",
            75,
            "⚡",
        ),
        Achievement(
            "excellence_adoption",
            "Optimization Master",
            "Excellence",
            "Best practices virtuoso",
            "80%+ on Optimization Adoption",
            75,
            "🎯",
        ),
        Achievement(
            "excellence_cache",
            "Cache Champion",
            "Excellence",
            "Cache hit expert",
            "80%+ on Cache Effectiveness",
            75,
            "💾",
        ),
        Achievement(
            "excellence_waste",
            "Zero Waste Pioneer",
            "Excellence",
            "Minimal token waste",
            "80%+ on Waste Awareness",
            75,
            "♻️",
        ),
        Achievement(
            "excellence_cost",
            "Cost Efficiency Master",
            "Excellence",
            "Budget optimization pro",
            "80%+ on Cost Efficiency",
            75,
            "💰",
        ),
        # Streaks (3) - Consecutive improvement
        Achievement(
            "streak_5",
            "On Fire",
            "Streaks",
            "5-session improvement streak",
            "Achieve 5 consecutive improving sessions",
            100,
            "🔥",
        ),
        Achievement(
            "streak_10",
            "Unstoppable",
            "Streaks",
            "10-session improvement streak",
            "Achieve 10 consecutive improving sessions",
            150,
            "💪",
        ),
        Achievement(
            "streak_20",
            "Legendary Consistency",
            "Streaks",
            "20-session improvement streak",
            "Achieve 20 consecutive improving sessions",
            200,
            "⭐",
        ),
        # Combos (3) - Multi-category excellence
        Achievement(
            "combo_focused",
            "Focused Practitioner",
            "Combos",
            "Excel in 2+ categories",
            "2 categories at 80%+",
            50,
            "🎪",
        ),
        Achievement(
            "combo_wellrounded",
            "Well-Rounded Optimizer",
            "Combos",
            "Excel in 3+ categories",
            "3 categories at 80%+",
            100,
            "⚖️",
        ),
        Achievement(
            "combo_mastery",
            "MASTERY: All Categories",
            "Combos",
            "Perfect mastery across all categories",
            "5+ categories at 80%+",
            200,
            "👑",
        ),
        # Exploration (4) - Session milestones
        Achievement(
            "explore_10",
            "First Flight",
            "Exploration",
            "10 sessions completed",
            "Reach 10 sessions",
            25,
            "🚀",
        ),
        Achievement(
            "explore_50",
            "Experienced Explorer",
            "Exploration",
            "50 sessions completed",
            "Reach 50 sessions",
            75,
            "🛸",
        ),
        Achievement(
            "explore_100",
            "Century Club",
            "Exploration",
            "100 sessions completed",
            "Reach 100 sessions",
            150,
            "🌠",
        ),
        Achievement(
            "explore_250",
            "Veteran Navigator",
            "Exploration",
            "250 sessions completed",
            "Reach 250 sessions",
            200,
            "🪐",
        ),
        # Special (5) - Unique challenges
        Achievement(
            "special_zero_waste",
            "Zero Waste Day",
            "Special",
            "Optimal session with <10% waste",
            "Single session with <10% waste",
            60,
            "🌿",
        ),
        Achievement(
            "special_consistency",
            "Consistency King",
            "Special",
            "Maintain 80%+ efficiency for 30 days",
            "30 consecutive days >80% efficiency",
            150,
            "📈",
        ),
        Achievement(
            "special_speedrun",
            "Speed Demon",
            "Special",
            "Complete 5 sessions in one day",
            "5 sessions in 24 hours with improvements",
            100,
            "🏎️",
        ),
        Achievement(
            "special_comeback",
            "Comeback Kid",
            "Special",
            "Recover from 10+ pt loss",
            "Recover from degraded score (+10 pts improvement)",
            80,
            "📍",
        ),
        Achievement(
            "special_peak",
            "Peak Performance",
            "Special",
            "Achieve personal best score",
            "Set new personal high score",
            120,
            "🏔️",
        ),
        # Sustainability (5) - Healthy optimization patterns
        Achievement(
            "sustainability_paced",
            "Steady Climber",
            "Sustainability",
            "Consistent, sustainable growth pattern",
            "Reach 500 pts with <5% month-over-month volatility",
            100,
            "🌱",
        ),
        Achievement(
            "sustainability_balanced",
            "Balanced Optimizer",
            "Sustainability",
            "Avoid over-optimizing single categories",
            "No single category >90% for 60+ days (prevent tunnel vision)",
            75,
            "⚖️",
        ),
        Achievement(
            "sustainability_rest",
            "Rest is Productive",
            "Sustainability",
            "Take healthy breaks without streak penalties",
            "Maintain 80%+ categories after 7+ day break",
            80,
            "😴",
        ),
        Achievement(
            "sustainability_longterm",
            "Marathon Mindset",
            "Sustainability",
            "Sustained 6-month engagement at steady pace",
            "180+ days of consistent usage (no burnout dips)",
            150,
            "🏃",
        ),
        Achievement(
            "sustainability_wisdom",
            "Wisdom Over Grind",
            "Sustainability",
            "Prioritize quality over quantity",
            "Achieve 75%+ efficiency with 20% fewer sessions than baseline",
            125,
            "🧠",
        ),
        # Special (4 more) - Best practices from industry standards
        Achievement(
            "special_concise",
            "Concise Communicator",
            "Special",
            "Optimize response length without sacrificing clarity",
            "Maintain <20% bloat in average response (vs baseline)",
            75,
            "📏",
        ),
        Achievement(
            "special_flawless",
            "Flawless Execution",
            "Special",
            "Complete sessions without corrections or reworks",
            "5 consecutive sessions with zero re-runs or corrections",
            100,
            "✅",
        ),
        Achievement(
            "special_model_maestro",
            "Model Maestro",
            "Special",
            "Effectively use multiple models for different tasks",
            "Use 3+ different models with 75%+ efficiency across all",
            100,
            "🎛️",
        ),
        Achievement(
            "special_batch_master",
            "Batch Master",
            "Special",
            "Process multiple related tasks efficiently in sequence",
            "Complete 3+ related tasks in single session with 20%+ efficiency gain",
            75,
            "📦",
        ),
    ]

    # Build ACHIEVEMENTS as list of dicts for compatibility with tests
    ACHIEVEMENTS = [
        {
            "id": ach.achievement_id,
            "title": ach.name,
            "description": ach.description,
            "category": ach.category.lower(),
            "threshold": ach.requirement,
            "points": ach.points,
            "icon": ach.badge_icon,
            "requirement": ach.requirement,
        }
        for ach in _ACHIEVEMENT_OBJECTS
    ]

    @classmethod
    def _get_achievements_as_dicts(cls) -> List[Dict]:
        """Convert Achievement objects to dicts with expected test field names."""
        achievements = []
        for ach in cls._ACHIEVEMENT_OBJECTS:
            achievements.append(
                {
                    "id": ach.achievement_id,
                    "title": ach.name,
                    "description": ach.description,
                    "category": ach.category.lower(),
                    "threshold": ach.requirement,
                    "points": ach.points,
                    "icon": ach.badge_icon,
                    "requirement": ach.requirement,
                }
            )
        return achievements

    def __init__(
        self, user_profile: Optional[Dict] = None, profile: Optional[Dict] = None
    ):
        """Initialize achievement engine."""
        # Accept both 'user_profile' and 'profile' for backwards compatibility
        self.user_profile = user_profile or profile or {}
        self.unlocked_achievements = self._load_unlocked()

    def _load_unlocked(self) -> List[str]:
        """Load unlocked achievements from profile."""
        if "achievements" in self.user_profile:
            return self.user_profile["achievements"]
        return []

    def get_achievement_by_id(self, achievement_id: str) -> Optional[Achievement]:
        """Get achievement definition by ID."""
        # Try exact match first
        for achievement in self._ACHIEVEMENT_OBJECTS:
            if achievement.achievement_id == achievement_id:
                return achievement

        # Try alternative ID formats (for backwards compatibility)
        # "cadet_ranked" -> "rank_cadet"
        if "_ranked" in achievement_id:
            alt_id_v2 = "rank_" + achievement_id.split("_")[0]
            for achievement in self._ACHIEVEMENT_OBJECTS:
                if achievement.achievement_id == alt_id_v2:
                    return achievement

        return None

    def unlock_achievement(
        self, achievement_id: str, timestamp: Optional[str] = None
    ) -> Dict:
        """
        Unlock an achievement.

        Args:
            achievement_id: Achievement ID to unlock
            timestamp: When achievement was unlocked (ISO format)

        Returns:
            Dict with unlock result
        """
        if achievement_id in self.unlocked_achievements:
            return {"status": "already_unlocked", "achievement_id": achievement_id}

        achievement = self.get_achievement_by_id(achievement_id)
        if not achievement:
            return {"status": "invalid_achievement"}

        self.unlocked_achievements.append(achievement_id)

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        return {
            "status": "unlocked",
            "unlocked": True,
            "achievement_id": achievement_id,
            "name": achievement.name,
            "category": achievement.category,
            "points": achievement.points,
            "timestamp": timestamp,
        }

    def check_progression_achievements(
        self,
        rank: Optional[int] = None,
        score: Optional[int] = None,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """
        Check and unlock progression achievements based on rank/score.

        Args:
            rank: Current rank (1-10) or None if user_data dict is provided
            score: Current score or None if user_data dict is provided
            user_data: Optional dict with "current_rank" and "current_score" keys

        Returns:
            List of newly unlocked achievements
        """
        # Handle dict parameter format for backwards compatibility
        if user_data is not None:
            # user_data is first positional arg if called with dict
            from .rank_system import SpaceRankSystem

            rank_obj = SpaceRankSystem.get_rank_by_name(
                user_data.get("current_rank", "Cadet")
            )
            rank = rank_obj.get("number", 1) if rank_obj else 1
            score = user_data.get("current_score", 0)
        elif isinstance(rank, dict):
            # Handle case where first arg is a dict (called as check_progression_achievements(dict_arg))
            from .rank_system import SpaceRankSystem

            rank_obj = SpaceRankSystem.get_rank_by_name(
                rank.get("current_rank", "Cadet")
            )
            rank_int = rank_obj.get("number", 1) if rank_obj else 1
            score = rank.get("current_score", 0)
            rank = rank_int

        # Ensure rank and score have default values if None
        rank = rank if rank is not None else 1
        score = score if score is not None else 0

        unlocked = []

        # Cadet rank
        if rank >= 1 and "rank_cadet" not in self.unlocked_achievements:
            result = self.unlock_achievement("rank_cadet")
            if result["status"] == "unlocked":
                unlocked.append(result)

        # Navigator rank (100 pts)
        if rank >= 2 and "rank_navigator" not in self.unlocked_achievements:
            result = self.unlock_achievement("rank_navigator")
            if result["status"] == "unlocked":
                unlocked.append(result)

        # Captain rank (550 pts)
        if rank >= 5 and "rank_captain" not in self.unlocked_achievements:
            result = self.unlock_achievement("rank_captain")
            if result["status"] == "unlocked":
                unlocked.append(result)

        # Admiral rank (1100 pts)
        if rank >= 7 and "rank_admiral" not in self.unlocked_achievements:
            result = self.unlock_achievement("rank_admiral")
            if result["status"] == "unlocked":
                unlocked.append(result)

        # Legend rank (2300 pts)
        if rank >= 10 and "rank_legend" not in self.unlocked_achievements:
            result = self.unlock_achievement("rank_legend")
            if result["status"] == "unlocked":
                unlocked.append(result)

        return unlocked

    def check_excellence_achievements(
        self, category_scores: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Check and unlock excellence achievements.

        Args:
            category_scores: Dict of {category: {"score": X, "max_score": Y}}

        Returns:
            List of newly unlocked achievements
        """
        unlocked = []
        threshold = 0.80

        excellence_map = {
            "token_efficiency": "excellence_efficiency",
            "optimization_adoption": "excellence_adoption",
            "cache_effectiveness": "excellence_cache",
            "waste_awareness": "excellence_waste",
            "cost_efficiency": "excellence_cost",
        }

        for category, achievement_id in excellence_map.items():
            if (
                category in category_scores
                and achievement_id not in self.unlocked_achievements
            ):
                score = category_scores[category].get("score", 0)
                max_score = category_scores[category].get("max_score", 1)
                if max_score > 0 and (score / max_score) >= threshold:
                    result = self.unlock_achievement(achievement_id)
                    if result["status"] == "unlocked":
                        unlocked.append(result)

        return unlocked

    def get_all_achievements(self) -> List[Dict]:
        """Get all achievements with unlock status."""
        achievements = []
        for achievement in self._ACHIEVEMENT_OBJECTS:
            achievement_dict = achievement.to_dict()
            achievement_dict["unlocked"] = (
                achievement.achievement_id in self.unlocked_achievements
            )
            achievements.append(achievement_dict)
        return achievements

    def get_achievement_stats(self) -> Dict:
        """Get achievement statistics."""
        unlocked_count = len(self.unlocked_achievements)
        total_count = len(self._ACHIEVEMENT_OBJECTS)
        total_points = sum(
            ach.points
            for ach in self._ACHIEVEMENT_OBJECTS
            if ach.achievement_id in self.unlocked_achievements
        )

        return {
            "unlocked_count": unlocked_count,
            "total_count": total_count,
            "completion_pct": round((unlocked_count / total_count) * 100, 1),
            "total_points_earned": total_points,
            "total_points_possible": sum(
                ach.points for ach in self._ACHIEVEMENT_OBJECTS
            ),
        }

    def to_dict(self) -> Dict:
        """Serialize to dict for storage."""
        return {"achievements": self.unlocked_achievements}
