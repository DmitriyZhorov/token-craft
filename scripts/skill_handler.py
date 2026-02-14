"""
Token-Craft Skill Handler

Main entry point for the /token-craft skill.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Add token_craft to path
sys.path.insert(0, str(Path(__file__).parent))

from token_craft.scoring_engine import TokenCraftScorer
from token_craft.rank_system import SpaceRankSystem
from token_craft.user_profile import UserProfile
from token_craft.snapshot_manager import SnapshotManager
from token_craft.delta_calculator import DeltaCalculator
from token_craft.report_generator import ReportGenerator

# v2.0 components
try:
    from token_craft.waste_detector import WasteDetector
    from token_craft.insights_engine import InsightsEngine
    from token_craft.recommendation_tracker import RecommendationTracker
    from token_craft.experimentation import ExperimentationFramework
    from token_craft.pattern_library import PatternLibrary
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False


class TokenCraftHandler:
    """Main handler for Token-Craft skill."""

    def __init__(self):
        """Initialize handler."""
        self.claude_dir = Path.home() / ".claude"
        self.history_file = self.claude_dir / "history.jsonl"
        self.stats_file = self.claude_dir / "stats-cache.json"

        self.profile = UserProfile()
        self.snapshot_manager = SnapshotManager()
        self.report_generator = ReportGenerator()

    def load_data(self) -> tuple:
        """
        Load history and stats data.

        Returns:
            Tuple of (history_data, stats_data)
        """
        # Load history.jsonl
        history_data = []
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                history_data.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                print(f"Warning: Could not load history.jsonl: {e}")

        # Load stats-cache.json
        stats_data = {}
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    stats_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load stats-cache.json: {e}")

        return history_data, stats_data

    def calculate_scores(self, history_data: list, stats_data: Dict, previous_snapshot: Optional[Dict] = None) -> Dict:
        """
        Calculate user scores.

        Args:
            history_data: Parsed history.jsonl
            stats_data: Parsed stats-cache.json
            previous_snapshot: Previous snapshot for trend calculation

        Returns:
            Score data
        """
        scorer = TokenCraftScorer(history_data, stats_data)
        score_data = scorer.calculate_total_score(previous_snapshot)

        return score_data

    def run(self, mode: str = "full") -> str:
        """
        Run the Token-Craft analysis.

        Args:
            mode: 'full', 'summary', or 'quick'

        Returns:
            Formatted report
        """
        try:
            # Load data
            print("Loading your data...")
            history_data, stats_data = self.load_data()

            if not history_data:
                return "No history data found. Start using Claude Code to track your progress!"

            # Get previous snapshot for comparison
            previous_snapshot = self.snapshot_manager.get_latest_snapshot()

            # Calculate scores
            print("Calculating your scores...")
            previous_profile = None
            if previous_snapshot and isinstance(previous_snapshot, dict):
                previous_profile = previous_snapshot.get("profile")

            score_data = self.calculate_scores(
                history_data,
                stats_data,
                previous_profile
            )

            # Get rank
            rank_data = SpaceRankSystem.get_rank(score_data["total_score"])

            # Calculate delta if we have previous data
            delta_data = None
            if previous_snapshot:
                current_snapshot = {
                    "timestamp": score_data["calculated_at"],
                    "profile": self.profile.get_current_state(),
                    "scores": score_data,
                    "rank": rank_data
                }
                delta_data = DeltaCalculator.calculate_delta(current_snapshot, previous_snapshot)

            # Update profile
            self.profile.update_from_analysis(score_data, rank_data)

            # Check for achievements
            self._check_achievements(score_data, rank_data, delta_data)

            # v2.0 module integration (never breaks core report)
            if V2_AVAILABLE and mode == "full":
                try:
                    self._run_v2_integrations(score_data, history_data)
                except Exception:
                    pass

            # Save profile
            self.profile.save()

            # Create snapshot
            print("Saving snapshot...")
            self.snapshot_manager.create_snapshot(
                self.profile.get_current_state(),
                score_data,
                rank_data
            )

            # Generate report
            print("Generating report...")
            if mode == "summary":
                report = self.report_generator.generate_summary(
                    self.profile.get_current_state(),
                    score_data,
                    rank_data
                )
            elif mode == "quick":
                report = self._generate_quick_status(score_data, rank_data)
            else:  # full
                report = self.report_generator.generate_full_report(
                    self.profile.get_current_state(),
                    score_data,
                    rank_data,
                    delta_data,
                    history_data
                )

            return report

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error running Token-Craft: {e}\n\nDetails:\n{error_details}\n\nPlease report this issue."

    def _check_achievements(self, score_data: Dict, rank_data: Dict, delta_data: Optional[Dict]):
        """Check and award achievements."""
        # First rank achievement
        if rank_data["name"] == "Pilot" and not any(a["id"] == "first_pilot" for a in self.profile.get_achievements()):
            self.profile.add_achievement(
                "first_pilot",
                "First Pilot",
                "Achieved Pilot rank for the first time"
            )

        # Score milestones
        score = score_data["total_score"]
        if score >= 500 and not any(a["id"] == "halfway_there" for a in self.profile.get_achievements()):
            self.profile.add_achievement(
                "halfway_there",
                "Halfway There",
                "Reached 500 points"
            )

        if score >= 1000 and not any(a["id"] == "four_digits" for a in self.profile.get_achievements()):
            self.profile.add_achievement(
                "four_digits",
                "Four Digits",
                "Reached 1000+ points (Admiral level)"
            )

        # Efficiency achievement
        efficiency_pct = score_data["breakdown"]["token_efficiency"].get("improvement_pct", 0)
        if efficiency_pct >= 30 and not any(a["id"] == "efficiency_master" for a in self.profile.get_achievements()):
            self.profile.add_achievement(
                "efficiency_master",
                "Efficiency Master",
                "Achieved 30%+ better efficiency than baseline"
            )

        # Promotion achievement
        if delta_data and isinstance(delta_data, dict):
            rank_change = delta_data.get("rank_change")
            if rank_change and isinstance(rank_change, dict) and rank_change.get("promoted"):
                promo_id = f"promoted_to_{rank_data['name'].lower()}"
                if not any(a["id"] == promo_id for a in self.profile.get_achievements()):
                    self.profile.add_achievement(
                        promo_id,
                        f"Promoted to {rank_data['name']}",
                        f"Achieved {rank_data['name']} rank"
                    )

    def _run_v2_integrations(self, score_data: Dict, history_data: list):
        """
        Run v2.0 module integrations (RecommendationTracker, ExperimentationFramework, PatternLibrary).
        All operations are best-effort; failures never break the core report.
        """
        from token_craft.recommendation_engine import RecommendationEngine

        # 5a. RecommendationTracker — track and detect implementations
        try:
            tracker = RecommendationTracker()

            # Generate recommendations and track them
            recommendations = RecommendationEngine.generate_recommendations(
                score_data, self.profile.get_current_state(), history_data
            )

            baseline_metrics = {
                "tokens_before": int(self.profile.data.get("avg_tokens_per_session", 0)),
                "total_score": score_data.get("total_score", 0)
            }

            for rec in recommendations:
                tracker.track_recommendation(
                    rec["id"],
                    rec["title"],
                    rec.get("category", "general"),
                    baseline_metrics
                )

            # Check pending recommendations for implementation
            for rec_id in list(tracker.recommendations.get("pending", [])):
                if tracker.detect_implementation(rec_id, self.sessions if hasattr(self, 'sessions') else []):
                    current_metrics = {
                        "tokens_after": int(self.profile.data.get("avg_tokens_per_session", 0)),
                        "sessions_after": self.profile.data.get("total_sessions", 1)
                    }
                    tracker.mark_implemented(rec_id, current_metrics)
        except Exception:
            pass

        # 5b. ExperimentationFramework — auto-detect A/B comparisons
        try:
            framework = ExperimentationFramework()

            # Auto-create experiments from history sessions
            # history_data is a flat list of entries, not sessions.
            # ExperimentationFramework.auto_create_experiments expects session-like dicts.
            # We can pass history_data and let it detect approaches.
            framework.auto_create_experiments(history_data)

            # Compare active experiments with enough data
            for exp in framework.experiments.get("experiments", []):
                if exp.get("status") == "active":
                    arms = exp.get("arms", [])
                    has_enough = all(len(arm.get("sessions", [])) >= 3 for arm in arms)
                    if has_enough:
                        framework.compare_approaches(exp["id"])
        except Exception:
            pass

        # 5c. PatternLibrary — record trials from session-over-session data
        try:
            library = PatternLibrary()

            breakdown = score_data.get("breakdown", {})
            total_tokens = self.profile.data.get("total_tokens", 0)
            avg_tokens = self.profile.data.get("avg_tokens_per_session", 0)

            # Record trial for defer_docs pattern
            adoption = breakdown.get("optimization_adoption", {})
            defer_data = adoption.get("breakdown", {}).get("defer_docs", {})
            if defer_data.get("opportunities", 0) > 0:
                success = defer_data.get("consistency", 0) >= 60
                library.record_trial(
                    "pattern_defer_docs",
                    success=success,
                    before_tokens=int(avg_tokens * 1.2),
                    after_tokens=int(avg_tokens),
                    session_id=f"analysis_{score_data.get('calculated_at', 'unknown')}",
                    details=f"Defer docs consistency: {defer_data.get('consistency', 0)}%"
                )

            # Record trial for CLAUDE.md pattern
            claude_md = adoption.get("breakdown", {}).get("claude_md", {})
            if claude_md.get("top_projects", 0) > 0:
                success = claude_md.get("with_claude_md", 0) >= 1
                library.record_trial(
                    "pattern_claude_md",
                    success=success,
                    before_tokens=int(avg_tokens * 1.15),
                    after_tokens=int(avg_tokens),
                    session_id=f"analysis_{score_data.get('calculated_at', 'unknown')}",
                    details=f"CLAUDE.md in {claude_md.get('with_claude_md', 0)}/{claude_md.get('top_projects', 0)} projects"
                )

            # Record trial for concise prompts pattern
            concise = adoption.get("breakdown", {}).get("concise_mode", {})
            if concise:
                success = concise.get("preference_set", False)
                library.record_trial(
                    "pattern_concise_prompts",
                    success=success,
                    before_tokens=int(avg_tokens * 1.1),
                    after_tokens=int(avg_tokens),
                    session_id=f"analysis_{score_data.get('calculated_at', 'unknown')}",
                    details=f"Concise mode: {'enabled' if success else 'disabled'}"
                )

            # Discover new patterns from history
            library.discover_new_patterns(history_data)
        except Exception:
            pass

    def _generate_quick_status(self, score_data: Dict, rank_data: Dict) -> str:
        """Generate quick one-line status."""
        next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])

        status = f"{rank_data['icon']} {rank_data['name']} - {score_data['total_score']:.0f} points"

        if next_rank:
            status += f" ({next_rank['points_needed']} to {next_rank['name']})"

        return status


def show_menu():
    """Show interactive menu and get user choice."""
    print("\n" + "="*70)
    print("              TOKEN-CRAFT - Interactive Menu")
    print("="*70)
    print("\nHow would you like to view your report?\n")
    print("  [1] Full Report (detailed breakdown with recommendations)")
    print("  [2] Quick Summary (rank and score overview)")
    print("  [3] One-Line Status (just rank and score)")
    print("  [4] JSON Output (for programmatic access)")
    print("  [Q] Quit")
    print("\n" + "="*70)

    while True:
        choice = input("\nYour choice: ").strip().upper()

        if choice in ['1', 'FULL', 'F']:
            return 'full'
        elif choice in ['2', 'SUMMARY', 'S']:
            return 'summary'
        elif choice in ['3', 'QUICK', 'Q', 'ONE']:
            return 'quick'
        elif choice in ['4', 'JSON', 'J']:
            return 'json'
        elif choice in ['QUIT', 'EXIT', 'Q']:
            return None
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, or Q.")


def main():
    """Main entry point - fully interactive."""
    import sys
    import io

    # Fix Windows CMD encoding issues
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Show menu and get choice
    mode = show_menu()

    if mode is None:
        print("\n👋 Thanks for using Token-Craft!")
        return

    # Run analysis
    handler = TokenCraftHandler()

    if mode == 'json':
        report = handler.run(mode='full')
        output = {
            "profile": handler.profile.get_current_state(),
            "report": report
        }
        print(json.dumps(output, indent=2))
    else:
        report = handler.run(mode=mode)
        print(report)


if __name__ == "__main__":
    main()
