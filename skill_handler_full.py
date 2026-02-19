"""
Token-Craft Skill Handler (Full Version)

Main entry point with all features: leaderboards, team export, hero badges, interactive menu.
Supports v3.0 gamification with difficulty scaling, streaks, achievements, and regression detection.
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
from token_craft.leaderboard_generator import LeaderboardGenerator
from token_craft.hero_api_client import MockHeroClient
from token_craft.team_exporter import TeamExporter
from token_craft.recommendation_engine import RecommendationEngine
from token_craft.interactive_menu import InteractiveMenu
from token_craft.difficulty_modifier import DifficultyModifier
from token_craft.streak_system import StreakSystem
from token_craft.achievement_engine import AchievementEngine
from token_craft.time_based_mechanics import TimeBasedMechanics
from token_craft.regression_detector import RegressionDetector


class TokenCraftHandlerFull:
    """Full Token-Craft handler with all features."""

    def __init__(self):
        """Initialize handler with all components."""
        self.claude_dir = Path.home() / ".claude"
        self.history_file = self.claude_dir / "history.jsonl"
        self.stats_file = self.claude_dir / "stats-cache.json"

        self.profile = UserProfile()
        self.snapshot_manager = SnapshotManager()
        self.report_generator = ReportGenerator()
        self.leaderboard_generator = LeaderboardGenerator()
        self.hero_client = MockHeroClient()
        self.team_exporter = TeamExporter()
        self.recommendation_engine = RecommendationEngine()
        self.menu = InteractiveMenu()

        # Cache for current session
        self.current_score_data = None
        self.current_rank_data = None
        self.current_recommendations = None

    def load_data(self) -> tuple:
        """Load history and stats data."""
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

        stats_data = {}
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    stats_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load stats-cache.json: {e}")

        return history_data, stats_data

    def calculate_scores(self, history_data: list, stats_data: Dict, previous_snapshot: Optional[Dict] = None, user_rank: int = 1) -> Dict:
        """
        Calculate user scores using v3.0 system.

        Args:
            history_data: Parsed history.jsonl
            stats_data: Parsed stats-cache.json
            previous_snapshot: Previous snapshot for trend calculation
            user_rank: Current user rank (1-10) for v3.0 difficulty scaling

        Returns:
            Score data with v3.0 metrics
        """
        scorer = TokenCraftScorer(history_data, stats_data, user_rank=user_rank, user_profile=self.profile.get_current_state())
        score_data = scorer.calculate_total_score(previous_snapshot)
        return score_data

    def run_analysis(self) -> bool:
        """
        Run full analysis and cache results (v3.0 with difficulty scaling).

        Returns:
            True if successful
        """
        try:
            print("Loading your data...")
            history_data, stats_data = self.load_data()

            if not history_data:
                print("No history data found. Start using Claude Code to track your progress!")
                return False

            # Get previous snapshot
            previous_snapshot = self.snapshot_manager.get_latest_snapshot()

            # Calculate current rank for v3.0 difficulty scaling
            previous_profile = None
            if previous_snapshot and isinstance(previous_snapshot, dict):
                previous_profile = previous_snapshot.get("profile")

            previous_score = previous_profile.get("total_score", 0) if previous_profile else 0
            previous_rank_data = SpaceRankSystem.get_rank(previous_score)
            current_rank = previous_rank_data.get("rank", 1)

            # Calculate scores with v3.0 difficulty scaling
            print("Calculating your scores (v3.0 with difficulty scaling)...")
            self.current_score_data = self.calculate_scores(
                history_data,
                stats_data,
                previous_profile,
                user_rank=current_rank
            )

            # Get new rank based on v3.0 score
            self.current_rank_data = SpaceRankSystem.get_rank(self.current_score_data["total_score"])

            # Calculate delta
            delta_data = None
            if previous_snapshot:
                current_snapshot = {
                    "timestamp": self.current_score_data["calculated_at"],
                    "profile": self.profile.get_current_state(),
                    "scores": self.current_score_data,
                    "rank": self.current_rank_data
                }
                delta_data = DeltaCalculator.calculate_delta(current_snapshot, previous_snapshot)

            # Update profile
            self.profile.update_from_analysis(self.current_score_data, self.current_rank_data)

            # Check achievements
            self._check_achievements(self.current_score_data, self.current_rank_data, delta_data)

            # Sync with hero.epam.com
            self._sync_hero_badges()

            # Generate recommendations
            self.current_recommendations = self.recommendation_engine.generate_recommendations(
                self.current_score_data,
                self.profile.get_current_state()
            )

            # Save profile and snapshot
            self.profile.save()
            print("Saving snapshot...")
            self.snapshot_manager.create_snapshot(
                self.profile.get_current_state(),
                self.current_score_data,
                self.current_rank_data
            )

            return True

        except Exception as e:
            import traceback
            print(f"Error running analysis: {e}")
            print(traceback.format_exc())
            return False

    def show_full_report(self):
        """Show full report."""
        if not self.current_score_data:
            print("No analysis data available. Run analysis first.")
            return

        previous_snapshot = self.snapshot_manager.get_latest_snapshot()
        delta_data = None

        if previous_snapshot:
            current_snapshot = {
                "timestamp": self.current_score_data["calculated_at"],
                "profile": self.profile.get_current_state(),
                "scores": self.current_score_data,
                "rank": self.current_rank_data
            }
            delta_data = DeltaCalculator.calculate_delta(current_snapshot, previous_snapshot)

        report = self.report_generator.generate_full_report(
            self.profile.get_current_state(),
            self.current_score_data,
            self.current_rank_data,
            delta_data
        )

        print(report)

    def run_interactive(self):
        """Run interactive mode with menu."""
        # Run analysis first
        if not self.run_analysis():
            return

        # Show initial report
        print("\nGenerating your report...")
        self.show_full_report()

        # Interactive loop
        while True:
            choice = self.menu.show_main_menu()

            if choice == "A":
                self._handle_apply_optimizations()
            elif choice == "E":
                self._handle_export_stats()
            elif choice == "L":
                self._handle_leaderboards()
            elif choice == "H":
                self._handle_achievements()
            elif choice == "R":
                self._handle_detailed_recommendations()
            elif choice == "S":
                self.show_full_report()
            elif choice == "Q":
                print("\nFly safe, space explorer! 🚀")
                break
            else:
                print("Invalid choice. Please try again.")

    def _handle_apply_optimizations(self):
        """Handle optimization application."""
        if not self.current_recommendations:
            print("\nNo recommendations available.")
            return

        selected_ids = self.menu.show_optimization_menu(self.current_recommendations)

        if not selected_ids:
            print("\nNo optimizations selected.")
            return

        print("\n" + "=" * 70)
        print("APPLYING OPTIMIZATIONS".center(70))
        print("=" * 70)

        for rec_id in selected_ids:
            rec = next((r for r in self.current_recommendations if r["id"] == rec_id), None)
            if not rec:
                continue

            print(f"\n▶ {rec['title']}")

            # Apply the optimization
            if rec_id == "setup_claude_md":
                self._apply_claude_md_setup()
            elif rec_id == "defer_documentation":
                self._apply_defer_docs()
            elif rec_id == "enable_concise_mode":
                self._apply_concise_mode()
            else:
                print(f"   Instructions:")
                for action in rec.get("actions", []):
                    print(f"   • {action}")

        self.menu.wait_for_enter()

    def _apply_claude_md_setup(self):
        """Help user set up CLAUDE.md."""
        print("   Creating CLAUDE.md template...")

        template = """# Project Context
