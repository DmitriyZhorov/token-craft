"""
Report Generator

Generates comprehensive reports for users.
"""

from typing import Dict, List, Optional
from .progress_visualizer import ProgressVisualizer
from .rank_system import SpaceRankSystem
from .delta_calculator import DeltaCalculator
from .cost_alerts import CostAlerts
from .recommendation_engine import RecommendationEngine

try:
    from .insights_engine import InsightsEngine
    _HAS_INSIGHTS = True
except ImportError:
    _HAS_INSIGHTS = False


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
        delta_data: Optional[Dict] = None,
        history_data: Optional[List] = None
    ) -> str:
        """
        Generate complete mission report.

        Args:
            profile_data: User profile data
            score_data: Score breakdown
            rank_data: Current rank info
            delta_data: Delta from previous snapshot (optional)
            history_data: Parsed history.jsonl data (optional, for insights)

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

        # Waste detection (NEW v2.0)
        waste_section = self._generate_waste_detection_section(score_data)
        if waste_section:
            sections.append(waste_section)

        # Prescriptive insights (NEW v2.0)
        insights_section = self._generate_prescriptive_insights_section(score_data, history_data)
        if insights_section:
            sections.append(insights_section)

        # Top recommendations
        recommendations = self._generate_recommendations(score_data, profile_data, history_data)
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

    def _generate_recommendations(self, score_data: Dict, profile_data: Dict,
                                    history_data: Optional[List] = None) -> str:
        """Generate personalized recommendations using RecommendationEngine."""
        lines = []
        lines.append("Top Optimization Opportunities:")
        lines.append("=" * 70)

        try:
            recommendations = RecommendationEngine.generate_recommendations(
                score_data, profile_data, history_data
            )

            if not recommendations:
                recommendations = self._identify_recommendations(score_data, profile_data)
                # Fall back to old-style box format
                for i, rec in enumerate(recommendations[:3], 1):
                    box = self.visualizer.create_recommendation_box(
                        rec["title"], rec["description"], rec["impact"]
                    )
                    lines.append(box)
                    if i < len(recommendations[:3]):
                        lines.append("")
                return "\n".join(lines)

            # Format using RecommendationEngine's prescriptive style
            for i, rec in enumerate(recommendations[:5], 1):
                formatted = RecommendationEngine.format_recommendation(rec, i)
                lines.append(formatted)

            # Next Rank Path section
            next_rank = SpaceRankSystem.get_next_rank(score_data["total_score"])
            if next_rank and recommendations:
                path_recs = RecommendationEngine.get_next_rank_recommendations(
                    int(score_data["total_score"]),
                    next_rank["min"],
                    recommendations
                )
                total_potential = RecommendationEngine.calculate_total_potential(path_recs)

                lines.append("")
                lines.append(f"Path to {next_rank['name']} ({next_rank['points_needed']} pts needed):")
                lines.append("-" * 70)
                for rec in path_recs:
                    pts = rec.get("potential_points", 0)
                    lines.append(f"  + {rec['title']}: ~{pts} pts")
                lines.append(f"  Total potential: ~{total_potential} pts")

        except Exception:
            # Fallback to old-style recommendations
            recommendations = self._identify_recommendations(score_data, profile_data)
            for i, rec in enumerate(recommendations[:3], 1):
                box = self.visualizer.create_recommendation_box(
                    rec["title"], rec["description"], rec["impact"]
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

    def _generate_waste_detection_section(self, score_data: Dict) -> str:
        """
        Generate waste detection section showing actual token waste patterns.

        Args:
            score_data: Score breakdown with waste_awareness data

        Returns:
            Formatted waste detection section (or empty string if no waste data)
        """
        breakdown = score_data.get("breakdown", {})
        waste_data = breakdown.get("waste_awareness", {})

        if not waste_data or waste_data.get("total_waste_tokens", 0) == 0:
            return ""  # No waste detected

        lines = []
        lines.append("Token Waste Analysis:")
        lines.append("=" * 70)
        lines.append("")

        total_waste = waste_data.get("total_waste_tokens", 0)
        daily_waste = waste_data.get("daily_waste_rate", 0)
        patterns = waste_data.get("waste_patterns", {})

        # Summary
        lines.append(f"Total waste detected: {total_waste:,} tokens")
        lines.append(f"Daily waste rate: ~{daily_waste:,.0f} tokens/day")
        lines.append("")

        if patterns:
            lines.append("Waste Patterns Found:")
            lines.append("-" * 70)
            lines.append("")

            # Priority order
            priority_order = ['repeated_context', 'verbose_prompts', 'redundant_file_reads', 'prompt_bloat']

            for pattern_type in priority_order:
                if pattern_type not in patterns:
                    continue

                pattern = patterns[pattern_type]
                waste_tokens = pattern.get('waste_tokens', 0)

                if waste_tokens == 0:
                    continue

                # Pattern header
                pattern_names = {
                    'repeated_context': 'REPEATED CONTEXT',
                    'verbose_prompts': 'VERBOSE PROMPTS',
                    'redundant_file_reads': 'REDUNDANT FILE READS',
                    'prompt_bloat': 'PROMPT BLOAT'
                }
                lines.append(f"  {pattern_names.get(pattern_type, pattern_type.upper())}")
                lines.append(f"  Waste: {waste_tokens:,} tokens")

                # Examples
                examples = pattern.get('examples', [])
                if examples and len(examples) > 0:
                    lines.append("  Examples:")
                    for example in examples[:2]:  # Show max 2 examples
                        if isinstance(example, dict):
                            # Verbose prompts format
                            verbose = example.get('verbose', '')
                            waste = example.get('waste_tokens', 0)
                            lines.append(f"    • {verbose} (wasted {waste} tokens)")
                        elif isinstance(example, str):
                            # String format
                            lines.append(f"    • {example}")

                # Recommendation
                recommendation = pattern.get('recommendation', '')
                if recommendation:
                    lines.append(f"  Fix: {recommendation}")

                lines.append("")

        # Overall recommendation
        if total_waste > 30000:
            priority = "HIGH PRIORITY"
        elif total_waste > 10000:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "LOW PRIORITY"

        lines.append(f"Priority: {priority}")
        lines.append("")

        return "\n".join(lines)

    def _generate_prescriptive_insights_section(self, score_data: Dict,
                                                  history_data: Optional[List] = None) -> str:
        """
        Generate prescriptive insights section.

        Args:
            score_data: Score breakdown
            history_data: Parsed history.jsonl data

        Returns:
            Formatted insights section (or empty string if no insights engine)
        """
        if not _HAS_INSIGHTS or not history_data:
            return ""

        try:
            engine = InsightsEngine(score_data, history_data)
            insights = engine.generate_insights()
            if insights:
                return engine.format_insights_section(insights)
        except Exception:
            pass

        return ""

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
