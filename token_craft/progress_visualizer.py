"""
Progress Visualization

Creates ASCII art progress bars, badges, and visual indicators.
"""

from typing import Dict


class ProgressVisualizer:
    """Create visual representations of progress."""

    @staticmethod
    def create_progress_bar(current: int, maximum: int, width: int = 50,
                          filled_char: str = "█", empty_char: str = "░") -> str:
        """
        Create ASCII progress bar.

        Args:
            current: Current value
            maximum: Maximum value
            width: Width in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion

        Returns:
            Progress bar string
        """
        if maximum == 0:
            return empty_char * width

        percentage = min(1.0, current / maximum)
        filled = int(percentage * width)
        empty = width - filled

        return f"{filled_char * filled}{empty_char * empty}"

    @staticmethod
    def create_percentage_bar(percentage: float, width: int = 50) -> str:
        """
        Create progress bar from percentage.

        Args:
            percentage: Percentage value (0-100)
            width: Width in characters

        Returns:
            Progress bar string
        """
        percentage = max(0, min(100, percentage))
        return ProgressVisualizer.create_progress_bar(int(percentage), 100, width)

    @staticmethod
    def create_rank_badge(rank_name: str, icon: str = "") -> str:
        """
        Create ASCII art rank badge.

        Args:
            rank_name: Name of the rank
            icon: Optional icon character

        Returns:
            ASCII art badge
        """
        name_upper = rank_name.upper()
        border_len = len(name_upper) + 6

        if icon:
            header = f"  {icon}  {name_upper}  {icon}"
        else:
            header = f"  {name_upper}"

        border = "=" * border_len

        return f"\n{border}\n{header}\n{border}"

    @staticmethod
    def create_score_display(category: str, score: float, max_score: float, width: int = 30) -> str:
        """
        Create single line score display with bar.

        Args:
            category: Category name
            score: Current score
            max_score: Maximum possible score
            width: Progress bar width

        Returns:
            Formatted score line
        """
        bar = ProgressVisualizer.create_progress_bar(int(score), int(max_score), width)
        percentage = (score / max_score * 100) if max_score > 0 else 0

        # Pad category name to 22 characters
        category_display = category.replace("_", " ").title()
        category_padded = category_display.ljust(22)

        return f"{category_padded} [{bar}] {score:.0f}/{max_score:.0f} ({percentage:.0f}%)"

    @staticmethod
    def create_trend_indicator(value: float) -> str:
        """
        Create trend arrow indicator.

        Args:
            value: Delta value

        Returns:
            Arrow character (↑ ↓ →)
        """
        if value > 0:
            return "↑"
        elif value < 0:
            return "↓"
        else:
            return "→"

    @staticmethod
    def create_full_report_header(rank_name: str, icon: str, score: int, next_rank: Dict = None) -> str:
        """
        Create full report header with rank and progress.

        Args:
            rank_name: Current rank name
            icon: Rank icon
            score: Current score
            next_rank: Next rank info (optional)

        Returns:
            Formatted header
        """
        lines = []
        lines.append("=" * 70)
        lines.append("TOKEN-CRAFT: YOUR SPACE MISSION REPORT".center(70))
        lines.append("=" * 70)
        lines.append("")

        # Current rank
        if next_rank:
            bar = ProgressVisualizer.create_progress_bar(score, next_rank["min"], 40)
            lines.append(f"Current Rank: [{rank_name.upper()}] {bar} {score}/{next_rank['min']}")
            lines.append(f"Next Rank:    [{next_rank['name'].upper()}] in {next_rank['points_needed']} points")
        else:
            lines.append(f"Current Rank: [{rank_name.upper()}] {icon} (MAX RANK ACHIEVED!)")
            lines.append(f"Current Score: {score} points")

        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def create_category_breakdown(scores_breakdown: Dict) -> str:
        """
        Create category score breakdown display.

        Args:
            scores_breakdown: Breakdown from scoring engine

        Returns:
            Formatted breakdown
        """
        lines = []
        lines.append("Score Breakdown:")
        lines.append("-" * 70)

        categories = [
            ("token_efficiency", "Token Efficiency"),
            ("optimization_adoption", "Optimization Adoption"),
            ("self_sufficiency", "Self-Sufficiency"),
            ("improvement_trend", "Improvement Trend"),
            ("best_practices", "Best Practices"),
            ("cache_effectiveness", "Cache Effectiveness"),
            ("tool_efficiency", "Tool Efficiency"),
            ("cost_efficiency", "Cost Efficiency"),
            ("session_focus", "Session Focus"),
            ("learning_growth", "Learning & Growth")
        ]

        for cat_key, cat_name in categories:
            if cat_key in scores_breakdown:
                cat_data = scores_breakdown[cat_key]
                score = cat_data.get("score", 0)
                max_score = cat_data.get("max_score", 0)

                line = ProgressVisualizer.create_score_display(cat_name, score, max_score, 30)
                lines.append(line)

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def create_stats_summary(profile_data: Dict) -> str:
        """
        Create stats summary section.

        Args:
            profile_data: User profile data

        Returns:
            Formatted stats
        """
        lines = []
        lines.append("Your Mission Stats:")
        lines.append("-" * 70)

        stats = [
            ("Total Sessions", profile_data.get("total_sessions", 0)),
            ("Total Messages", profile_data.get("total_messages", 0)),
            ("Total Tokens", f"{profile_data.get('total_tokens', 0):,}"),
            ("Avg Tokens/Session", f"{profile_data.get('avg_tokens_per_session', 0):,.0f}"),
            ("Current Rank", profile_data.get("current_rank", "Unknown")),
            ("Achievements Earned", len(profile_data.get("achievements", [])))
        ]

        for label, value in stats:
            lines.append(f"  {label:.<30} {value}")

        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def create_leaderboard_position(rank: int, total: int, percentile: float) -> str:
        """
        Create leaderboard position display.

        Args:
            rank: User's rank position
            total: Total participants
            percentile: Percentile (0-100)

        Returns:
            Formatted position
        """
        lines = []
        lines.append("Leaderboard Position:")
        lines.append("-" * 70)
        lines.append(f"  Company-wide: #{rank} of {total} (top {100-percentile:.0f}%)")

        # Visual indicator
        if percentile >= 90:
            badge = "[ELITE - TOP 10%]"
        elif percentile >= 75:
            badge = "[ADVANCED - TOP 25%]"
        elif percentile >= 50:
            badge = "[PROFICIENT - TOP 50%]"
        else:
            badge = "[LEARNING]"

        lines.append(f"  Status: {badge}")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def create_recommendation_box(title: str, description: str, impact: str) -> str:
        """
        Create a recommendation box.

        Args:
            title: Recommendation title
            description: Description text
            impact: Expected impact

        Returns:
            Formatted box
        """
        lines = []
        lines.append("┌" + "─" * 68 + "┐")
        lines.append(f"│ ► {title:<65}│")
        lines.append("├" + "─" * 68 + "┤")

        # Wrap description
        desc_lines = ProgressVisualizer._wrap_text(description, 64)
        for line in desc_lines:
            lines.append(f"│   {line:<65}│")

        lines.append("├" + "─" * 68 + "┤")
        lines.append(f"│   Impact: {impact:<58}│")
        lines.append("└" + "─" * 68 + "┘")

        return "\n".join(lines)

    @staticmethod
    def _wrap_text(text: str, width: int) -> list:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            if current_length + word_length + len(current_line) <= width:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    @staticmethod
    def create_achievement_badge(title: str, description: str, earned_at: str) -> str:
        """
        Create achievement badge display.

        Args:
            title: Achievement title
            description: Achievement description
            earned_at: Date earned

        Returns:
            Formatted badge
        """
        lines = []
        lines.append("🏆 " + "=" * 60)
        lines.append(f"   {title}")
        lines.append("   " + "-" * 60)
        lines.append(f"   {description}")
        lines.append(f"   Earned: {earned_at}")
        lines.append("   " + "=" * 60)

        return "\n".join(lines)
