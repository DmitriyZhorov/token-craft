"""
Report Generator

Generates comprehensive reports for users.
"""

from typing import Dict, List, Optional
from .progress_visualizer import ProgressVisualizer
from .rank_system import SpaceRankSystem
from .delta_calculator import DeltaCalculator
from .cost_alerts import CostAlerts


class ReportGenerator:
    """Generate user reports."""

    def __init__(self):
        """Initialize report generator."""
        self.visualizer = ProgressVisualizer()
        self.cost_alerts = CostAlerts()

    def generate_full_report(
        self,
        profile_data: Dict,
        score_data: Dict,
        rank_data: Dict,
        delta_data: Optional[Dict] = None
    ) -> str:
        """
        Generate complete mission report.

        Args:
            profile_data: User profile data
            score_data: Score breakdown
            rank_data: Current rank info
            delta_data: Delta from previous snapshot (optional)

        Returns:
            Formatted report string
        """
        sections = []

        # Header with rank and progress
        next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])
        header = self.visualizer.create_full_report_header(
            rank_data["name"],
            rank_data["icon"],
            score_data["total_score"],
            next_rank
        )
        sections.append(header)

        # Delta/Progress since last check
        if delta_data:
            delta_section = self._generate_delta_section(delta_data)
            sections.append(delta_section)

        # Score breakdown
        breakdown = self.visualizer.create_category_breakdown(score_data["breakdown"])
        sections.append(breakdown)

        # Stats summary
        stats = self.visualizer.create_stats_summary(profile_data)
        sections.append(stats)

        # Cost tracking
        cost_summary = self._generate_cost_section(profile_data)
        if cost_summary:
            sections.append(cost_summary)

        # Top recommendations
        recommendations = self._generate_recommendations(score_data, profile_data)
        sections.append(recommendations)

        # Achievements
        if profile_data.get("achievements"):
            achievements = self._generate_achievements_section(profile_data["achievements"])
            sections.append(achievements)

        # Footer
        footer = self._generate_footer()
        sections.append(footer)

        return "\n".join(sections)

    def generate_summary(self, profile_data: Dict, score_data: Dict, rank_data: Dict) -> str:
        """
        Generate quick summary.

        Args:
            profile_data: User profile data
            score_data: Score breakdown
            rank_data: Current rank info

        Returns:
            Brief summary string
        """
        lines = []
        lines.append("=" * 50)
        lines.append("TOKEN-CRAFT QUICK SUMMARY".center(50))
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Rank: {rank_data['name']} {rank_data['icon']}")
        lines.append(f"Score: {score_data['total_score']:.0f}/{score_data['max_possible']}")

        next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])
        if next_rank:
            lines.append(f"Next: {next_rank['name']} ({next_rank['points_needed']} points away)")

        lines.append("")
        lines.append(f"Sessions: {profile_data.get('total_sessions', 0)}")
        lines.append(f"Avg tokens/session: {profile_data.get('avg_tokens_per_session', 0):,.0f}")
        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def _generate_delta_section(self, delta_data: Dict) -> str:
        """Generate progress/delta section."""
        lines = []
        lines.append("Progress Since Last Check:")
        lines.append("-" * 70)
        lines.append("")

        summary = DeltaCalculator.get_improvement_summary(delta_data)
        lines.append(f"  {summary}")
        lines.append("")

        # Score change
        score_change = delta_data.get("score_change", 0)
        arrow = self.visualizer.create_trend_indicator(score_change)
        lines.append(f"  Score change: {arrow} {score_change:+.0f} points")

        # Rank change
        rank_change = delta_data.get("rank_change")
        if rank_change:
            if rank_change["promoted"]:
                lines.append(f"  Rank: PROMOTED from {rank_change['from']} to {rank_change['to']}! 🎉")
            else:
                lines.append(f"  Rank: Demoted from {rank_change['from']} to {rank_change['to']}")

        lines.append("")
        return "\n".join(lines)

    def _generate_recommendations(self, score_data: Dict, profile_data: Dict) -> str:
        """Generate personalized recommendations."""
        lines = []
        lines.append("Top Optimization Opportunities:")
        lines.append("=" * 70)
        lines.append("")

        recommendations = self._identify_recommendations(score_data, profile_data)

        for i, rec in enumerate(recommendations[:3], 1):
            box = self.visualizer.create_recommendation_box(
                rec["title"],
                rec["description"],
                rec["impact"]
            )
            lines.append(box)
            if i < len(recommendations[:3]):
                lines.append("")

        return "\n".join(lines)

    def _identify_recommendations(self, score_data: Dict, profile_data: Dict) -> List[Dict]:
        """Identify top recommendations based on scores."""
        recommendations = []
        breakdown = score_data.get("breakdown", {})

        # Token Efficiency
        if breakdown.get("token_efficiency", {}).get("percentage", 0) < 50:
            recommendations.append({
                "title": "Improve Token Efficiency",
                "description": "Your average tokens per session is above baseline. Review sessions to identify optimization opportunities.",
                "impact": "+50-100 points potential",
                "priority": 1
            })

        # Optimization Adoption
        adoption_breakdown = breakdown.get("optimization_adoption", {}).get("breakdown", {})

        if adoption_breakdown.get("defer_docs", {}).get("consistency", 100) < 60:
            recommendations.append({
                "title": "Defer Documentation Until Ready to Push",
                "description": "Avoid writing documentation mid-development. Wait until code is complete and ready for GitHub.",
                "impact": "+30-50 points, saves 2000-3000 tokens per feature",
                "priority": 2
            })

        if adoption_breakdown.get("claude_md", {}).get("with_claude_md", 0) < adoption_breakdown.get("claude_md", {}).get("top_projects", 3):
            recommendations.append({
                "title": "Set Up CLAUDE.md in Your Top Projects",
                "description": "Create CLAUDE.md files in your most-used projects with project-specific context and preferences.",
                "impact": "+35-50 points, saves 1500-2500 tokens per session",
                "priority": 2
            })

        # Self-Sufficiency
        if breakdown.get("self_sufficiency", {}).get("percentage", 0) < 60:
            recommendations.append({
                "title": "Run Simple Commands Directly",
                "description": "Use terminal for git status, ls, cat instead of asking AI. Saves tokens and builds skills.",
                "impact": "+40-60 points, saves 800-1500 tokens per command",
                "priority": 3
            })

        # Context Management
        if adoption_breakdown.get("context_mgmt", {}).get("consistency", 100) < 70:
            recommendations.append({
                "title": "Improve Context Management",
                "description": "Keep sessions focused (5-15 messages). Start new session for new topics to avoid context bloat.",
                "impact": "+25-40 points, prevents token waste",
                "priority": 3
            })

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])

        return recommendations

    def _generate_cost_section(self, profile_data: Dict) -> str:
        """Generate cost tracking section."""
        total_tokens = profile_data.get("total_tokens", 0)
        total_sessions = profile_data.get("total_sessions", 1)
        avg_tokens = profile_data.get("avg_tokens_per_session", 0)

        # Skip if no token data
        if total_tokens == 0:
            return ""

        lines = []
        lines.append("Cost Tracking:")
        lines.append("=" * 70)
        lines.append("")

        # Get cost summary
        cost_summary = self.cost_alerts.format_cost_summary(
            total_tokens,
            avg_tokens,
            total_sessions
        )
        lines.append(cost_summary)
        lines.append("")

        return "\n".join(lines)

    def _generate_achievements_section(self, achievements: List[Dict]) -> str:
        """Generate achievements section."""
        lines = []
        lines.append("Achievements Earned:")
        lines.append("=" * 70)
        lines.append("")

        for achievement in achievements[-5:]:  # Show last 5
            badge = self.visualizer.create_achievement_badge(
                achievement.get("title", "Unknown"),
                achievement.get("description", ""),
                achievement.get("earned_at", "Unknown date")
            )
            lines.append(badge)
            lines.append("")

        if len(achievements) > 5:
            lines.append(f"... and {len(achievements) - 5} more achievements")
            lines.append("")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        lines = []
        lines.append("=" * 70)
        lines.append("Run '/token-craft' anytime to check your progress!".center(70))
        lines.append("=" * 70)

        return "\n".join(lines)

    def generate_leaderboard_report(self, leaderboard_data: Dict) -> str:
        """
        Generate leaderboard report.

        Args:
            leaderboard_data: Leaderboard data

        Returns:
            Formatted leaderboard
        """
        lines = []
        lines.append("=" * 70)
        lines.append("COMPANY LEADERBOARD".center(70))
        lines.append("=" * 70)
        lines.append("")

        rankings = leaderboard_data.get("rankings", [])

        lines.append(f"{'Rank':<6} {'Name':<25} {'Level':<15} {'Score':<10}")
        lines.append("-" * 70)

        for entry in rankings[:25]:  # Top 25
            rank = entry.get("rank", "?")
            name = entry.get("name", "Unknown")[:24]
            level = entry.get("rank_title", "Unknown")
            score = entry.get("score", 0)

            lines.append(f"#{rank:<5} {name:<25} {level:<15} {score:<10.0f}")

        lines.append("")
        lines.append(f"Your rank: #{leaderboard_data.get('your_rank', '?')}")
        lines.append(f"Total participants: {leaderboard_data.get('total_participants', 0)}")
        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)
