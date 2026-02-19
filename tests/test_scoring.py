"""
Unit tests for Token-Craft v3.0 scoring engine.

Tests cover:
- Removed duplicate Self-Sufficiency scoring
- Smooth Token Efficiency scale (logarithmic)
- Linear Cache Effectiveness scale
- Difficulty modifier by rank
- Streak & Combo bonus systems
- Achievement engine
- Time-based mechanics (recency, decay, seasonal)
- Migration from v2.0 to v3.0
- Verify max achievable score = 2300 pts
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from token_craft.scoring_engine import TokenCraftScorer
from token_craft.rank_system import SpaceRankSystem
from token_craft.difficulty_modifier import DifficultyModifier
from token_craft.streak_system import StreakSystem, ComboBonus
from token_craft.achievement_engine import AchievementEngine
from token_craft.time_based_mechanics import TimeBasedMechanics
from token_craft.migration_engine import MigrationEngine
from token_craft.user_profile import UserProfile


class TestSpaceRankSystem(unittest.TestCase):
    """Test v3.0 rank system - 10 ranks with exponential progression."""

    def test_all_10_ranks_exist(self):
        """Test all 10 ranks exist in correct order."""
        all_ranks = SpaceRankSystem.get_all_ranks()
        self.assertEqual(len(all_ranks), 10)
        expected_names = [
            "Cadet", "Navigator", "Pilot", "Explorer", "Captain",
            "Commander", "Admiral", "Commodore", "Fleet Admiral", "Galactic Legend"
        ]
        actual_names = [r["name"] for r in all_ranks]
        self.assertEqual(actual_names, expected_names)

    def test_get_rank_cadet(self):
        """Test Cadet rank (0-99 pts)."""
        rank = SpaceRankSystem.get_rank(50)
        self.assertEqual(rank["name"], "Cadet")
        self.assertEqual(rank["min"], 0)
        self.assertEqual(rank["max"], 99)

    def test_get_rank_navigator(self):
        """Test Navigator rank (100-199 pts)."""
        rank = SpaceRankSystem.get_rank(150)
        self.assertEqual(rank["name"], "Navigator")

    def test_get_rank_pilot(self):
        """Test Pilot rank (200-349 pts)."""
        rank = SpaceRankSystem.get_rank(250)
        self.assertEqual(rank["name"], "Pilot")

    def test_get_rank_explorer(self):
        """Test Explorer rank (350-549 pts)."""
        rank = SpaceRankSystem.get_rank(450)
        self.assertEqual(rank["name"], "Explorer")

    def test_get_rank_captain(self):
        """Test Captain rank (550-799 pts)."""
        rank = SpaceRankSystem.get_rank(650)
        self.assertEqual(rank["name"], "Captain")

    def test_get_rank_commander(self):
        """Test Commander rank (800-1099 pts)."""
        rank = SpaceRankSystem.get_rank(900)
        self.assertEqual(rank["name"], "Commander")

    def test_get_rank_admiral(self):
        """Test Admiral rank (1100-1449 pts)."""
        rank = SpaceRankSystem.get_rank(1200)
        self.assertEqual(rank["name"], "Admiral")

    def test_get_rank_commodore(self):
        """Test Commodore rank (1450-1849 pts)."""
        rank = SpaceRankSystem.get_rank(1650)
        self.assertEqual(rank["name"], "Commodore")

    def test_get_rank_fleet_admiral(self):
        """Test Fleet Admiral rank (1850-2299 pts)."""
        rank = SpaceRankSystem.get_rank(2000)
        self.assertEqual(rank["name"], "Fleet Admiral")

    def test_get_rank_legend(self):
        """Test Galactic Legend rank (2300+ pts)."""
        rank = SpaceRankSystem.get_rank(2300)
        self.assertEqual(rank["name"], "Galactic Legend")
        rank = SpaceRankSystem.get_rank(5000)
        self.assertEqual(rank["name"], "Galactic Legend")

    def test_rank_progress_percentage(self):
        """Test progress percentage within rank."""
        rank = SpaceRankSystem.get_rank(150)  # Navigator
        # 150 is at min (100), so 0% progress
        self.assertGreaterEqual(rank["progress_pct"], 0)
        self.assertLessEqual(rank["progress_pct"], 100)

    def test_get_next_rank(self):
        """Test next rank calculation."""
        next_rank = SpaceRankSystem.get_next_rank(150)
        self.assertEqual(next_rank["name"], "Pilot")
        self.assertEqual(next_rank["points_needed"], 50)

    def test_get_next_rank_from_pilot(self):
        """Test next rank from Pilot."""
        next_rank = SpaceRankSystem.get_next_rank(250)
        self.assertEqual(next_rank["name"], "Explorer")
        self.assertEqual(next_rank["points_needed"], 100)

    def test_get_next_rank_max(self):
        """Test next rank at max level."""
        next_rank = SpaceRankSystem.get_next_rank(2300)
        self.assertIsNone(next_rank)

    def test_progress_bar(self):
        """Test progress bar generation."""
        bar = SpaceRankSystem.get_progress_bar(100, width=10)
        self.assertEqual(len(bar), 10)
        self.assertIn("█", bar)
        self.assertIn("░", bar)

    def test_rank_level(self):
        """Test numeric rank level (1-10)."""
        self.assertEqual(SpaceRankSystem.calculate_rank_level(50), 1)   # Cadet
        self.assertEqual(SpaceRankSystem.calculate_rank_level(150), 2)  # Navigator
        self.assertEqual(SpaceRankSystem.calculate_rank_level(250), 3)  # Pilot
        self.assertEqual(SpaceRankSystem.calculate_rank_level(450), 4)  # Explorer
        self.assertEqual(SpaceRankSystem.calculate_rank_level(650), 5)  # Captain
        self.assertEqual(SpaceRankSystem.calculate_rank_level(900), 6)  # Commander
        self.assertEqual(SpaceRankSystem.calculate_rank_level(1200), 7) # Admiral
        self.assertEqual(SpaceRankSystem.calculate_rank_level(1650), 8) # Commodore
        self.assertEqual(SpaceRankSystem.calculate_rank_level(2000), 9) # Fleet Admiral
        self.assertEqual(SpaceRankSystem.calculate_rank_level(2300), 10) # Galactic Legend

    def test_get_rank_by_name(self):
        """Test getting rank by name."""
        rank = SpaceRankSystem.get_rank_by_name("Captain")
        self.assertIsNotNone(rank)
        self.assertEqual(rank["name"], "Captain")
        self.assertEqual(rank["min"], 550)
        self.assertEqual(rank["max"], 799)


class TestTokenCraftScorerV3(unittest.TestCase):
    """Test v3.0 scoring engine with new features."""

    def setUp(self):
        """Set up test data."""
        self.history_data = [
            {
                "sessionId": "session1",
                "project": "project_a",
                "message": "test message",
                "timestamp": "2026-02-12T10:00:00Z"
            },
            {
                "sessionId": "session1",
                "project": "project_a",
                "message": "another message with more tokens",
                "timestamp": "2026-02-12T10:05:00Z"
            },
            {
                "sessionId": "session2",
                "project": "project_b",
                "message": "different project session",
                "timestamp": "2026-02-12T15:00:00Z"
            },
        ]

        self.stats_data = {
            "models": {
                "claude-sonnet-4.5": {
                    "inputTokens": 50000,
                    "outputTokens": 30000
                }
            }
        }

        # Create sample user profile for v3.0
        self.user_profile_v3 = {
            "version": "3.0",
            "user_email": "user@example.com",
            "current_rank": "Cadet",
            "current_score": 0,
            "total_sessions": 1,
            "total_tokens": 80000,
            "scores": {
                "token_efficiency": 0,
                "optimization_adoption": 0,
                "improvement_trend": 0,
                "best_practices": 0,
                "cache_effectiveness": 0,
                "tool_efficiency": 0,
                "session_focus": 0,
                "cost_efficiency": 0,
                "learning_growth": 0,
                "waste_awareness": 0,
            },
            "streak_info": {
                "current": {"length": 0, "start_date": None, "last_session_date": None},
                "best": {"length": 0, "start_date": None, "last_session_date": None}
            },
            "seasonal_info": {
                "current_season_score": 0,
                "lifetime_score": 0,
                "current_season_start": datetime.now().isoformat(),
                "last_reset": None,
            },
            "achievements": [],
        }

    def test_scorer_initialization_v3(self):
        """Test scorer initialization with v3.0."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        self.assertIsNotNone(scorer)
        self.assertEqual(scorer.total_sessions, 2)
        self.assertEqual(scorer.total_tokens, 80000)

    def test_no_self_sufficiency_in_weights(self):
        """Test that self_sufficiency is removed from v3.0 weights."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        self.assertNotIn("self_sufficiency", scorer.weights)

    def test_waste_awareness_category_exists(self):
        """Test that waste_awareness is a new v3.0 category."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        self.assertIn("waste_awareness", scorer.weights)

    def test_smooth_token_efficiency_scale(self):
        """Test smooth logarithmic scale for token efficiency (not tiers)."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_token_efficiency_score()

        # Should be smooth, not discrete tiers
        self.assertIn("score", score_data)
        self.assertIn("max_score", score_data)
        self.assertEqual(score_data["max_score"], 250)  # v3.0 value (was 300)

        # Score should be between 0 and max_score
        self.assertGreaterEqual(score_data["score"], 0)
        self.assertLessEqual(score_data["score"], 250)

    def test_linear_cache_effectiveness_scale(self):
        """Test linear scale for cache effectiveness."""
        # Create scorer with cache data
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_cache_effectiveness_score()

        self.assertIn("score", score_data)
        self.assertEqual(score_data["max_score"], 75)  # v3.0 value (was 100)

        # Should be continuous, not discrete
        self.assertGreaterEqual(score_data["score"], 0)
        self.assertLessEqual(score_data["score"], 75)

    def test_learning_growth_no_warmup_bonus(self):
        """Test learning growth removes warm-up bonus."""
        # With <10 sessions, should not get auto 25pts
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_learning_growth_score()

        self.assertIn("score", score_data)
        self.assertEqual(score_data["max_score"], 75)

        # Should explain that warm-up bonus is gone
        self.assertIn("details", score_data)

    def test_total_score_v3_max(self):
        """Test total score max is 2300 (not 1450)."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_total_score()

        self.assertIn("total_score", score_data)
        self.assertIn("max_achievable", score_data)

        # Max achievable should be around 2300 (includes bonuses)
        self.assertGreaterEqual(score_data["max_achievable"], 2300)

        # Should have version marker
        self.assertEqual(score_data.get("version"), "3.0")

    def test_breakdown_has_10_categories(self):
        """Test breakdown contains all 10 v3.0 categories."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=1, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_total_score()

        breakdown = score_data.get("breakdown", {})
        expected_categories = [
            "token_efficiency",
            "optimization_adoption",
            "improvement_trend",
            "waste_awareness",
            "best_practices",
            "cache_effectiveness",
            "tool_efficiency",
            "session_focus",
            "cost_efficiency",
            "learning_growth",
        ]

        for cat in expected_categories:
            self.assertIn(cat, breakdown, f"Missing category: {cat}")

        # self_sufficiency should NOT be in breakdown
        self.assertNotIn("self_sufficiency", breakdown)


class TestDifficultyModifier(unittest.TestCase):
    """Test rank-based difficulty scaling."""

    def test_difficulty_cadet(self):
        """Test Cadet (rank 1) difficulty."""
        diff = DifficultyModifier.get_difficulty(rank=1)
        self.assertEqual(diff["rank"], 1)
        self.assertEqual(diff["rank_name"], "Cadet")
        self.assertIn("token_efficiency_baseline", diff)

    def test_difficulty_captain(self):
        """Test Captain (rank 5) difficulty."""
        diff = DifficultyModifier.get_difficulty(rank=5)
        self.assertEqual(diff["rank"], 5)
        self.assertEqual(diff["rank_name"], "Captain")

    def test_difficulty_legend(self):
        """Test Galactic Legend (rank 10) difficulty."""
        diff = DifficultyModifier.get_difficulty(rank=10)
        self.assertEqual(diff["rank"], 10)
        self.assertEqual(diff["rank_name"], "Galactic Legend")

    def test_difficulty_progressively_harder(self):
        """Test difficulty increases with rank."""
        cadet_diff = DifficultyModifier.get_difficulty(rank=1)
        legend_diff = DifficultyModifier.get_difficulty(rank=10)

        cadet_baseline = cadet_diff["token_efficiency_baseline"]
        legend_baseline = legend_diff["token_efficiency_baseline"]

        # Legend should have lower baseline (harder)
        self.assertLess(legend_baseline, cadet_baseline)

    def test_token_efficiency_difficulty_applied(self):
        """Test applying difficulty to token efficiency."""
        score_cadet = DifficultyModifier.apply_token_efficiency_difficulty(
            base_score=200, rank=1
        )
        score_legend = DifficultyModifier.apply_token_efficiency_difficulty(
            base_score=200, rank=10
        )

        # Legend should get lower adjusted score for same base
        self.assertLess(score_legend, score_cadet)

    def test_all_10_ranks_have_difficulty(self):
        """Test all 10 ranks have difficulty definitions."""
        for rank in range(1, 11):
            diff = DifficultyModifier.get_difficulty(rank=rank)
            self.assertIsNotNone(diff)
            self.assertEqual(diff["rank"], rank)


class TestStreakSystem(unittest.TestCase):
    """Test streak multiplier and bonus points."""

    def test_streak_progression_table(self):
        """Test streak progression increases multiplier."""
        streak_data = StreakSystem.STREAK_PROGRESSION
        self.assertEqual(len(streak_data), 6)

        # Multiplier should increase with streak
        for i in range(len(streak_data) - 1):
            curr_mult = streak_data[i]["multiplier"]
            next_mult = streak_data[i + 1]["multiplier"]
            self.assertLess(curr_mult, next_mult)

    def test_streak_bonus_points_increase(self):
        """Test bonus points increase with streak."""
        streak_data = StreakSystem.STREAK_PROGRESSION
        bonus_points = [s["bonus_points"] for s in streak_data]

        # Should be monotonically increasing
        for i in range(len(bonus_points) - 1):
            self.assertLessEqual(bonus_points[i], bonus_points[i + 1])

    def test_max_streak_multiplier(self):
        """Test max streak multiplier is 1.25x."""
        max_streak = StreakSystem.STREAK_PROGRESSION[-1]
        self.assertEqual(max_streak["multiplier"], 1.25)

    def test_max_streak_bonus_points(self):
        """Test max streak bonus is 50 points."""
        max_streak = StreakSystem.STREAK_PROGRESSION[-1]
        self.assertEqual(max_streak["bonus_points"], 50)

    def test_session_1_is_baseline(self):
        """Test first session has 1.0x multiplier, no bonus."""
        first_streak = StreakSystem.STREAK_PROGRESSION[0]
        self.assertEqual(first_streak["sessions"], 1)
        self.assertEqual(first_streak["multiplier"], 1.0)
        self.assertEqual(first_streak["bonus_points"], 0)


class TestComboBonus(unittest.TestCase):
    """Test multi-category excellence bonus."""

    def test_combo_tiers_exist(self):
        """Test combo bonus tiers are defined."""
        tiers = ComboBonus.COMBO_TIERS
        self.assertGreater(len(tiers), 0)

    def test_combo_bonus_increases_with_categories(self):
        """Test bonus points increase with more categories."""
        bonus_points = [t["bonus_points"] for t in ComboBonus.COMBO_TIERS]

        for i in range(len(bonus_points) - 1):
            self.assertLessEqual(bonus_points[i], bonus_points[i + 1])

    def test_max_combo_bonus(self):
        """Test max combo bonus (5+ categories at 80%)."""
        max_tier = ComboBonus.COMBO_TIERS[-1]
        self.assertEqual(max_tier["categories_min"], 5)
        self.assertEqual(max_tier["bonus_points"], 150)

    def test_combo_calculation(self):
        """Test calculating combo bonus from categories."""
        # Score data with 3 categories at 80%+
        scores = {
            "token_efficiency": {"score": 200, "max_score": 250},  # 80%
            "optimization_adoption": {"score": 320, "max_score": 400},  # 80%
            "improvement_trend": {"score": 100, "max_score": 125},  # 80%
            "best_practices": {"score": 30, "max_score": 50},  # 60%
            "cache_effectiveness": {"score": 40, "max_score": 75},  # 53%
        }

        combo_bonus = ComboBonus.calculate_combo_bonus(scores)
        self.assertGreater(combo_bonus, 0)


class TestAchievementEngine(unittest.TestCase):
    """Test 25+ achievement system."""

    def test_achievements_list_not_empty(self):
        """Test achievements list contains 25+ achievements."""
        achievements = AchievementEngine.ACHIEVEMENTS
        self.assertGreaterEqual(len(achievements), 25)

    def test_achievements_have_required_fields(self):
        """Test each achievement has required fields."""
        for ach in AchievementEngine.ACHIEVEMENTS:
            self.assertIn("id", ach)
            self.assertIn("title", ach)
            self.assertIn("description", ach)
            self.assertIn("category", ach)
            self.assertIn("threshold", ach)

    def test_achievement_categories(self):
        """Test achievements cover multiple categories."""
        achievements = AchievementEngine.ACHIEVEMENTS
        categories = set(a["category"] for a in achievements)

        expected_categories = ["progression", "excellence", "streaks", "combos", "exploration", "special"]
        for cat in expected_categories:
            self.assertIn(cat, categories)

    def test_unlock_achievement(self):
        """Test unlocking achievement."""
        engine = AchievementEngine(profile=None)
        result = engine.unlock_achievement("cadet_ranked")

        self.assertIsNotNone(result)
        self.assertTrue(result.get("unlocked", False))

    def test_check_progression_achievements(self):
        """Test checking progression achievement unlocks."""
        engine = AchievementEngine(profile=None)
        user_data = {"current_rank": "Captain", "current_score": 650}

        unlocked = engine.check_progression_achievements(user_data)
        # Should have unlocked some progression achievements
        self.assertIsInstance(unlocked, list)


class TestTimeBasedMechanics(unittest.TestCase):
    """Test recency bonus, inactivity decay, seasonal reset."""

    def test_recency_bonus_same_day(self):
        """Test same-day recency bonus is 1.25x."""
        now = datetime.now().isoformat()
        recency = TimeBasedMechanics.calculate_recency_bonus(now)

        self.assertEqual(recency["multiplier"], 1.25)
        self.assertEqual(recency["bonus_pct"], 25)
        self.assertEqual(recency["days_ago"], 0)

    def test_recency_bonus_7_days(self):
        """Test 7-day recency bonus is 1.15x."""
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recency = TimeBasedMechanics.calculate_recency_bonus(seven_days_ago)

        self.assertEqual(recency["multiplier"], 1.15)
        self.assertEqual(recency["bonus_pct"], 15)

    def test_recency_bonus_14_days(self):
        """Test 14-day recency bonus is 1.05x."""
        fourteen_days_ago = (datetime.now() - timedelta(days=14)).isoformat()
        recency = TimeBasedMechanics.calculate_recency_bonus(fourteen_days_ago)

        self.assertEqual(recency["multiplier"], 1.05)
        self.assertEqual(recency["bonus_pct"], 5)

    def test_recency_bonus_15_plus_days(self):
        """Test 15+ day recency has no bonus (1.0x)."""
        old_date = (datetime.now() - timedelta(days=20)).isoformat()
        recency = TimeBasedMechanics.calculate_recency_bonus(old_date)

        self.assertEqual(recency["multiplier"], 1.0)
        self.assertEqual(recency["bonus_pct"], 0)

    def test_inactivity_decay_active(self):
        """Test 0-3 days inactive has no decay (1.0x)."""
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        decay = TimeBasedMechanics.calculate_inactivity_decay(yesterday)

        self.assertEqual(decay["multiplier"], 1.0)
        self.assertEqual(decay["decay_pct"], 0)

    def test_inactivity_decay_week(self):
        """Test 4-7 days inactive has 0.95x decay."""
        five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
        decay = TimeBasedMechanics.calculate_inactivity_decay(five_days_ago)

        self.assertEqual(decay["multiplier"], 0.95)
        self.assertEqual(decay["decay_pct"], 5)

    def test_inactivity_decay_critical(self):
        """Test 31+ days inactive has 0.50x decay."""
        one_month_ago = (datetime.now() - timedelta(days=31)).isoformat()
        decay = TimeBasedMechanics.calculate_inactivity_decay(one_month_ago)

        self.assertEqual(decay["multiplier"], 0.50)
        self.assertEqual(decay["decay_pct"], 50)

    def test_seasonal_reset_needed(self):
        """Test seasonal reset detection at 30-day mark."""
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        reset = TimeBasedMechanics.calculate_seasonal_reset(thirty_days_ago)

        self.assertTrue(reset["should_reset"])

    def test_seasonal_reset_not_needed(self):
        """Test seasonal reset not needed before 30 days."""
        five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
        reset = TimeBasedMechanics.calculate_seasonal_reset(five_days_ago)

        self.assertFalse(reset["should_reset"])
        self.assertGreater(reset["days_until_reset"], 0)

    def test_apply_seasonal_reset(self):
        """Test applying seasonal reset adds to lifetime."""
        result = TimeBasedMechanics.apply_seasonal_reset(
            current_season_score=100.0,
            lifetime_score=50.0
        )

        # 50% of season score should be added to lifetime
        self.assertEqual(result["season_contribution_to_lifetime"], 50.0)
        self.assertEqual(result["new_lifetime_score"], 100.0)
        self.assertEqual(result["new_season_score"], 0)


class TestMigrationEngine(unittest.TestCase):
    """Test v2.0 to v3.0 migration."""

    def test_need_migration_v2_profile(self):
        """Test v2.0 profile needs migration."""
        v2_profile = {"version": "2.0", "current_score": 800}
        needs = MigrationEngine.need_migration(v2_profile)
        self.assertTrue(needs)

    def test_no_migration_v3_profile(self):
        """Test v3.0 profile doesn't need migration."""
        v3_profile = {"version": "3.0", "current_score": 800}
        needs = MigrationEngine.need_migration(v3_profile)
        self.assertFalse(needs)

    def test_migrate_profile_adds_v3_fields(self):
        """Test migration adds v3.0 fields."""
        v2_profile = {
            "version": "2.0",
            "current_score": 800,
            "current_rank": "Captain",
            "scores": {
                "token_efficiency": 300,
                "self_sufficiency": 200,  # This gets removed
            }
        }

        v3_profile = MigrationEngine.migrate_profile(v2_profile)

        # Should be v3.0
        self.assertEqual(v3_profile["version"], "3.0")

        # Should have new v3.0 fields
        self.assertIn("streak_info", v3_profile)
        self.assertIn("seasonal_info", v3_profile)
        self.assertIn("legacy", v3_profile)
        self.assertIn("migration", v3_profile)

    def test_migration_removes_self_sufficiency(self):
        """Test migration removes self_sufficiency category."""
        v2_profile = {
            "version": "2.0",
            "scores": {
                "token_efficiency": 300,
                "self_sufficiency": 200,  # This should be removed
                "best_practices": 50,
            }
        }

        v3_profile = MigrationEngine.migrate_profile(v2_profile)

        # self_sufficiency should be gone
        self.assertNotIn("self_sufficiency", v3_profile.get("scores", {}))

    def test_migration_preserves_legacy_data(self):
        """Test migration preserves v2.0 data in legacy field."""
        v2_profile = {
            "version": "2.0",
            "current_score": 800,
            "current_rank": "Captain",
            "total_sessions": 20,
        }

        v3_profile = MigrationEngine.migrate_profile(v2_profile)

        # Legacy should contain v2 snapshot
        self.assertIsNotNone(v3_profile.get("legacy"))
        self.assertEqual(v3_profile["legacy"]["v2_final_score"], 800)
        self.assertEqual(v3_profile["legacy"]["v2_current_rank"], "Captain")

    def test_validate_migration(self):
        """Test migration validation."""
        v3_profile = {
            "version": "3.0",
            "streak_info": {"current": {}, "best": {}},
            "seasonal_info": {},
            "legacy": {},
            "migration": {},
        }

        validation = MigrationEngine.validate_migration(v3_profile)

        self.assertTrue(validation["valid"])
        self.assertEqual(validation["schema_version"], "3.0")

    def test_migration_report_generation(self):
        """Test migration report shows score changes."""
        v2_profile = {
            "version": "2.0",
            "current_score": 800,
            "current_rank": "Captain",
            "scores": {"self_sufficiency": 200},
        }

        v3_profile = {
            "version": "3.0",
            "current_score": 600,
            "current_rank": "Captain",
        }

        report = MigrationEngine.generate_migration_report(v2_profile, v3_profile)

        self.assertIn("migration_date", report)
        self.assertEqual(report["source_version"], "v2.0")
        self.assertEqual(report["target_version"], "v3.0")
        self.assertIn("score_changes", report)
        self.assertIn("message", report)


