"""
Unit tests for Token-Craft scoring engine and v2.0 integrations.
"""

import unittest
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from token_craft.scoring_engine import TokenCraftScorer
from token_craft.rank_system import SpaceRankSystem
from token_craft.delta_calculator import DeltaCalculator
from token_craft.user_profile import UserProfile
from token_craft.recommendation_tracker import RecommendationTracker
from token_craft.experimentation import ExperimentationFramework
from token_craft.pattern_library import PatternLibrary


class TestSpaceRankSystem(unittest.TestCase):
    """Test rank system."""

    def test_get_rank_cadet(self):
        """Test Cadet rank (0-269 in v2.0)."""
        rank = SpaceRankSystem.get_rank(100)
        self.assertEqual(rank["name"], "Cadet")
        self.assertEqual(rank["min"], 0)
        self.assertEqual(rank["max"], 269)

    def test_get_rank_pilot(self):
        """Test Pilot rank (270-539 in v2.0)."""
        rank = SpaceRankSystem.get_rank(300)
        self.assertEqual(rank["name"], "Pilot")

    def test_get_rank_legend(self):
        """Test Galactic Legend rank (1620+ in v2.0)."""
        rank = SpaceRankSystem.get_rank(1700)
        self.assertEqual(rank["name"], "Galactic Legend")

    def test_get_next_rank(self):
        """Test next rank calculation."""
        next_rank = SpaceRankSystem.get_next_rank(150)
        self.assertEqual(next_rank["name"], "Pilot")
        self.assertEqual(next_rank["points_needed"], 120)

    def test_get_next_rank_max(self):
        """Test next rank at max level."""
        next_rank = SpaceRankSystem.get_next_rank(1700)
        self.assertIsNone(next_rank)

    def test_progress_bar(self):
        """Test progress bar generation."""
        bar = SpaceRankSystem.get_progress_bar(100, width=10)
        self.assertEqual(len(bar), 10)
        self.assertIn("\u2588", bar)
        self.assertIn("\u2591", bar)

    def test_rank_level(self):
        """Test numeric rank level."""
        level = SpaceRankSystem.calculate_rank_level(100)
        self.assertEqual(level, 1)  # Cadet

        level = SpaceRankSystem.calculate_rank_level(500)
        self.assertEqual(level, 2)  # Pilot (270-539 in v2.0)

        level = SpaceRankSystem.calculate_rank_level(600)
        self.assertEqual(level, 3)  # Navigator (540-809 in v2.0)


class TestTokenCraftScorer(unittest.TestCase):
    """Test scoring engine."""

    def setUp(self):
        """Set up test data."""
        self.history_data = [
            {
                "sessionId": "session1",
                "project": "/test/project",
                "message": "test message",
                "timestamp": "2026-02-12T10:00:00Z"
            },
            {
                "sessionId": "session1",
                "project": "/test/project",
                "message": "another message",
                "timestamp": "2026-02-12T10:05:00Z"
            }
        ]

        self.stats_data = {
            "models": {
                "claude-sonnet-4.5": {
                    "inputTokens": 50000,
                    "outputTokens": 30000
                }
            }
        }

    def test_scorer_initialization(self):
        """Test scorer initialization."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        self.assertIsNotNone(scorer)
        self.assertEqual(scorer.total_sessions, 1)
        self.assertEqual(scorer.total_tokens, 80000)

    def test_token_efficiency_score(self):
        """Test token efficiency calculation."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_token_efficiency_score()

        self.assertIn("score", score_data)
        self.assertIn("max_score", score_data)
        self.assertIn("percentage", score_data)
        self.assertEqual(score_data["max_score"], 300)

    def test_optimization_adoption_score(self):
        """Test optimization adoption calculation."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_optimization_adoption_score()

        self.assertIn("score", score_data)
        self.assertEqual(score_data["max_score"], 325)
        self.assertIn("breakdown", score_data)

    def test_self_sufficiency_score(self):
        """Test self-sufficiency calculation."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_self_sufficiency_score()

        self.assertIn("score", score_data)
        self.assertEqual(score_data["max_score"], 200)

    def test_best_practices_score(self):
        """Test best practices calculation."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_best_practices_score()

        self.assertIn("score", score_data)
        self.assertEqual(score_data["max_score"], 50)

    def test_total_score_all_11_categories(self):
        """Test total score includes all 11 categories with 1450 max."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_total_score()

        self.assertIn("total_score", score_data)
        self.assertIn("max_possible", score_data)
        self.assertEqual(score_data["max_possible"], 1450)
        self.assertIn("breakdown", score_data)

        # Check all 11 categories present
        expected_categories = [
            "token_efficiency", "optimization_adoption", "self_sufficiency",
            "improvement_trend", "best_practices",
            "cache_effectiveness", "tool_efficiency", "cost_efficiency",
            "session_focus", "learning_growth", "waste_awareness"
        ]
        for cat in expected_categories:
            self.assertIn(cat, score_data["breakdown"],
                         f"Missing category: {cat}")

    def test_each_category_has_score_and_max(self):
        """Every category in breakdown must have score and max_score."""
        scorer = TokenCraftScorer(self.history_data, self.stats_data)
        score_data = scorer.calculate_total_score()

        for cat, data in score_data["breakdown"].items():
            self.assertIn("score", data, f"{cat} missing 'score'")
            self.assertIn("max_score", data, f"{cat} missing 'max_score'")
            self.assertGreaterEqual(data["score"], 0, f"{cat} score < 0")
            self.assertLessEqual(data["score"], data["max_score"],
                               f"{cat} score > max_score")


