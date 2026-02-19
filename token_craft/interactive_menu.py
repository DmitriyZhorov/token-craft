"""
Interactive Menu System

Provides interactive menu for Token-Craft operations.
"""

from typing import Callable, Dict, List, Optional


class InteractiveMenu:
    """Interactive menu system for Token-Craft."""

    @staticmethod
    def show_main_menu() -> str:
        """
        Show main menu and get user choice.

        Returns:
            User's choice
        """
        print("\n" + "=" * 70)
        print("WHAT WOULD YOU LIKE TO DO?".center(70))
        print("=" * 70)
        print()
        print("  [A] Apply recommended optimizations")
        print("  [E] Export stats for team analysis")
        print("  [L] View leaderboards")
        print("  [H] View achievements history")
        print("  [R] Show detailed recommendations")
        print("  [S] Show full report again")
        print("  [Q] Quit")
        print()

        choice = input("Your choice: ").strip().upper()
        return choice

    @staticmethod
    def show_optimization_menu(recommendations: List[Dict]) -> List[str]:
        """
        Show optimization options and let user select which to apply.

        Args:
            recommendations: List of recommendations

        Returns:
            List of selected recommendation IDs
        """
        print("\n" + "=" * 70)
        print("OPTIMIZATION RECOMMENDATIONS".center(70))
        print("=" * 70)
        print()

        if not recommendations:
            print("No recommendations available. You're doing great!")
            return []

        print("Select optimizations to apply (comma-separated numbers, or 'all'):\n")

        for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
            impact_points = rec.get("potential_points", 0)
            print(f"  [{i}] {rec['title']}")
            print(f"      Impact: {rec['impact']} (+{impact_points} points potential)")
            print()

        choice = input("Your choice (e.g., '1,3' or 'all' or 'none'): ").strip().lower()

        if choice == "none" or choice == "":
            return []

        if choice == "all":
            return [rec["id"] for rec in recommendations[:5]]

        # Parse selection
        try:
            selected_indices = [int(x.strip()) for x in choice.split(",")]
            selected_ids = []

            for idx in selected_indices:
                if 1 <= idx <= min(5, len(recommendations)):
                    selected_ids.append(recommendations[idx - 1]["id"])

            return selected_ids

        except ValueError:
            print("Invalid selection.")
            return []

    @staticmethod
    def show_leaderboard_menu() -> str:
        """
        Show leaderboard options.

        Returns:
            Leaderboard type choice
        """
        print("\n" + "=" * 70)
        print("LEADERBOARDS".center(70))
        print("=" * 70)
        print()
        print("  [C] Company-wide leaderboard")
        print("  [P] Project leaderboard")
        print("  [D] Department leaderboard")
        print("  [B] Back to main menu")
        print()

        choice = input("Your choice: ").strip().upper()
        return choice

    @staticmethod
    def show_export_menu() -> Dict:
        """
        Show export options and get configuration.

        Returns:
            Export configuration
        """
        print("\n" + "=" * 70)
        print("EXPORT STATS FOR TEAM".center(70))
        print("=" * 70)
        print()

        config = {}

        # Output directory
        print("Where should stats be exported?")
        print("(Default: ~/.claude/token-craft/team-exports)")
        output_dir = input("Output directory (or press Enter for default): ").strip()

        if output_dir:
            config["output_dir"] = output_dir
        else:
            config["output_dir"] = None

        # Department
        print("\nWhat is your department?")
        department = input("Department (default: Engineering): ").strip()
        config["department"] = department if department else "Engineering"

        return config

    @staticmethod
    def confirm_action(message: str) -> bool:
        """
        Ask user to confirm an action.

        Args:
            message: Confirmation message

        Returns:
            True if confirmed
        """
        response = input(f"\n{message} (y/n): ").strip().lower()
        return response in ["y", "yes"]

    @staticmethod
    def show_achievements(achievements: List[Dict]):
        """
        Display achievements.

        Args:
            achievements: List of achievements
        """
        print("\n" + "=" * 70)
        print("YOUR ACHIEVEMENTS".center(70))
        print("=" * 70)
        print()

        if not achievements:
            print("No achievements yet. Keep optimizing!")
            return

        for achievement in achievements:
            print(f"🏆 {achievement.get('title', 'Unknown')}")
            print(f"   {achievement.get('description', '')}")
            print(f"   Earned: {achievement.get('earned_at', 'Unknown date')}")
            print()

    @staticmethod
    def show_recommendations_detailed(recommendations: List[Dict]):
        """
        Show detailed recommendations with actions.

        Args:
            recommendations: List of recommendations
        """
        print("\n" + "=" * 70)
        print("DETAILED RECOMMENDATIONS".center(70))
        print("=" * 70)

        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['title']}")
            print("   " + "-" * 66)
            print(f"   Category: {rec['category'].replace('_', ' ').title()}")
            print(f"   Priority: {rec['priority']}")
            print()
            print(f"   {rec['description']}")
            print()
            print(f"   Impact: {rec['impact']}")
            print(f"   Potential points: +{rec.get('potential_points', 0)}")

            if rec.get("actions"):
                print()
                print("   Actions to take:")
                for action in rec["actions"]:
                    print(f"   • {action}")

            print()

    @staticmethod
    def wait_for_enter(message: str = "Press Enter to continue..."):
        """Wait for user to press Enter."""
        input(f"\n{message}")

    @staticmethod
    def show_progress_bar(current: int, total: int, width: int = 50) -> str:
        """
        Create progress bar.

        Args:
            current: Current value
            total: Total value
            width: Bar width

        Returns:
            Progress bar string
        """
        if total == 0:
            return "░" * width

        percentage = min(1.0, current / total)
        filled = int(percentage * width)
        empty = width - filled

        return "█" * filled + "░" * empty