class TestWasteAwarenessSystem(unittest.TestCase):
    """Test new waste awareness scoring category."""

    def test_waste_awareness_exists(self):
        """Test waste_awareness is available in scorer."""
        scorer = TokenCraftScorer([], {}, rank=1)
        self.assertIn("waste_awareness", scorer.weights)

    def test_waste_awareness_max_score(self):
        """Test waste_awareness max score is 100."""
        scorer = TokenCraftScorer([], {}, rank=1)
        self.assertEqual(scorer.weights.get("waste_awareness"), 100)


class TestV3MaxScore(unittest.TestCase):
    """Test total achievable score is 2300 (not 1450)."""

    def test_base_categories_total_2300(self):
        """Test base scoring categories total to ~2300."""
        scorer = TokenCraftScorer([], {}, rank=1)

        base_total = sum(scorer.weights.values())

        # Should be around 2300 (accounting for new categories)
        self.assertGreater(base_total, 2200)
        self.assertLess(base_total, 2400)

    def test_bonus_categories_exist(self):
        """Test bonus categories are defined for additional points."""
        scorer = TokenCraftScorer([], {}, rank=1)

        # Should have bonus weights for streak, combo, achievements, etc.
        self.assertGreater(len(scorer.bonus_weights), 0)




class TestRegressionDetector(unittest.TestCase):
    """Test Phase 10: Performance regression detection system."""

    def test_efficiency_regression_detection(self):
        """Test detecting efficiency regression."""
        from token_craft.regression_detector import RegressionDetector

        # Current efficiency worse than personal best
        current_efficiency = 2000  # tokens per message
        personal_best_efficiency = 1500  # better

        result = RegressionDetector.detect_efficiency_regression(
            current_efficiency, personal_best_efficiency
        )

        self.assertTrue(result["has_regressed"])
        self.assertGreater(result["efficiency_drop_pct"], 0)

    def test_no_efficiency_regression_when_improving(self):
        """Test no regression when improving."""
        from token_craft.regression_detector import RegressionDetector

        current_efficiency = 1200  # tokens per message
        personal_best_efficiency = 1500  # worse

        result = RegressionDetector.detect_efficiency_regression(
            current_efficiency, personal_best_efficiency
        )

        self.assertFalse(result["has_regressed"])
        self.assertEqual(result["efficiency_drop_pct"], 0)

    def test_score_regression_detection(self):
        """Test detecting score regression."""
        from token_craft.regression_detector import RegressionDetector

        current_score = 450.0
        recent_scores = [600.0, 580.0, 570.0]  # Recent average ~583

        result = RegressionDetector.detect_score_regression(
            current_score, recent_scores
        )

        self.assertTrue(result["has_regressed"])
        self.assertGreater(result["score_drop_pct"], 0)

    def test_no_score_regression_with_variance(self):
        """Test no regression for normal variance."""
        from token_craft.regression_detector import RegressionDetector

        current_score = 560.0
        recent_scores = [600.0, 580.0, 570.0]  # Recent average ~583

        result = RegressionDetector.detect_score_regression(
            current_score, recent_scores
        )

        # Small drop (23 pts from ~583) should be within threshold
        self.assertFalse(result["has_regressed"])

    def test_consecutive_decline_detection(self):
        """Test detecting consecutive declining sessions."""
        from token_craft.regression_detector import RegressionDetector

        recent_scores = [600.0, 580.0, 560.0, 540.0, 520.0]  # All declining

        result = RegressionDetector.detect_consecutive_decline(recent_scores)

        self.assertTrue(result["has_consecutive_decline"])
        self.assertEqual(result["consecutive_count"], 4)

    def test_consecutive_decline_broken_by_improvement(self):
        """Test declining streak broken by improvement."""
        from token_craft.regression_detector import RegressionDetector

        recent_scores = [600.0, 580.0, 560.0, 575.0, 570.0]  # Improved at 575

        result = RegressionDetector.detect_consecutive_decline(recent_scores)

        # Streak broken at improvement
        self.assertFalse(result["has_consecutive_decline"])
        self.assertLess(result["consecutive_count"], 3)

    def test_comprehensive_regression_analysis(self):
        """Test comprehensive regression analysis."""
        from token_craft.regression_detector import RegressionDetector

        # Severe regression scenario
        current_score = 400.0
        current_efficiency = 2500.0  # Got worse
        personal_best_efficiency = 1500.0
        recent_scores = [600.0, 580.0, 560.0, 540.0, 520.0]  # All declining

        analysis = RegressionDetector.analyze_regression(
            current_score=current_score,
            current_efficiency=current_efficiency,
            personal_best_efficiency=personal_best_efficiency,
            recent_scores=recent_scores
        )

        self.assertTrue(analysis["has_regressed"])
        self.assertIn(analysis["severity"], ["minor", "moderate", "severe"])
        self.assertGreater(analysis["regression_signals"], 0)
        self.assertIn("recommendation", analysis)

    def test_difficulty_adjustment_for_severe_regression(self):
        """Test difficulty adjustment recommendation for severe regression."""
        from token_craft.regression_detector import RegressionDetector

        # Build severe regression analysis
        analysis = {
            "severity": "severe",
            "has_regressed": True,
            "regression_signals": 3,
        }

        adjustment = RegressionDetector.calculate_difficulty_adjustment(analysis)

        self.assertTrue(adjustment["should_adjust"])
        self.assertEqual(adjustment["adjustment_factor"], 0.85)  # 15% easier
        self.assertEqual(adjustment["duration_days"], 14)

    def test_no_difficulty_adjustment_for_minor_regression(self):
        """Test no difficulty adjustment for minor regression."""
        from token_craft.regression_detector import RegressionDetector

        analysis = {
            "severity": "minor",
            "has_regressed": True,
            "regression_signals": 1,
        }

        adjustment = RegressionDetector.calculate_difficulty_adjustment(analysis)

        self.assertFalse(adjustment["should_adjust"])
        self.assertEqual(adjustment["adjustment_factor"], 1.0)

    def test_recovery_guidance_provided(self):
        """Test recovery guidance is provided on regression."""
        from token_craft.regression_detector import RegressionDetector

        analysis = RegressionDetector.analyze_regression(
            current_score=400.0,
            current_efficiency=2500.0,
            personal_best_efficiency=1500.0,
            recent_scores=[600.0, 550.0, 500.0]
        )

        guidance = RegressionDetector.get_recovery_guidance(analysis)

        self.assertIsNotNone(guidance)
        self.assertGreater(len(guidance), 0)
        self.assertIn("Token", guidance)  # Should mention some metric


