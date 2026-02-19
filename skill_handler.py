"""
Token-Craft Skill Handler

Main entry point for the /token-craft skill.
Supports v3.0 gamification system with:
- 10 ranks with exponential progression
- Difficulty scaling by rank
- Streak multipliers (1.0x-1.25x)
- Combo bonuses (25-150 pts)
- 25+ achievements
- Time-based mechanics (recency, decay, seasonal)
- Regression detection
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
from token_craft.difficulty_modifier import DifficultyModifier
from token_craft.streak_system import StreakSystem
from token_craft.achievement_engine import AchievementEngine
from token_craft.time_based_mechanics import TimeBasedMechanics


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

    def calculate_scores(self, history_data: list, stats_data: Dict, previous_snapshot: Optional[Dict] = None, user_rank: int = 1) -> Dict:
        """
        Calculate user scores using v3.0 system.

        Args:
            history_data: Parsed history.jsonl
            stats_data: Parsed stats-cache.json
            previous_snapshot: Previous snapshot for trend calculation
            user_rank: Current user rank (1-10) for difficulty scaling

        Returns:
            Score data with v3.0 metrics
        """
        scorer = TokenCraftScorer(history_data, stats_data, user_rank=user_rank, user_profile=self.profile.get_current_state())
        score_data = scorer.calculate_total_score(previous_snapshot)

        return score_data

    def run(self, mode: str = "full") -> str:
        """
        Run the Token-Craft v3.0 analysis.

        Args:
            mode: 'full', 'summary', 'quick', or 'v3'

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

            # Get current rank (for difficulty scaling in v3.0)
            previous_profile = None
            if previous_snapshot and isinstance(previous_snapshot, dict):
                previous_profile = previous_snapshot.get("profile")

            current_rank_data = SpaceRankSystem.get_rank(
                previous_profile.get("total_score", 0) if previous_profile else 0
            )
            current_rank = current_rank_data.get("rank", 1)

            # Calculate scores (with v3.0 difficulty scaling)
            print("Calculating your scores (v3.0 system)...")
            score_data = self.calculate_scores(
                history_data,
                stats_data,
                previous_profile,
                user_rank=current_rank
            )

            # Get new rank based on v3.0 score
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
            elif mode == "v3":
                report = self._generate_v3_full_report(score_data, rank_data, delta_data)
            else:  # full
                report = self._generate_v3_full_report(score_data, rank_data, delta_data)

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

    def _generate_quick_status(self, score_data: Dict, rank_data: Dict) -> str:
        """Generate quick one-line status."""
        next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])

        status = f"{rank_data['icon']} {rank_data['name']} - {score_data['total_score']:.0f} points"

        if next_rank:
            status += f" ({next_rank['points_needed']} to {next_rank['name']})"

        return status

    def _generate_v3_full_report(self, score_data: Dict, rank_data: Dict, delta_data: Optional[Dict]) -> str:
        """Generate comprehensive v3.0 report with all gamification features."""
        lines = []

        # Header
        lines.append("\n" + "="*70)
        lines.append("          ⚡ TOKEN-CRAFT v3.0 - GAMIFIED OPTIMIZATION REPORT")
        lines.append("="*70)

        # Rank and Score
        lines.append(f"\n{rank_data['icon']} RANK: {rank_data['name'].upper()}")
        lines.append(f"   📊 Score: {score_data['total_score']:.0f} / {score_data['max_achievable']:.0f} pts ({score_data['percentage']:.1f}%)")

        # Breakdown
        lines.append("\n" + "-"*70)
        lines.append("📈 SCORING BREAKDOWN (10 Categories)")
        lines.append("-"*70)

        breakdown = score_data["breakdown"]
        for category, data in breakdown.items():
            if isinstance(data, dict):
                score = data.get("score", 0)
                max_pts = data.get("max_points", 100)
                pct = (score / max_pts * 100) if max_pts > 0 else 0
                label = category.replace("_", " ").title()
                lines.append(f"  {label:.<40} {score:>6.0f} / {max_pts:<6.0f} ({pct:>5.1f}%)")

        lines.append(f"  {'Base Score':.<40} {score_data['base_score']:>6.0f}")

        # Bonuses
        bonuses = score_data.get("bonuses", {})
        if bonuses:
            lines.append("\n" + "-"*70)
            lines.append("🎁 BONUSES & MULTIPLIERS")
            lines.append("-"*70)

            # Streak
            streak = bonuses.get("streak", {})
            if streak:
                lines.append(f"  Streak (Length: {streak.get('streak_length', 0)})")
                lines.append(f"    Multiplier: {streak.get('multiplier', 1.0)}x")
                lines.append(f"    Bonus Points: +{streak.get('bonus_points', 0):.0f}")

            # Combo
            combo = bonuses.get("combo", {})
            if combo:
                lines.append(f"  Combo ({combo.get('tier', 'None')})")
                lines.append(f"    Categories: {combo.get('excellent_categories', 0)} > 80%")
                lines.append(f"    Bonus Points: +{combo.get('bonus_points', 0):.0f}")

            # Time Modifiers
            time_mod = bonuses.get("time_modifiers", {})
            if time_mod:
                lines.append(f"  Time Modifiers")
                lines.append(f"    Recency: {time_mod.get('recency_multiplier', 1.0)}x")
                if time_mod.get('decay_multiplier', 1.0) < 1.0:
                    lines.append(f"    Decay: {time_mod.get('decay_multiplier', 1.0)}x")

            # Achievements
            ach = bonuses.get("achievements", {})
            if ach and ach.get("newly_unlocked", 0) > 0:
                lines.append(f"  🏆 NEW ACHIEVEMENTS: +{ach.get('newly_unlocked', 0)}")

        # Difficulty Info
        diff = score_data.get("difficulty_info", {})
        if diff:
            lines.append("\n" + "-"*70)
            lines.append("⚙️  DIFFICULTY LEVEL (Rank-Based)")
            lines.append("-"*70)
            lines.append(f"  Current Rank: {diff.get('rank_name', 'Unknown')}")
            lines.append(f"  Difficulty: {diff.get('difficulty_label', 'Standard')}")
            lines.append(f"  Token Efficiency Baseline: {diff.get('token_efficiency_baseline', 'N/A'):,} tokens/session")

        # Regression Analysis
        regression = score_data.get("regression_analysis", {})
        if regression and regression.get("has_regressed", False):
            lines.append("\n" + "-"*70)
            lines.append("⚠️  PERFORMANCE REGRESSION DETECTED")
            lines.append("-"*70)
            lines.append(f"  Severity: {regression.get('severity', 'unknown').upper()}")
            if regression.get("efficiency", {}).get("has_regressed"):
                lines.append(f"  Efficiency: {regression['efficiency'].get('efficiency_drop_pct', 0):.1f}% drop")
            if regression.get("score", {}).get("has_regressed"):
                lines.append(f"  Score Trend: {regression['score'].get('score_drop_pct', 0):.1f}% drop")
            lines.append(f"  Action: {regression.get('recommendation', 'Continue improving')}")

        # Newly Unlocked Achievements
        new_achievements = score_data.get("newly_unlocked_achievements", [])
        if new_achievements:
            lines.append("\n" + "-"*70)
            lines.append("🎯 NEWLY UNLOCKED ACHIEVEMENTS")
            lines.append("-"*70)
            for ach in new_achievements:
                lines.append(f"  ✓ {ach.get('name', 'Unknown')} (+{ach.get('points', 0)} pts)")

        # Next Rank
        next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])
        if next_rank:
            lines.append("\n" + "-"*70)
            lines.append("🚀 NEXT MILESTONE")
            lines.append("-"*70)
            lines.append(f"  Rank: {next_rank['icon']} {next_rank['name']}")
            lines.append(f"  Points Needed: {next_rank['points_needed']:.0f}")

        # Footer
        lines.append("\n" + "="*70)
        lines.append("Version 3.0 | Difficulty scales with rank | 10 ranks | Max 2300+ pts")
        lines.append("="*70 + "\n")

        return "\n".join(lines)