class TestDeltaCalculator(unittest.TestCase):
    """Test delta calculator with dynamic categories."""

    def test_delta_with_5_categories(self):
        """Old snapshots with 5 categories still work."""
        current = {
            "scores": {
                "total_score": 500,
                "breakdown": {
                    "token_efficiency": {"score": 200},
                    "optimization_adoption": {"score": 150},
                    "self_sufficiency": {"score": 80},
                    "improvement_trend": {"score": 50},
                    "best_practices": {"score": 20}
                }
            },
            "rank": {"name": "Navigator"},
            "profile": {},
            "timestamp": "2026-02-13T10:00:00"
        }
        previous = {
            "scores": {
                "total_score": 400,
                "breakdown": {
                    "token_efficiency": {"score": 150},
                    "optimization_adoption": {"score": 120},
                    "self_sufficiency": {"score": 70},
                    "improvement_trend": {"score": 40},
                    "best_practices": {"score": 20}
                }
            },
            "rank": {"name": "Pilot"},
            "profile": {},
            "timestamp": "2026-02-12T10:00:00"
        }

        delta = DeltaCalculator.calculate_delta(current, previous)
        self.assertEqual(delta["score_change"], 100)
        self.assertEqual(len(delta["category_changes"]), 5)

    def test_delta_with_11_categories(self):
        """New snapshots with 11 categories get full delta tracking."""
        cats = [
            "token_efficiency", "optimization_adoption", "self_sufficiency",
            "improvement_trend", "best_practices",
            "cache_effectiveness", "tool_efficiency", "cost_efficiency",
            "session_focus", "learning_growth", "waste_awareness"
        ]
        current_bd = {c: {"score": 50} for c in cats}
        previous_bd = {c: {"score": 40} for c in cats}

        current = {
            "scores": {"total_score": 550, "breakdown": current_bd},
            "rank": {"name": "Navigator"},
            "profile": {},
            "timestamp": "2026-02-13T10:00:00"
        }
        previous = {
            "scores": {"total_score": 440, "breakdown": previous_bd},
            "rank": {"name": "Pilot"},
            "profile": {},
            "timestamp": "2026-02-12T10:00:00"
        }

        delta = DeltaCalculator.calculate_delta(current, previous)
        self.assertEqual(len(delta["category_changes"]), 11)
        for cat in cats:
            self.assertIn(cat, delta["category_changes"])
            self.assertEqual(delta["category_changes"][cat]["change"], 10)

    def test_delta_mixed_categories(self):
        """Old 5-cat snapshot vs new 11-cat snapshot works."""
        current_bd = {c: {"score": 50} for c in [
            "token_efficiency", "optimization_adoption", "self_sufficiency",
            "improvement_trend", "best_practices",
            "cache_effectiveness", "tool_efficiency", "cost_efficiency",
            "session_focus", "learning_growth", "waste_awareness"
        ]}
        previous_bd = {c: {"score": 40} for c in [
            "token_efficiency", "optimization_adoption", "self_sufficiency",
            "improvement_trend", "best_practices"
        ]}

        current = {
            "scores": {"total_score": 550, "breakdown": current_bd},
            "rank": {"name": "Navigator"},
            "profile": {},
            "timestamp": "2026-02-13T10:00:00"
        }
        previous = {
            "scores": {"total_score": 200, "breakdown": previous_bd},
            "rank": {"name": "Pilot"},
            "profile": {},
            "timestamp": "2026-02-12T10:00:00"
        }

        delta = DeltaCalculator.calculate_delta(current, previous)
        # Union of both sets = 11
        self.assertEqual(len(delta["category_changes"]), 11)
        # New categories should show current vs 0
        self.assertEqual(delta["category_changes"]["waste_awareness"]["previous"], 0)
        self.assertEqual(delta["category_changes"]["waste_awareness"]["current"], 50)