class TestV3IntegrationWithRegression(unittest.TestCase):
    """Test v3.0 full integration including regression detection."""

    def setUp(self):
        """Set up test data."""
        self.history_data = [
            {
                "sessionId": "session1",
                "project": "project_a",
                "message": "test message",
                "timestamp": "2026-02-12T10:00:00Z"
            },
        ]

        self.stats_data = {
            "models": {
                "claude-sonnet-4.5": {
                    "inputTokens": 50000,
                    "outputTokens": 30000
                }
            }
        }

        self.user_profile_v3 = {
            "version": "3.0",
            "current_rank": "Captain",
            "current_score": 600,
            "total_sessions": 5,
            "recent_session_scores": [600.0, 580.0, 560.0, 540.0],
            "streak_info": {"current": {"length": 2}},
            "seasonal_info": {},
            "achievements": [],
        }

    def test_regression_info_in_total_score(self):
        """Test regression analysis included in total_score output."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=5, user_profile=self.user_profile_v3)
        score_data = scorer.calculate_total_score()

        self.assertIn("regression_analysis", score_data)
        regression = score_data["regression_analysis"]
        self.assertIn("has_regressed", regression)
        self.assertIn("severity", regression)
        self.assertIn("recommendation", regression)

    def test_severe_regression_detected_when_appropriate(self):
        """Test severe regression is detected with multiple declining signals."""
        profile_with_regression = {
            "version": "3.0",
            "current_rank": "Captain",
            "current_score": 400,  # Down from 600
            "recent_session_scores": [600.0, 550.0, 500.0, 450.0],  # Consistent decline
        }

        scorer = TokenCraftScorer(self.history_data, self.stats_data, rank=5, user_profile=profile_with_regression)
        score_data = scorer.calculate_total_score()

        regression = score_data["regression_analysis"]
        # Should detect multiple signals
        self.assertGreater(regression.get("efficiency", {}).get("efficiency_drop_pct", -1), 0)


if __name__ == "__main__":
    unittest.main()