def show_menu():
    """Show interactive menu and get user choice."""
    print("\n" + "="*70)
    print("              TOKEN-CRAFT v3.0 - Interactive Menu")
    print("="*70)
    print("\nHow would you like to view your report?\n")
    print("  [1] Full Report v3.0 (comprehensive with v3.0 features)")
    print("  [2] Quick Summary (rank and score overview)")
    print("  [3] One-Line Status (just rank and score)")
    print("  [4] JSON Output (for programmatic access)")
    print("  [5] Legacy Report (original format)")
    print("  [Q] Quit")
    print("\n" + "="*70)

    while True:
        choice = input("\nYour choice: ").strip().upper()

        if choice in ['1', 'FULL', 'F', 'V3']:
            return 'v3'
        elif choice in ['2', 'SUMMARY', 'S']:
            return 'summary'
        elif choice in ['3', 'QUICK', 'O', 'ONE']:
            return 'quick'
        elif choice in ['4', 'JSON', 'J']:
            return 'json'
        elif choice in ['5', 'LEGACY', 'L']:
            return 'full'
        elif choice in ['QUIT', 'EXIT', 'Q']:
            return None
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, or Q.")


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
        print("\n👋 Thanks for using Token-Craft v3.0!")
        return

    # Run analysis
    handler = TokenCraftHandler()

    if mode == 'json':
        report = handler.run(mode='v3')
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
