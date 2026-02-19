"""
Recommendation Engine

Generates personalized optimization recommendations.
"""

from typing import List, Dict


class RecommendationEngine:
    """Generate personalized recommendations."""

    @staticmethod
    def generate_recommendations(score_data: Dict, profile_data: Dict) -> List[Dict]:
        """
        Generate prioritized recommendations.

        Args:
            score_data: Score breakdown
            profile_data: User profile data

        Returns:
            List of recommendations sorted by priority
        """
        recommendations = []
        breakdown = score_data.get("breakdown", {})

        # 1. Token Efficiency
        efficiency = breakdown.get("token_efficiency", {})
        if efficiency.get("percentage", 0) < 50:
            recommendations.append({
                "id": "improve_efficiency",
                "priority": 1,
                "category": "token_efficiency",
                "title": "Improve Token Efficiency",
                "description": "Your average tokens per session is above baseline. Review your recent sessions to identify patterns and opportunities for optimization.",
                "impact": "+50-100 points",
                "potential_points": 80,
                "actions": [
                    "Review longest sessions for optimization opportunities",
                    "Use more focused, specific prompts",
                    "Break large tasks into smaller sessions"
                ]
            })

        # 2. Defer Documentation
        adoption = breakdown.get("optimization_adoption", {})
        defer_docs = adoption.get("breakdown", {}).get("defer_docs", {})
        if defer_docs.get("consistency", 100) < 60:
            recommendations.append({
                "id": "defer_documentation",
                "priority": 2,
                "category": "optimization_adoption",
                "title": "Defer Documentation Until Code is Ready",
                "description": "Avoid writing README files, comments, or docstrings while actively developing. Wait until your code is tested and ready to push to GitHub.",
                "impact": "+30-50 points, saves 2000-3000 tokens per feature",
                "potential_points": 40,
                "actions": [
                    "Skip documentation during initial development",
                    "Add 'skip docs for now' to your prompts",
                    "Write all documentation in one pass at the end"
                ]
            })

        # 3. CLAUDE.md Setup
        claude_md = adoption.get("breakdown", {}).get("claude_md", {})
        if claude_md.get("with_claude_md", 0) < claude_md.get("top_projects", 3):
            missing_count = claude_md.get("top_projects", 3) - claude_md.get("with_claude_md", 0)
            recommendations.append({
                "id": "setup_claude_md",
                "priority": 2,
                "category": "optimization_adoption",
                "title": f"Set Up CLAUDE.md in {missing_count} More Project(s)",
                "description": "Create CLAUDE.md files in your most-used projects. Include project context, tech stack, coding preferences, and optimization rules.",
                "impact": f"+{missing_count * 15}-{missing_count * 20} points, saves 1500-2500 tokens per session",
                "potential_points": missing_count * 17,
                "actions": [
                    "Create CLAUDE.md in project root",
                    "Add project overview and tech stack",
                    "Include your optimization preferences"
                ]
            })

        # 4. Self-Sufficiency
        self_suff = breakdown.get("self_sufficiency", {})
        if self_suff.get("percentage", 0) < 60:
            current_rate = self_suff.get("rate", 0)
            target_rate = 0.75
            potential_gain = (target_rate - current_rate) * 200

            recommendations.append({
                "id": "increase_self_sufficiency",
                "priority": 3,
                "category": "self_sufficiency",
                "title": "Run Commands Directly in Terminal",
                "description": "Instead of asking AI to show you git status, ls, or cat files, run these commands directly in your terminal. It's faster and saves tokens.",
                "impact": f"+{int(potential_gain)} points, saves 800-1500 tokens per command",
                "potential_points": int(potential_gain),
                "actions": [
                    "Use 'git status' instead of asking AI",
                    "Use 'ls' instead of asking AI to list files",
                    "Use 'cat file.txt' instead of asking AI to show contents",
                    "Only ask AI for help with complex commands"
                ]
            })

        # 5. Context Management
        context = adoption.get("breakdown", {}).get("context_mgmt", {})
        avg_messages = context.get("avg_messages_per_session", 10)
        if avg_messages > 20:
            recommendations.append({
                "id": "improve_context_management",
                "priority": 4,
                "category": "optimization_adoption",
                "title": "Keep Sessions Focused (5-15 Messages)",
                "description": f"Your sessions average {avg_messages:.0f} messages. Long sessions cause context bloat and verbose responses. Start a new session when switching topics.",
                "impact": "+25-40 points, reduces token waste",
                "potential_points": 30,
                "actions": [
                    "Start new session for new topics",
                    "Aim for 5-15 messages per session",
                    "Complete one task per session"
                ]
            })

        # 6. Concise Mode
        concise = adoption.get("breakdown", {}).get("concise_mode", {})
        if not concise.get("preference_set", False):
            recommendations.append({
                "id": "enable_concise_mode",
                "priority": 5,
                "category": "optimization_adoption",
                "title": "Enable Concise Response Mode",
                "description": "Add preference for brief, focused responses to your Memory.md or CLAUDE.md files. This reduces output tokens significantly.",
                "impact": "+20-30 points, saves 500-1000 tokens per response",
                "potential_points": 25,
                "actions": [
                    "Add 'Keep responses concise' to Memory.md",
                    "Use phrases like 'briefly' or 'in summary'",
                    "Ask follow-up questions for details instead of getting everything upfront"
                ]
            })

        # 7. Improvement Trend
        trend = breakdown.get("improvement_trend", {})
        if trend.get("status") in ["maintaining", "slight_degradation", "significant_degradation"]:
            recommendations.append({
                "id": "reverse_degradation",
                "priority": 1,  # High priority if degrading
                "category": "improvement_trend",
                "title": "Reverse Recent Degradation",
                "description": "Your token efficiency has declined recently. Review what changed in your workflow and re-apply optimization practices.",
                "impact": "+50-150 points (restore previous level)",
                "potential_points": 100,
                "actions": [
                    "Review recent sessions for inefficiencies",
                    "Re-read optimization best practices",
                    "Check if you stopped using CLAUDE.md or defer docs"
                ]
            })

        # Sort by priority (lower number = higher priority)
        recommendations.sort(key=lambda x: (x["priority"], -x["potential_points"]))

        return recommendations

    @staticmethod
    def format_recommendation(rec: Dict, index: int = 1) -> str:
        """
        Format single recommendation for display.

        Args:
            rec: Recommendation dict
            index: Index number

        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"\n{index}. {rec['title']}")
        lines.append("   " + "-" * 70)
        lines.append(f"   {rec['description']}")
        lines.append(f"   Impact: {rec['impact']}")

        if rec.get("actions"):
            lines.append("   ")
            lines.append("   Actions to take:")
            for action in rec["actions"]:
                lines.append(f"   • {action}")

        return "\n".join(lines)

    @staticmethod
    def get_quick_wins(recommendations: List[Dict], limit: int = 3) -> List[Dict]:
        """
        Get quick win recommendations (highest impact, easiest to implement).

        Args:
            recommendations: Full list of recommendations
            limit: Number of quick wins to return

        Returns:
            List of quick win recommendations
        """
        # Quick wins are typically:
        # - CLAUDE.md setup (one-time, high impact)
        # - Defer documentation (behavioral, high impact)
        # - Concise mode (one-time setup)

        quick_win_ids = ["setup_claude_md", "defer_documentation", "enable_concise_mode"]

        quick_wins = [
            rec for rec in recommendations
            if rec["id"] in quick_win_ids
        ]

        return quick_wins[:limit]

    @staticmethod
    def calculate_total_potential(recommendations: List[Dict]) -> int:
        """
        Calculate total potential points from all recommendations.

        Args:
            recommendations: List of recommendations

        Returns:
            Total potential points
        """
        return sum(rec.get("potential_points", 0) for rec in recommendations)

    @staticmethod
    def get_next_rank_recommendations(current_score: int, next_rank_threshold: int, recommendations: List[Dict]) -> List[Dict]:
        """
        Get recommendations that would get user to next rank.

        Args:
            current_score: Current score
            next_rank_threshold: Score needed for next rank
            recommendations: All recommendations

        Returns:
            Filtered recommendations
        """
        points_needed = next_rank_threshold - current_score

        # Sort by potential points (highest first)
        sorted_recs = sorted(recommendations, key=lambda x: x.get("potential_points", 0), reverse=True)

        # Find minimum set that gets to next rank
        selected = []
        accumulated_points = 0

        for rec in sorted_recs:
            selected.append(rec)
            accumulated_points += rec.get("potential_points", 0)

            if accumulated_points >= points_needed:
                break

        return selected
