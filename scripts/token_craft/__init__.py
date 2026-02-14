"""
Token-Craft: Master LLM efficiency through space exploration ranks.

A gamified token optimization system inspired by retro computing constraints.
"""

__version__ = "2.0.0"
__author__ = "DmitriyZhorov"

from .scoring_engine import TokenCraftScorer
from .rank_system import SpaceRankSystem
from .user_profile import UserProfile
from .snapshot_manager import SnapshotManager
from .delta_calculator import DeltaCalculator
from .report_generator import ReportGenerator
from .progress_visualizer import ProgressVisualizer
from .leaderboard_generator import LeaderboardGenerator

from .team_exporter import TeamExporter
from .recommendation_engine import RecommendationEngine
from .interactive_menu import InteractiveMenu
from .pricing_calculator import PricingCalculator
from .waste_detector import WasteDetector
from .insights_engine import InsightsEngine
from .recommendation_tracker import RecommendationTracker
from .experimentation import ExperimentationFramework
from .pattern_library import PatternLibrary
from .cost_alerts import CostAlerts
from .session_analyzer import SessionAnalyzer

__all__ = [
    "TokenCraftScorer",
    "SpaceRankSystem",
    "UserProfile",
    "SnapshotManager",
    "DeltaCalculator",
    "ReportGenerator",
    "ProgressVisualizer",
    "LeaderboardGenerator",
    "TeamExporter",
    "RecommendationEngine",
    "InteractiveMenu",
    "PricingCalculator",
    "WasteDetector",
    "InsightsEngine",
    "RecommendationTracker",
    "ExperimentationFramework",
    "PatternLibrary",
    "CostAlerts",
    "SessionAnalyzer",
]
