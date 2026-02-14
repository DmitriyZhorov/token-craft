"""
Recommendation Engine v2.0

Generates prescriptive, evidence-based optimization recommendations.
Integrates with waste detection, recommendation tracking, and pattern library.
"""

from typing import List, Dict, Optional


class RecommendationEngine:
    """Generate personalized, prescriptive recommendations with ROI data."""

    @staticmethod
    def generate_recommendations(
        score_data: Dict,
        profile_data: Dict,
        history_data: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate prioritized, prescriptive recommendations.

        Args:
            score_data: Score breakdown with waste detection data
            profile_data: User profile data
            history_data: Optional history data for deeper analysis

        Returns:
            List of prescriptive recommendations with concrete metrics
        """
        recommendations = []
        breakdown = score_data.get("breakdown", {})

        # Try to load recommendation tracker for historical ROI
        try:
            from token_craft.recommendation_tracker import RecommendationTracker
            tracker = RecommendationTracker()
            has_tracker = True
        except:
            tracker = None
            has_tracker = False

        # Try to load pattern library for evidence
        try:
            from token_craft.pattern_library import PatternLibrary
            library = PatternLibrary()
            has_library = True
        except:
            library = None
            has_library = False

        # 1. WASTE-BASED RECOMMENDATIONS (NEW v2.0)
        waste_data = breakdown.get("waste_awareness", {})
        waste_patterns = waste_data.get("waste_patterns", {})

        # 1a. Repeated Context (highest priority waste)
        repeated_context = waste_patterns.get("repeated_context", {})
        if repeated_context.get("waste_tokens", 0) > 1000:
            waste_tokens = repeated_context.get("waste_tokens", 0)
            days_active = waste_data.get("days_active", 30)
            daily_savings = waste_tokens / days_active if days_active > 0 else 0

            # Check if we have historical ROI for this
            historical_roi = None
            if has_tracker:
                similar = tracker.find_similar_recommendation("repeated_context")
                if similar:
                    historical_roi = similar.get("impact", {})

            description = (
                f"You're repeating context across messages → wasting {waste_tokens:,} tokens. "
                f"This costs ~{daily_savings:.0f} tokens/day. "
                f"Fix: Add repeated context to CLAUDE.md in your projects."
            )

            if historical_roi and historical_roi.get("tokens_saved", 0) > 0:
                description += f" (You saved {historical_roi['tokens_saved']:,} tokens when you fixed this before!)"

            recommendations.append({
                "id": "fix_repeated_context",
                "priority": 1,
                "category": "waste_awareness",
                "title": "STOP Repeating Context",
                "description": description,
                "impact": f"Save ~{waste_tokens:,} tokens ({daily_savings:.0f}/day)",
                "potential_points": min(100, waste_tokens // 200),
                "waste_tokens": waste_tokens,
                "daily_savings": daily_savings,
                "actions": [
                    "Identify repeated phrases in your prompts",
                    "Add them to CLAUDE.md in project root",
                    "Reference once instead of repeating"
                ],
                "proven": historical_roi is not None
            })

        # 1b. Verbose Prompts
        verbose_prompts = waste_patterns.get("verbose_prompts", {})
        if verbose_prompts.get("waste_tokens", 0) > 1000:
            waste_tokens = verbose_prompts.get("waste_tokens", 0)
            examples = verbose_prompts.get("examples", [])

            example_text = ""
            if examples and len(examples) > 0:
                ex = examples[0]
                if isinstance(ex, dict):
                    before = ex.get("actual_tokens", 0)
                    after = ex.get("baseline_tokens", 0)
                    example_text = f"Example: {before} tokens → {after} tokens. "

            recommendations.append({
                "id": "fix_verbose_prompts",
                "priority": 2,
                "category": "waste_awareness",
                "title": "Use Concise Prompts",
                "description": (
                    f"Your prompts are too long → wasting {waste_tokens:,} tokens. "
                    f"{example_text}"
                    f"Be direct: 'Edit file.py' not 'Could you please edit file.py'."
                ),
                "impact": f"Save ~{waste_tokens:,} tokens",
                "potential_points": min(80, waste_tokens // 250),
                "waste_tokens": waste_tokens,
                "actions": [
                    "Remove 'please', 'could you', 'thank you'",
                    "Be direct: state command + target",
                    "Skip explanations for simple tasks"
                ]
            })

        # 1c. Prompt Bloat
        prompt_bloat = waste_patterns.get("prompt_bloat", {})
        if prompt_bloat.get("waste_tokens", 0) > 500:
            waste_tokens = prompt_bloat.get("waste_tokens", 0)
            bloat_phrases = prompt_bloat.get("bloat_phrases", {})
            top_phrase = list(bloat_phrases.keys())[0] if bloat_phrases else "pleasantries"

            recommendations.append({
                "id": "fix_prompt_bloat",
                "priority": 3,
                "category": "waste_awareness",
                "title": "Remove Boilerplate",
                "description": (
                    f"You're using '{top_phrase}' and similar phrases unnecessarily → "
                    f"wasting {waste_tokens:,} tokens. AI doesn't need politeness tokens."
                ),
                "impact": f"Save ~{waste_tokens:,} tokens",
                "potential_points": min(50, waste_tokens // 300),
                "waste_tokens": waste_tokens,
                "actions": [
                    f"Remove '{top_phrase}' from prompts",
                    "Skip pleasantries - be direct",
                    "AI responds the same without 'please'"
                ]
            })

        # 2. TOKEN EFFICIENCY RECOMMENDATIONS
        efficiency = breakdown.get("token_efficiency", {})
        tier = efficiency.get("tier", "average")
        user_avg = efficiency.get("user_avg", 0)
        baseline_avg = efficiency.get("baseline_avg", 0)

        if tier in ["needs_work", "poor"]:
            excess = user_avg - baseline_avg
            sessions_per_day = 3  # Estimate
            daily_waste = excess * sessions_per_day

            recommendations.append({
                "id": "reduce_session_size",
                "priority": 1,
                "category": "token_efficiency",
                "title": "Break Down Large Sessions",
                "description": (
                    f"Your sessions average {user_avg:,.0f} tokens vs benchmark {baseline_avg:,.0f}. "
                    f"You're wasting {excess:,.0f} tokens/session = {daily_waste:,.0f} tokens/day. "
                    f"Break tasks into focused 5-15 message sessions."
                ),
                "impact": f"Save ~{daily_waste:,.0f} tokens/day",
                "potential_points": 100,
                "waste_tokens": int(excess),
                "daily_savings": daily_waste,
                "actions": [
                    "One task per session (don't switch topics)",
                    "Start new session after completing a task",
                    "Aim for 5-15 messages per session"
                ]
            })

        # 3. Defer Documentation (with concrete evidence)
        adoption = breakdown.get("optimization_adoption", {})
        defer_docs = adoption.get("breakdown", {}).get("defer_docs", {})
        if defer_docs.get("consistency", 100) < 60:
            # Check pattern library for evidence
            evidence_text = ""
            if has_library:
                pattern = library._find_pattern("pattern_defer_docs")
                if pattern and pattern["status"] == "validated":
                    evidence = pattern["evidence"]
                    evidence_text = (
                        f" PROVEN: {evidence['success_rate']*100:.0f}% success rate, "
                        f"{evidence['avg_improvement']:.0f}% token savings across {evidence['trials']} trials."
                    )

            recommendations.append({
                "id": "defer_documentation",
                "priority": 2,
                "category": "optimization_adoption",
                "title": "Defer Documentation Until Push",
                "description": (
                    f"Skip README, comments, docstrings during development. "
                    f"Write all docs in one pass when code is ready to push. "
                    f"Saves 2000-3000 tokens per feature.{evidence_text}"
                ),
                "impact": "Save 2000-3000 tokens per feature",
                "potential_points": 40,
                "waste_tokens": 2500,  # Estimated
                "actions": [
                    "Say 'skip docs for now' in prompts",
                    "Write code first, document at end",
                    "One documentation pass before git push"
                ],
                "evidence": evidence_text != ""
            })

        # 4. CLAUDE.md Setup (with concrete savings)
        claude_md = adoption.get("breakdown", {}).get("claude_md", {})
        if claude_md.get("with_claude_md", 0) < claude_md.get("top_projects", 3):
            missing_count = claude_md.get("top_projects", 3) - claude_md.get("with_claude_md", 0)
            tokens_per_session = 2000  # Average context saved
            sessions_per_project = 10  # Estimate per week
            weekly_savings = tokens_per_session * sessions_per_project * missing_count

            recommendations.append({
                "id": "setup_claude_md",
                "priority": 2,
                "category": "optimization_adoption",
                "title": f"Create CLAUDE.md in {missing_count} Project(s)",
                "description": (
                    f"Add CLAUDE.md to your top {missing_count} projects. "
                    f"Saves {tokens_per_session:,} tokens/session by eliminating repeated context. "
                    f"Estimated weekly savings: {weekly_savings:,} tokens."
                ),
                "impact": f"Save ~{weekly_savings:,} tokens/week",
                "potential_points": missing_count * 17,
                "waste_tokens": tokens_per_session,
                "weekly_savings": weekly_savings,
                "actions": [
                    "Create CLAUDE.md in project root",
                    "Add: project overview, tech stack, conventions",
                    "Include repeated context you identified above",
                    "Takes 10 minutes, saves tokens forever"
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

        # 5. Cache Effectiveness (concrete recovery potential)
        cache_data = breakdown.get("cache_effectiveness", {})
        cache_hit_rate = cache_data.get("cache_hit_rate", 0)
        total_regular_input = cache_data.get("total_regular_input", 0)

        if cache_hit_rate < 30 and total_regular_input > 10000:
            # Low cache usage with significant input
            potential_cache_tokens = int(total_regular_input * 0.6)  # 60% could be cached
            potential_savings = int(potential_cache_tokens * 0.9)  # 90% savings on cached

            recommendations.append({
                "id": "improve_cache_usage",
                "priority": 1,
                "category": "cache_effectiveness",
                "title": "Boost Cache Hit Rate",
                "description": (
                    f"Your cache hit rate is {cache_hit_rate:.0f}% (target: 60%+). "
                    f"You're missing out on {potential_savings:,} tokens of savings. "
                    f"Cause: Switching projects too often. "
                    f"Fix: Work on 2-3 projects per day instead of jumping around."
                ),
                "impact": f"Recover ~{potential_savings:,} tokens",
                "potential_points": 80,
                "waste_tokens": potential_savings,
                "actions": [
                    "Focus on 2-3 projects per day (not 10+)",
                    "Complete tasks in same project before switching",
                    "Cache maximizes when working on same files"
                ]
            })

        # 6. Improvement Trend (with specific diagnosis)
        trend = breakdown.get("improvement_trend", {})
        if trend.get("status") in ["maintaining", "slight_degradation", "significant_degradation"]:
            # Diagnose what changed
            improvement_pct = trend.get("improvement_pct", 0)

            recommendations.append({
                "id": "reverse_degradation",
                "priority": 1,  # High priority if degrading
                "category": "improvement_trend",
                "title": "Fix Recent Degradation",
                "description": (
                    f"Your efficiency dropped {abs(improvement_pct):.0f}% recently. "
                    f"Common causes: stopped using CLAUDE.md, longer sessions, "
                    f"or writing docs inline. Review and re-apply optimizations above."
                ),
                "impact": "Restore previous efficiency level",
                "potential_points": 100,
                "actions": [
                    "Review implemented recommendations above",
                    "Check if CLAUDE.md still in place",
                    "Compare recent vs past session patterns"
                ]
            })

        # Sort by actual waste/savings (prioritize biggest impact)
        # Primary: waste tokens (higher = more important)
        # Secondary: daily savings
        # Tertiary: priority number
        def sort_key(rec):
            waste = rec.get("waste_tokens", 0)
            daily = rec.get("daily_savings", 0)
            priority = rec.get("priority", 5)
            return (-waste, -daily, priority)

        recommendations.sort(key=sort_key)

        # Add historical ROI data to recommendations
        if has_tracker:
            for rec in recommendations:
                similar = tracker.find_similar_recommendation(rec["category"])
                if similar and similar.get("impact", {}).get("tokens_saved", 0) > 0:
                    rec["historical_roi"] = similar["impact"]
                    rec["proven_effective"] = True

        return recommendations

    @staticmethod
    def format_recommendation(rec: Dict, index: int = 1) -> str:
        """
        Format single recommendation for display (prescriptive style).

        Args:
            rec: Recommendation dict
            index: Index number

        Returns:
            Formatted string
        """
        lines = []

        # Header with badges
        title = f"{index}. {rec['title']}"
        if rec.get("proven_effective"):
            title += " ✓ PROVEN"
        if rec.get("evidence"):
            title += " 📊 VALIDATED"

        lines.append(f"\n{title}")
        lines.append("   " + "-" * 70)

        # Description
        lines.append(f"   {rec['description']}")

        # Impact with concrete numbers
        impact_line = f"   Impact: {rec['impact']}"
        if rec.get("waste_tokens"):
            impact_line += f" (wasting {rec['waste_tokens']:,} tokens)"
        if rec.get("daily_savings"):
            impact_line += f" [~{rec['daily_savings']:,.0f}/day]"
        lines.append(impact_line)

        # Historical ROI if available
        if rec.get("historical_roi"):
            roi = rec["historical_roi"]
            lines.append(f"   Historical: Saved {roi.get('tokens_saved', 0):,} tokens "
                        f"({roi.get('percent_improvement', 0):.0f}% improvement) when you implemented this before")

        # Actions
        if rec.get("actions"):
            lines.append("   ")
            lines.append("   Actions:")
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