[Describe your project here]

## Tech Stack
- [List your technologies]

## Coding Preferences
- [Your coding style preferences]

## Optimization Settings
- Defer documentation until code is ready for GitHub
- Keep responses concise and focused
- Skip boilerplate explanations

## Common Tasks
- [List common tasks for this project]
"""

        cwd = Path.cwd()
        claude_md_path = cwd / "CLAUDE.md"

        if claude_md_path.exists():
            print(f"   ℹ CLAUDE.md already exists at {claude_md_path}")
        else:
            try:
                with open(claude_md_path, "w", encoding="utf-8") as f:
                    f.write(template)
                print(f"   ✓ Created CLAUDE.md at {claude_md_path}")
                print("   Edit it to add project-specific context!")
            except Exception as e:
                print(f"   ✗ Error creating CLAUDE.md: {e}")

    def _apply_defer_docs(self):
        """Apply defer documentation setting."""
        print("   Adding defer documentation rule to Memory.md...")

        memory_md_path = Path.home() / ".claude" / "memory" / "MEMORY.md"
        memory_md_path.parent.mkdir(parents=True, exist_ok=True)

        rule = "\n## Documentation Strategy\n- DEFER documentation (README, comments, docstrings) until code is ready to push to GitHub\n"

        try:
            if memory_md_path.exists():
                content = memory_md_path.read_text()
                if "defer documentation" not in content.lower():
                    with open(memory_md_path, "a", encoding="utf-8") as f:
                        f.write(rule)
                    print("   ✓ Added to Memory.md")
                else:
                    print("   ℹ Rule already exists in Memory.md")
            else:
                with open(memory_md_path, "w", encoding="utf-8") as f:
                    f.write("# Token Optimization Memory\n")
                    f.write(rule)
                print("   ✓ Created Memory.md with rule")
        except Exception as e:
            print(f"   ✗ Error updating Memory.md: {e}")

    def _apply_concise_mode(self):
        """Apply concise response mode."""
        print("   Adding concise response preference to Memory.md...")

        memory_md_path = Path.home() / ".claude" / "memory" / "MEMORY.md"
        memory_md_path.parent.mkdir(parents=True, exist_ok=True)

        rule = "\n## Response Style\n- Keep responses concise and focused by default\n- Avoid unnecessary explanations\n"

        try:
            if memory_md_path.exists():
                content = memory_md_path.read_text()
                if "concise" not in content.lower() or "response style" not in content.lower():
                    with open(memory_md_path, "a", encoding="utf-8") as f:
                        f.write(rule)
                    print("   ✓ Added to Memory.md")
                else:
                    print("   ℹ Preference already exists in Memory.md")
            else:
                with open(memory_md_path, "w", encoding="utf-8") as f:
                    f.write("# Token Optimization Memory\n")
                    f.write(rule)
                print("   ✓ Created Memory.md with preference")
        except Exception as e:
            print(f"   ✗ Error updating Memory.md: {e}")

    def _handle_export_stats(self):
        """Handle team stats export."""
        config = self.menu.show_export_menu()

        print("\nExporting your stats...")

        try:
            exporter = TeamExporter(config.get("output_dir"))
            filename = exporter.export_user_stats(
                self.profile.get_current_state(),
                self.current_score_data,
                self.current_rank_data,
                config.get("department", "Engineering")
            )

            print(f"\n✓ Stats exported successfully!")
            print(f"  File: {filename}")
            print(f"  Location: {exporter.output_dir}")
            print("\nShare this file with your team for leaderboard aggregation.")

        except Exception as e:
            print(f"\n✗ Export failed: {e}")

        self.menu.wait_for_enter()

    def _handle_leaderboards(self):
        """Handle leaderboard viewing."""
        while True:
            choice = self.menu.show_leaderboard_menu()

            if choice == "C":
                self._show_company_leaderboard()
            elif choice == "P":
                self._show_project_leaderboard()
            elif choice == "D":
                self._show_department_leaderboard()
            elif choice == "B":
                break
            else:
                print("Invalid choice.")

    def _show_company_leaderboard(self):
        """Show company-wide leaderboard."""
        print("\nLoading company leaderboard...")

        leaderboard = self.leaderboard_generator.generate_company_leaderboard(anonymous=True)

        if leaderboard["total_participants"] == 0:
            print("\nNo team data available yet.")
            print("Export your stats and have team members do the same to build the leaderboard.")
        else:
            formatted = self.leaderboard_generator.format_leaderboard(leaderboard)
            print(formatted)

            # Show user's position
            user_email = self.profile.get_current_state().get("user_email")
            your_rank = self.leaderboard_generator.find_your_rank(user_email)

            if your_rank:
                print(f"\nYour Position:")
                print(f"  Rank: #{your_rank['rank']} of {your_rank['total_participants']}")
                print(f"  Percentile: Top {100 - your_rank['percentile']:.0f}%")

        self.menu.wait_for_enter()

    def _show_project_leaderboard(self):
        """Show project leaderboard."""
        project_name = input("\nEnter project name: ").strip()

        if not project_name:
            print("No project specified.")
            return

        print(f"\nLoading leaderboard for {project_name}...")
        leaderboard = self.leaderboard_generator.generate_project_leaderboard(project_name)

        formatted = self.leaderboard_generator.format_leaderboard(leaderboard)
        print(formatted)

        self.menu.wait_for_enter()

    def _show_department_leaderboard(self):
        """Show department leaderboard."""
        department = input("\nEnter department (default: Engineering): ").strip()
        department = department if department else "Engineering"

        print(f"\nLoading {department} leaderboard...")
        leaderboard = self.leaderboard_generator.generate_department_leaderboard(department)

        formatted = self.leaderboard_generator.format_leaderboard(leaderboard)
        print(formatted)

        self.menu.wait_for_enter()

    def _handle_achievements(self):
        """Show achievements."""
        achievements = self.profile.get_achievements()
        self.menu.show_achievements(achievements)
        self.menu.wait_for_enter()

    def _handle_detailed_recommendations(self):
        """Show detailed recommendations."""
        if not self.current_recommendations:
            print("\nNo recommendations available.")
            return

        self.menu.show_recommendations_detailed(self.current_recommendations)
        self.menu.wait_for_enter()

    def _check_achievements(self, score_data: Dict, rank_data: Dict, delta_data: Optional[Dict]):
        """Check and award achievements."""
        # Existing achievements from basic handler
        if rank_data["name"] == "Pilot" and not any(a["id"] == "first_pilot" for a in self.profile.get_achievements()):
            self.profile.add_achievement("first_pilot", "First Pilot", "Achieved Pilot rank for the first time")

        score = score_data["total_score"]
        if score >= 500 and not any(a["id"] == "halfway_there" for a in self.profile.get_achievements()):
            self.profile.add_achievement("halfway_there", "Halfway There", "Reached 500 points")

        if score >= 1000 and not any(a["id"] == "four_digits" for a in self.profile.get_achievements()):
            self.profile.add_achievement("four_digits", "Four Digits", "Reached 1000+ points (Admiral level)")

        efficiency_pct = score_data["breakdown"]["token_efficiency"].get("improvement_pct", 0)
        if efficiency_pct >= 30 and not any(a["id"] == "efficiency_master" for a in self.profile.get_achievements()):
            self.profile.add_achievement("efficiency_master", "Efficiency Master", "Achieved 30%+ better efficiency than baseline")

        if delta_data and isinstance(delta_data, dict):
            rank_change = delta_data.get("rank_change")
            if rank_change and isinstance(rank_change, dict) and rank_change.get("promoted"):
                promo_id = f"promoted_to_{rank_data['name'].lower()}"
                if not any(a["id"] == promo_id for a in self.profile.get_achievements()):
                    self.profile.add_achievement(promo_id, f"Promoted to {rank_data['name']}", f"Achieved {rank_data['name']} rank")

    def _sync_hero_badges(self):
        """Sync badges with hero.epam.com."""
        if not self.current_rank_data:
            return

        user_email = self.profile.get_current_state().get("user_email")
        current_rank = self.current_rank_data["name"]

        # Sync badges (mock for now)
        result = self.hero_client.sync_badges_with_rank(user_email, current_rank)

        # Silent operation - badges synced in background


def main():
    """Main entry point - fully interactive."""
    import sys
    import io

    # Fix Windows CMD encoding
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Always run in interactive mode
    handler = TokenCraftHandlerFull()
    handler.run_interactive()


if __name__ == "__main__":
    main()