class TestUserProfileScores(unittest.TestCase):
    """Test user profile stores all 11 category scores."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_new_profile_has_11_scores(self):
        """New profile should have all 11 category scores."""
        profile = UserProfile(user_email="test@example.com", profile_dir=self.tmp_dir)
        scores = profile.data["scores"]
        self.assertEqual(len(scores), 11)
        self.assertIn("waste_awareness", scores)
        self.assertIn("cache_effectiveness", scores)

    def test_update_stores_all_categories(self):
        """update_from_analysis should store all categories dynamically."""
        profile = UserProfile(user_email="test@example.com", profile_dir=self.tmp_dir)

        score_data = {
            "total_score": 700,
            "breakdown": {
                "token_efficiency": {"score": 200},
                "optimization_adoption": {"score": 150},
                "self_sufficiency": {"score": 100},
                "improvement_trend": {"score": 50},
                "best_practices": {"score": 30},
                "cache_effectiveness": {"score": 50},
                "tool_efficiency": {"score": 40},
                "cost_efficiency": {"score": 30},
                "session_focus": {"score": 20},
                "learning_growth": {"score": 15},
                "waste_awareness": {"score": 15}
            }
        }
        rank_data = {"name": "Commander"}

        profile.update_from_analysis(score_data, rank_data)
        self.assertEqual(len(profile.data["scores"]), 11)
        self.assertEqual(profile.data["scores"]["waste_awareness"], 15)
        self.assertEqual(profile.data["scores"]["cache_effectiveness"], 50)


class TestRecommendationTrackerSmoke(unittest.TestCase):
    """Basic smoke tests for RecommendationTracker."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp()) / "token-craft"
        self.tmp_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir.parent, ignore_errors=True)

    def test_track_and_find(self):
        """Track a recommendation and find it."""
        tracker = RecommendationTracker()
        tracker.recommendations_file = self.tmp_dir / "recommendations.json"
        tracker.recommendations = tracker._load_recommendations()

        tracker.track_recommendation(
            "test_rec_1", "Test Recommendation", "token_efficiency",
            {"tokens_before": 50000}
        )

        rec = tracker._find_recommendation("test_rec_1")
        self.assertIsNotNone(rec)
        self.assertEqual(rec["status"], "pending")
        self.assertIn("test_rec_1", tracker.recommendations["pending"])

    def test_mark_implemented(self):
        """Mark a recommendation as implemented."""
        tracker = RecommendationTracker()
        tracker.recommendations_file = self.tmp_dir / "recommendations.json"
        tracker.recommendations = tracker._load_recommendations()

        tracker.track_recommendation(
            "test_rec_2", "Test Rec 2", "optimization_adoption",
            {"tokens_before": 40000}
        )
        tracker.mark_implemented("test_rec_2", {"tokens_after": 30000, "sessions_after": 5})

        rec = tracker._find_recommendation("test_rec_2")
        self.assertEqual(rec["status"], "implemented")
        self.assertIn("test_rec_2", tracker.recommendations["implemented"])


class TestPatternLibrarySmoke(unittest.TestCase):
    """Basic smoke tests for PatternLibrary."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp()) / "token-craft"
        self.tmp_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir.parent, ignore_errors=True)

    def test_seeds_defaults(self):
        """Library should seed default patterns on first init."""
        library = PatternLibrary()
        library.patterns_file = self.tmp_dir / "patterns.json"
        library.patterns = {"patterns": [], "version": "1.0"}
        library._seed_default_patterns()

        self.assertGreater(len(library.patterns["patterns"]), 0)
        ids = [p["id"] for p in library.patterns["patterns"]]
        self.assertIn("pattern_defer_docs", ids)
        self.assertIn("pattern_claude_md", ids)

    def test_record_trial(self):
        """Record a trial and verify evidence updates."""
        library = PatternLibrary()
        library.patterns_file = self.tmp_dir / "patterns.json"
        library.patterns = {"patterns": [], "version": "1.0"}
        library._seed_default_patterns()

        library.record_trial(
            "pattern_defer_docs", success=True,
            before_tokens=50000, after_tokens=35000,
            session_id="test_session", details="test"
        )

        pattern = library._find_pattern("pattern_defer_docs")
        self.assertEqual(pattern["evidence"]["trials"], 1)
        self.assertEqual(pattern["evidence"]["success_count"], 1)
        self.assertGreater(pattern["evidence"]["avg_improvement"], 0)


class TestExperimentationFrameworkSmoke(unittest.TestCase):
    """Basic smoke tests for ExperimentationFramework."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp()) / "token-craft"
        self.tmp_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir.parent, ignore_errors=True)

    def test_create_experiment(self):
        """Create an experiment and verify structure."""
        framework = ExperimentationFramework()
        framework.experiments_file = self.tmp_dir / "experiments.json"
        framework.experiments = framework._load_experiments()

        exp_id = framework.create_experiment(
            "Test Experiment", "inline_docs", "defer_docs"
        )
        self.assertIsNotNone(exp_id)

        exp = framework._find_experiment(exp_id)
        self.assertEqual(exp["status"], "active")
        self.assertEqual(len(exp["arms"]), 2)

    def test_insufficient_data(self):
        """Compare with insufficient data returns proper status."""
        framework = ExperimentationFramework()
        framework.experiments_file = self.tmp_dir / "experiments.json"
        framework.experiments = framework._load_experiments()

        exp_id = framework.create_experiment(
            "Test Experiment 2", "verbose", "concise"
        )
        result = framework.compare_approaches(exp_id)
        self.assertEqual(result["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
