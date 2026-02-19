"""
Token-Craft Scoring Engine v3.0

Calculates scores across 10 categories with progressive difficulty:
1. Token Efficiency (250 pts) - Performance vs rank-adjusted baseline
2. Optimization Adoption (400 pts) - Usage of best practices
3. Improvement Trend (125 pts) - Progress over time
4. Waste Awareness (100 pts) - Waste reduction focus
5. Cache Effectiveness (75 pts) - Linear scale, continuous feedback
6. Tool Efficiency (75 pts) - Recommended tool adoption
7. Cost Efficiency (75 pts) - Cost optimization focus
8. Session Focus (75 pts) - Message clustering efficiency
9. Learning Growth (75 pts) - Skill improvement (no warm-up bonus)
10. Best Practices (50 pts) - Setup and configuration

Total: 2300 pts (up from 1450 in v2.0)
Bonus: Streak multiplier (1.0-1.25x), Combo bonuses (25-150 pts), Achievement rewards

v3.0 Features:
- Difficulty scaling by rank (43% harder at Legend)
- Streak/combo bonuses for consistency and excellence
- 25+ achievements with point rewards
- Time-based recency bonus and inactivity decay
- Seasonal resets every 30 days
- Full backwards compatibility with v2.0 data
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

from .difficulty_modifier import DifficultyModifier
from .streak_system import StreakSystem, ComboBonus
from .achievement_engine import AchievementEngine
from .time_based_mechanics import TimeBasedMechanics
from .regression_detector import RegressionDetector


class TokenCraftScorer:
    """Calculate token optimization scores."""

    # Scoring weights v3.0 (total = 2300 points)
    # Self-Sufficiency (200 pts) removed - duplicate of direct_commands check
    # Warm-up bonuses removed - no participation trophies
    WEIGHTS = {
        "token_efficiency": 250,         # 10.9% base (with difficulty/streak it becomes adaptive)
        "optimization_adoption": 400,    # 17.4% (absorbed Self-Sufficiency)
        "improvement_trend": 125,        # 5.4%
        "waste_awareness": 100,          # 4.3%
        "cache_effectiveness": 75,       # 3.3% (linear scale, not binary)
        "tool_efficiency": 75,           # 3.3%
        "cost_efficiency": 75,           # 3.3%
        "session_focus": 75,             # 3.3% (expanded from 50)
        "learning_growth": 75,           # 3.3% (no auto-bonus)
        "best_practices": 50,            # 2.2%
    }

    # Bonus systems weights (additional to base scoring)
    BONUS_WEIGHTS = {
        "streak_multiplier": 75,         # Max +75 from 1.25x multiplier
        "combo_bonuses": 150,            # Max +150 from MASTERY combo
        "achievement_rewards": 200,      # 25+ achievements worth 20-200 pts each
        "rank_prestige": 150,            # Bonus at rank milestones
    }

    # Total max achievable: 2300 (base) + 575 (bonuses) = 2875 theoretical
    # More realistic with consistency: ~2300-2500 pts at max rank

    # Company baseline (can be updated from real data)
    # Updated to reflect real coding session usage (2026-02-12)
    DEFAULT_BASELINE = {
        "tokens_per_session": 30000,  # Realistic for coding sessions
        "tokens_per_message": 1500,
        "self_sufficiency_rate": 0.40,
        "optimization_adoption_rate": 0.30
    }

    def __init__(
        self,
        history_data: List[Dict],
        stats_data: Dict,
        baseline: Optional[Dict] = None,
        rank: int = 1,
        user_profile: Optional[Dict] = None,
    ):
        """
        Initialize scorer with user data.

        Args:
            history_data: Parsed history.jsonl data
            stats_data: Parsed stats-cache.json data
            baseline: Company baseline metrics (optional)
            rank: Current user rank (1-10), used for difficulty scaling
            user_profile: User profile dict for streak/achievement integration
        """
        self.history_data = history_data
        self.stats_data = stats_data
        self.baseline = baseline or self.DEFAULT_BASELINE
        self.user_rank = rank
        self.user_profile = user_profile or {}

        # Initialize v3.0 systems
        self.difficulty = DifficultyModifier.get_difficulty(rank)
        self.streak_system = StreakSystem(user_profile)
        self.achievement_engine = AchievementEngine(user_profile)
        self.regression_detector = RegressionDetector()  # Phase 10: Regression detection

        # Parse and prepare data
        self._prepare_data()

    def _prepare_data(self):
        """Parse history and stats into usable format."""
        # Calculate basic metrics
        self.sessions = self._group_by_sessions()
        self.total_sessions = len(self.sessions)
        self.total_messages = sum(len(s["messages"]) for s in self.sessions)

        # Calculate tokens
        self.total_tokens = self._calculate_total_tokens()
        self.avg_tokens_per_session = self.total_tokens / self.total_sessions if self.total_sessions > 0 else 0

        # Calculate dynamic baseline
        self.dynamic_baseline = self._calculate_dynamic_baseline()

    def _group_by_sessions(self) -> List[Dict]:
        """Group history data by session."""
        sessions = {}

        for entry in self.history_data:
            session_id = entry.get("sessionId", "unknown")

            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "messages": [],
                    "project": entry.get("project", "unknown"),
                    "timestamp": entry.get("timestamp")
                }

            sessions[session_id]["messages"].append(entry)

        return list(sessions.values())

    def _calculate_total_tokens(self) -> int:
        """Calculate total tokens from stats data."""
        total = 0

        # Support both old format ("models") and new format ("modelUsage")
        models_data = self.stats_data.get("models") or self.stats_data.get("modelUsage")

        if models_data:
            for model, data in models_data.items():
                if isinstance(data, dict):
                    total += data.get("inputTokens", 0)
                    total += data.get("outputTokens", 0)

        return total

    def _calculate_dynamic_baseline(self) -> float:
        """
        Calculate dynamic baseline from user's best performing sessions.

        Uses the best 25% of sessions (P25) and reduces by 10% as target.
        Falls back to fixed baseline if insufficient data (<10 sessions).

        Returns:
            Dynamic baseline in tokens per session
        """
        # Need at least 10 sessions for meaningful dynamic baseline
        if self.total_sessions < 10:
            return self.baseline["tokens_per_session"]

        # Calculate tokens per session for each session
        # We need to distribute total tokens across sessions proportionally
        if self.total_sessions == 0:
            return self.baseline["tokens_per_session"]

        # For now, use average as approximation
        # TODO: Track per-session tokens in history.jsonl for more accuracy
        session_tokens = []
        tokens_per_session_avg = self.avg_tokens_per_session

        # Simple model: assume roughly similar distribution
        # In future, enhance history.jsonl to track per-session tokens
        for session in self.sessions:
            # Estimate: distribute total tokens proportionally by message count
            if self.total_messages > 0:
                session_msg_count = len(session["messages"])
                estimated_tokens = (session_msg_count / self.total_messages) * self.total_tokens
                session_tokens.append(estimated_tokens)

        if not session_tokens:
            return self.baseline["tokens_per_session"]

        # Sort to find best performing sessions (lowest tokens)
        session_tokens_sorted = sorted(session_tokens)

        # Get P25 (best 25%)
        p25_index = len(session_tokens_sorted) // 4
        if p25_index == 0:
            p25_index = 1

        best_sessions = session_tokens_sorted[:p25_index]
        best_avg = statistics.mean(best_sessions)

        # Set baseline as 90% of best quartile (10% improvement target)
        dynamic_baseline = best_avg * 0.90

        # Don't set impossibly low baseline (min 15000 tokens - reasonable for any session)
        dynamic_baseline = max(15000, dynamic_baseline)

        # If dynamic baseline is unreasonably low compared to user average,
        # it means our estimation failed - use fixed baseline instead
        if dynamic_baseline < self.avg_tokens_per_session * 0.5:
            # Estimation failed, use fixed baseline
            return self.baseline["tokens_per_session"]

        # Don't set higher than fixed baseline (defeats purpose)
        dynamic_baseline = min(dynamic_baseline, self.baseline["tokens_per_session"])

        return round(dynamic_baseline, 0)

    def calculate_token_efficiency_score(self) -> Dict:
        """
        Calculate Token Efficiency score (v3.0: 250 points max).

        Uses smooth logarithmic scale instead of harsh tiers for continuous feedback.
        Compares user's average tokens/session against rank-adjusted baseline.

        Score formula: 250 * log(1 + 1/ratio) / log(2)
        Result: 1.0x baseline = 250 pts, 1.5x = 214 pts, 2.0x = 165 pts (smooth, not stepped)

        Also applies difficulty multiplier based on user rank.

        Returns:
            Dict with score details
        """
        import math

        # Get rank-adjusted baseline from difficulty modifier
        adjusted_baseline = self.difficulty["tokens_per_session"]
        user_avg = self.avg_tokens_per_session
        using_dynamic = self.total_sessions >= 10

        if adjusted_baseline == 0 or user_avg == 0:
            # No data yet
            return {
                "score": 125,  # Neutral score
                "max_score": self.WEIGHTS["token_efficiency"],
                "percentage": 50.0,
                "user_avg": round(user_avg, 0),
                "baseline_avg": round(adjusted_baseline, 0),
                "baseline_type": "none",
                "tier": "no_data",
                "difficulty_rank": self.user_rank,
                "details": {
                    "total_sessions": self.total_sessions,
                    "total_tokens": self.total_tokens,
                    "avg_tokens_per_session": round(user_avg, 0)
                }
            }

        # Calculate ratio
        ratio = user_avg / adjusted_baseline

        # Smooth logarithmic scale: 250 * log(1 + 1/ratio) / log(2)
        # This gives continuous 0-250 range without harsh tier cliffs
        max_points = self.WEIGHTS["token_efficiency"]

        if ratio <= 1.0:
            # At or below baseline
            base_score = max_points
        else:
            # Calculate using logarithmic formula for smooth scaling
            try:
                # log(1 + 1/ratio) gives diminishing returns
                # Divide by log(2) to scale to 0-1 range
                log_component = math.log(1 + 1 / ratio) / math.log(2)
                base_score = max_points * log_component
            except (ValueError, ZeroDivisionError):
                # Fallback if math fails
                base_score = 0

        # Apply difficulty multiplier (higher ranks have tighter curves)
        difficulty_adjusted_score = DifficultyModifier.apply_token_efficiency_difficulty(
            base_score, ratio, self.user_rank
        )

        # Determine tier for display
        if ratio <= 1.0:
            tier = "excellent"
        elif ratio <= 1.5:
            tier = "very_good"
        elif ratio <= 2.0:
            tier = "good"
        elif ratio <= 3.0:
            tier = "average"
        else:
            tier = "needs_work"

        # Calculate improvement percentage
        improvement_pct = ((adjusted_baseline - user_avg) / adjusted_baseline) * 100

        return {
            "score": round(difficulty_adjusted_score, 1),
            "max_score": max_points,
            "percentage": round((difficulty_adjusted_score / max_points) * 100, 1),
            "user_avg": round(user_avg, 0),
            "baseline_avg": round(adjusted_baseline, 0),
            "baseline_type": "dynamic" if using_dynamic else "fixed",
            "ratio": round(ratio, 2),
            "tier": tier,
            "improvement_pct": round(improvement_pct, 1),
            "difficulty_rank": self.user_rank,
            "base_score_before_difficulty": round(base_score, 1),
            "difficulty_multiplier": round(DifficultyModifier.RANK_BASELINES[self.user_rank]["multiplier"], 2),
            "details": {
                "total_sessions": self.total_sessions,
                "total_tokens": self.total_tokens,
                "avg_tokens_per_session": round(user_avg, 0)
            }
        }

    def calculate_optimization_adoption_score(self) -> Dict:
        """
        Calculate Optimization Adoption score (32.5%, 325 points max).

        Tracks usage of 8 Anthropic best practices over 90-day window:
        1. Defer documentation (50 points)
        2. Use CLAUDE.md (50 points)
        3. Concise response mode (40 points)
        4. Direct commands (60 points)
        5. Context management (50 points)
        6. XML tags usage (20 points) - Anthropic validated
        7. Chain of Thought (30 points) - Anthropic validated
        8. Examples usage (25 points) - Anthropic validated

        Returns:
            Dict with score breakdown
        """
        scores = {}
        total_score = 0

        # 1. Defer Documentation (50 points)
        defer_score = self._check_defer_documentation()
        scores["defer_docs"] = defer_score
        total_score += defer_score["score"]

        # 2. CLAUDE.md Usage (50 points)
        claude_md_score = self._check_claude_md_usage()
        scores["claude_md"] = claude_md_score
        total_score += claude_md_score["score"]

        # 3. Concise Response Mode (40 points)
        concise_score = self._check_concise_mode()
        scores["concise_mode"] = concise_score
        total_score += concise_score["score"]

        # 4. Direct Commands (60 points)
        direct_cmd_score = self._check_direct_commands()
        scores["direct_commands"] = direct_cmd_score
        total_score += direct_cmd_score["score"]

        # 5. Context Management (50 points)
        context_score = self._check_context_management()
        scores["context_mgmt"] = context_score
        total_score += context_score["score"]

        # 6. XML Tags Usage (20 points) - NEW
        xml_score = self._check_xml_usage()
        scores["xml_tags"] = xml_score
        total_score += xml_score["score"]

        # 7. Chain of Thought (30 points) - NEW
        cot_score = self._check_chain_of_thought()
        scores["chain_of_thought"] = cot_score
        total_score += cot_score["score"]

        # 8. Examples Usage (25 points) - NEW
        examples_score = self._check_examples_usage()
        scores["examples"] = examples_score
        total_score += examples_score["score"]

        return {
            "score": round(total_score, 1),
            "max_score": self.WEIGHTS["optimization_adoption"],
            "percentage": round((total_score / self.WEIGHTS["optimization_adoption"]) * 100, 1),
            "breakdown": scores
        }

    def _check_defer_documentation(self) -> Dict:
        """Check if user defers documentation until ready to push."""
        # Heuristic: Look for documentation keywords in messages
        doc_keywords = ["readme", "documentation", "comment", "docstring", "docs"]
        defer_keywords = ["defer", "later", "skip", "wait", "after"]

        doc_sessions = 0
        deferred_sessions = 0

        for session in self.sessions:
            has_doc_request = False
            has_defer = False

            for msg in session["messages"]:
                content = msg.get("message", "").lower()

                if any(kw in content for kw in doc_keywords):
                    has_doc_request = True

                if any(kw in content for kw in defer_keywords):
                    has_defer = True

            if has_doc_request:
                doc_sessions += 1
                if has_defer:
                    deferred_sessions += 1

        consistency = deferred_sessions / doc_sessions if doc_sessions > 0 else 0.5
        score = self._calculate_tier_score(consistency, max_points=50)

        return {
            "score": score,
            "max_score": 50,
            "consistency": round(consistency * 100, 1),
            "opportunities": doc_sessions,
            "used": deferred_sessions
        }

    def _check_claude_md_usage(self) -> Dict:
        """Check if CLAUDE.md exists in top projects."""
        # Get top 3 projects by usage
        project_counts = {}
        for session in self.sessions:
            project = session["project"]
            project_counts[project] = project_counts.get(project, 0) + 1

        top_projects = sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Check for CLAUDE.md in each project
        projects_with_claude_md = 0
        for project, _ in top_projects:
            claude_md_path = Path(project) / "CLAUDE.md"
            if claude_md_path.exists():
                projects_with_claude_md += 1

        consistency = projects_with_claude_md / len(top_projects) if top_projects else 0
        score = self._calculate_tier_score(consistency, max_points=50)

        return {
            "score": score,
            "max_score": 50,
            "consistency": round(consistency * 100, 1),
            "top_projects": len(top_projects),
            "with_claude_md": projects_with_claude_md
        }

    def _check_concise_mode(self) -> Dict:
        """Check for concise response preference."""
        # Heuristic: Check MEMORY.md or CLAUDE.md for concise preference
        memory_md_path = Path.home() / ".claude" / "memory" / "MEMORY.md"

        has_concise_preference = False
        if memory_md_path.exists():
            content = memory_md_path.read_text().lower()
            if "concise" in content or "brief" in content or "short" in content:
                has_concise_preference = True

        # Also check average message length
        if self.total_messages > 0:
            avg_msg_length = sum(
                len(msg.get("message", ""))
                for session in self.sessions
                for msg in session["messages"]
            ) / self.total_messages

            # If average message is under 200 chars, consider concise
            if avg_msg_length < 200:
                has_concise_preference = True

        consistency = 1.0 if has_concise_preference else 0.3
        score = self._calculate_tier_score(consistency, max_points=40)

        return {
            "score": score,
            "max_score": 40,
            "consistency": round(consistency * 100, 1),
            "preference_set": has_concise_preference
        }

    def _check_direct_commands(self) -> Dict:
        """Check how often user runs commands directly vs asking AI."""
        # Heuristic: Count tool calls vs opportunities
        # This is simplified - in production, track actual command opportunities

        # Count Read/Bash tool calls (these could be done directly)
        ai_command_count = 0
        for session in self.sessions:
            for msg in session["messages"]:
                # Check if AI was asked to run simple commands
                content = msg.get("message", "").lower()
                simple_cmds = ["git log", "git status", "cat ", "ls ", "grep ", "show me"]

                if any(cmd in content for cmd in simple_cmds):
                    ai_command_count += 1

        # Estimate opportunities (rough heuristic)
        total_opportunities = self.total_sessions * 2  # Assume 2 opportunities per session
        direct_commands = max(0, total_opportunities - ai_command_count)

        consistency = direct_commands / total_opportunities if total_opportunities > 0 else 0.5
        score = self._calculate_tier_score(consistency, max_points=60)

        return {
            "score": score,
            "max_score": 60,
            "consistency": round(consistency * 100, 1),
            "opportunities": total_opportunities,
            "direct_commands": direct_commands,
            "ai_commands": ai_command_count
        }

    def _check_context_management(self) -> Dict:
        """Check for good context management practices."""
        # Heuristic: Check session length and message count
        if self.total_sessions == 0:
            return {"score": 25, "max_score": 50, "consistency": 50.0}

        avg_messages_per_session = self.total_messages / self.total_sessions

        # Good: 5-15 messages per session (focused)
        # Too short (<5): Not using AI effectively
        # Too long (>20): Context bloat

        if 5 <= avg_messages_per_session <= 15:
            consistency = 1.0
        elif avg_messages_per_session < 5:
            consistency = 0.6
        else:  # > 15
            consistency = max(0.3, 1.0 - ((avg_messages_per_session - 15) / 50))

        score = self._calculate_tier_score(consistency, max_points=50)

        return {
            "score": score,
            "max_score": 50,
            "consistency": round(consistency * 100, 1),
            "avg_messages_per_session": round(avg_messages_per_session, 1)
        }

    def _check_xml_usage(self) -> Dict:
        """
        Check for XML tag usage in prompts (Anthropic best practice).

        Anthropic recommends structuring prompts with XML tags like:
        <document>, <task>, <context>, <example>, etc.
        """
        xml_keywords = ["<document>", "<task>", "<context>", "<example>", "<input>", "<output>", "</"]

        xml_sessions = 0
        for session in self.sessions:
            for msg in session["messages"]:
                content = msg.get("message", "")
                if any(kw in content for kw in xml_keywords):
                    xml_sessions += 1
                    break  # Count session once

        consistency = xml_sessions / self.total_sessions if self.total_sessions > 0 else 0
        score = self._calculate_tier_score(consistency, max_points=20)

        return {
            "score": score,
            "max_score": 20,
            "consistency": round(consistency * 100, 1),
            "sessions_with_xml": xml_sessions,
            "total_sessions": self.total_sessions,
            "benefit": "XML tags improve prompt structure and clarity"
        }

    def _check_chain_of_thought(self) -> Dict:
        """
        Check for Chain of Thought usage (Anthropic best practice).

        Anthropic recommends using CoT prompts like:
        "let's think step by step", "reasoning:", "because", etc.
        """
        cot_keywords = ["let's think", "step by step", "reasoning:", "because", "first", "then", "therefore", "analyze"]

        cot_sessions = 0
        for session in self.sessions:
            for msg in session["messages"]:
                content = msg.get("message", "").lower()
                if any(kw in content for kw in cot_keywords):
                    cot_sessions += 1
                    break  # Count session once

        consistency = cot_sessions / self.total_sessions if self.total_sessions > 0 else 0
        score = self._calculate_tier_score(consistency, max_points=30)

        return {
            "score": score,
            "max_score": 30,
            "consistency": round(consistency * 100, 1),
            "sessions_with_cot": cot_sessions,
            "total_sessions": self.total_sessions,
            "benefit": "Chain of Thought improves reasoning quality and accuracy"
        }

    def _check_examples_usage(self) -> Dict:
        """
        Check for examples/few-shot prompting (Anthropic best practice).

        Anthropic recommends providing examples like:
        "for example", "e.g.", "such as", "like this:", etc.
        """
        example_keywords = ["for example", "e.g.", "such as", "like this:", "here's an example", "example:"]

        example_sessions = 0
        for session in self.sessions:
            for msg in session["messages"]:
                content = msg.get("message", "").lower()
                if any(kw in content for kw in example_keywords):
                    example_sessions += 1
                    break  # Count session once

        consistency = example_sessions / self.total_sessions if self.total_sessions > 0 else 0
        score = self._calculate_tier_score(consistency, max_points=25)

        return {
            "score": score,
            "max_score": 25,
            "consistency": round(consistency * 100, 1),
            "sessions_with_examples": example_sessions,
            "total_sessions": self.total_sessions,
            "benefit": "Examples improve output quality and reduce iterations"
        }

    def _calculate_tier_score(self, consistency: float, max_points: int) -> float:
        """
        Calculate smooth sliding scale score based on consistency rate.

        Provides gradual increases for better progress visibility.
        Users see improvement every 5-10% instead of big jumps.

        Scoring curves:
        - 90-100%: Full points (100%)
        - 70-89%: Interpolated 85-100%
        - 50-69%: Interpolated 65-85%
        - 30-49%: Interpolated 40-65%
        - 0-29%: Linear from 0%
        """
        if consistency >= 0.90:
            # Excellent - full points
            return max_points
        elif consistency >= 0.70:
            # Good - interpolate between 85% and 100%
            ratio = (consistency - 0.70) / 0.20
            return max_points * (0.85 + (0.15 * ratio))
        elif consistency >= 0.50:
            # Average - interpolate between 65% and 85%
            ratio = (consistency - 0.50) / 0.20
            return max_points * (0.65 + (0.20 * ratio))
        elif consistency >= 0.30:
            # Below average - interpolate between 40% and 65%
            ratio = (consistency - 0.30) / 0.20
            return max_points * (0.40 + (0.25 * ratio))
        else:
            # Poor - linear from 0 to 40%
            return max_points * (consistency / 0.30) * 0.40

    def calculate_improvement_trend_score(self, previous_snapshot: Optional[Dict] = None) -> Dict:
        """
        Calculate Improvement Trend score (12.5%, 125 points max).

        Includes warm-up period for new users (<10 sessions).
        Compares rolling windows for established users.

        Args:
            previous_snapshot: Previous snapshot data for comparison

        Returns:
            Dict with score details
        """
        # Warm-up period for new users (<10 sessions)
        if self.total_sessions < 10:
            return {
                "score": 50,
                "max_score": self.WEIGHTS["improvement_trend"],
                "percentage": 40.0,
                "improvement_pct": 0,
                "status": "warming_up",
                "message": f"Session {self.total_sessions}/10 - Establishing baseline"
            }

        if not previous_snapshot:
            # No previous data, give baseline score
            return {
                "score": 50,
                "max_score": self.WEIGHTS["improvement_trend"],
                "percentage": 40.0,
                "improvement_pct": 0,
                "status": "baseline",
                "message": "No previous snapshot for comparison"
            }

        # Compare token efficiency
        prev_avg = previous_snapshot.get("avg_tokens_per_session", self.baseline["tokens_per_session"])
        current_avg = self.avg_tokens_per_session

        if prev_avg == 0:
            improvement_pct = 0
        else:
            improvement_pct = ((prev_avg - current_avg) / prev_avg) * 100

        # Score based on improvement
        if improvement_pct >= 10:
            score = 150
            status = "excellent"
        elif improvement_pct >= 5:
            score = 100
            status = "good"
        elif improvement_pct >= 2:
            score = 50
            status = "modest"
        elif improvement_pct >= 0:
            score = 20
            status = "maintaining"
        elif improvement_pct >= -5:
            score = 0
            status = "slight_degradation"
        else:
            score = 0
            status = "significant_degradation"

        return {
            "score": score,
            "max_score": self.WEIGHTS["improvement_trend"],
            "percentage": round((score / self.WEIGHTS["improvement_trend"]) * 100, 1),
            "improvement_pct": round(improvement_pct, 1),
            "status": status,
            "prev_avg": round(prev_avg, 0),
            "current_avg": round(current_avg, 0)
        }

    def calculate_best_practices_score(self) -> Dict:
        """
        Calculate Best Practices score (5%, 50 points max).

        Checks:
        - CLAUDE.md in top 3 projects (30 points)
        - Memory.md has optimizations (10 points)
        - Uses appropriate tooling (10 points)

        Returns:
            Dict with score details
        """
        checks = {}
        total_score = 0

        # 1. CLAUDE.md in top projects
        claude_md_data = self._check_claude_md_usage()
        claude_md_score = (claude_md_data["with_claude_md"] / max(1, claude_md_data["top_projects"])) * 30
        checks["claude_md_setup"] = {
            "score": round(claude_md_score, 1),
            "max_score": 30,
            "projects_with_setup": claude_md_data["with_claude_md"],
            "top_projects": claude_md_data["top_projects"]
        }
        total_score += claude_md_score

        # 2. Memory.md optimizations
        memory_md_path = Path.home() / ".claude" / "memory" / "MEMORY.md"
        has_optimizations = False

        if memory_md_path.exists():
            content = memory_md_path.read_text().lower()
            opt_keywords = ["optimization", "defer", "efficiency", "token", "concise"]
            if any(kw in content for kw in opt_keywords):
                has_optimizations = True

        memory_score = 10 if has_optimizations else 0
        checks["memory_md_optimizations"] = {
            "score": memory_score,
            "max_score": 10,
            "has_optimizations": has_optimizations
        }
        total_score += memory_score

        # 3. Appropriate tooling
        # Give 10 points as baseline (assumes using token-craft tool)
        checks["tooling"] = {
            "score": 10,
            "max_score": 10,
            "using_token_craft": True
        }
        total_score += 10

        return {
            "score": round(total_score, 1),
            "max_score": self.WEIGHTS["best_practices"],
            "percentage": round((total_score / self.WEIGHTS["best_practices"]) * 100, 1),
            "checks": checks
        }

    def calculate_cache_effectiveness_score(self) -> Dict:
        """
        Calculate Cache Effectiveness score (v3.0: 75 points max).

        Uses linear scale for continuous feedback instead of binary states.
        Score = (cache_hit_rate / 100) * 75
        Result: 20% cache hits = 15 pts (not 0), 50% = 37.5 pts, 100% = 75 pts

        Also applies rank-adjusted targets from difficulty modifier.

        Returns:
            Dict with score details
        """
        # Get cache stats from stats data
        models_data = self.stats_data.get("models") or self.stats_data.get("modelUsage")

        if not models_data:
            return {
                "score": 0,
                "max_score": self.WEIGHTS["cache_effectiveness"],
                "percentage": 0,
                "cache_hit_rate": 0,
                "target_hit_rate": self.difficulty["cache_hit_target"],
                "message": "No cache data available"
            }

        # Calculate total cache reads and regular inputs
        total_cache_reads = 0
        total_cache_creates = 0
        total_regular_input = 0

        for model, data in models_data.items():
            if isinstance(data, dict):
                total_cache_reads += data.get("cacheReadInputTokens", 0)
                total_cache_creates += data.get("cacheCreationInputTokens", 0)
                total_regular_input += data.get("inputTokens", 0)

        # Calculate cache hit rate
        total_input_opportunities = total_cache_reads + total_regular_input

        if total_input_opportunities == 0:
            cache_hit_rate = 0
        else:
            cache_hit_rate = (total_cache_reads / total_input_opportunities) * 100

        # Linear score: (cache_hit_rate / 100) * max_points
        # This gives continuous 0-75 range without harsh tier cliffs
        max_points = self.WEIGHTS["cache_effectiveness"]
        score = (cache_hit_rate / 100) * max_points

        # Determine tier for display
        target = self.difficulty["cache_hit_target"]
        if cache_hit_rate >= target + 20:
            tier = "excellent"
        elif cache_hit_rate >= target:
            tier = "good"
        elif cache_hit_rate >= max(10, target - 10):
            tier = "average"
        else:
            tier = "needs_work"

        # Calculate cost savings from caching
        # Cache reads cost 90% less than regular inputs
        cache_savings_pct = 90 if total_cache_reads > 0 else 0

        return {
            "score": round(score, 1),
            "max_score": max_points,
            "percentage": round((score / max_points) * 100, 1),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "target_hit_rate": target,
            "total_cache_reads": total_cache_reads,
            "total_cache_creates": total_cache_creates,
            "total_regular_input": total_regular_input,
            "cache_savings_pct": cache_savings_pct,
            "tier": tier,
            "difficulty_rank": self.user_rank,
            "details": {
                "excellent": cache_hit_rate >= target + 20,
                "using_cache": total_cache_reads > 0
            }
        }

    def calculate_session_focus_score(self) -> Dict:
        """
        Calculate Session Focus score (3.7%, 50 points max).

        Optimal session length is 5-15 messages (focused work).

        Returns:
            Dict with score details
        """
        if self.total_sessions == 0:
            return {
                "score": 25,
                "max_score": self.WEIGHTS["session_focus"],
                "percentage": 50.0,
                "avg_messages_per_session": 0,
                "message": "No sessions yet"
            }

        avg_messages = self.total_messages / self.total_sessions

        # Score based on message count
        if 5 <= avg_messages <= 15:
            score = 50  # Perfect - focused sessions
        elif 3 <= avg_messages < 5 or 15 < avg_messages <= 20:
            score = 40  # Good - slightly off
        elif 1 <= avg_messages < 3 or 20 < avg_messages <= 30:
            score = 20  # Not ideal - too short or too long
        else:  # < 1 or > 30
            score = 0   # Poor - way off

        return {
            "score": score,
            "max_score": self.WEIGHTS["session_focus"],
            "percentage": round((score / self.WEIGHTS["session_focus"]) * 100, 1),
            "avg_messages_per_session": round(avg_messages, 1),
            "total_messages": self.total_messages,
            "total_sessions": self.total_sessions,
            "optimal": 5 <= avg_messages <= 15
        }

    def calculate_tool_efficiency_score(self) -> Dict:
        """
        Calculate Tool Usage Efficiency score (5.6%, 75 points max).

        Tracks optimal tool usage patterns:
        - Read-before-edit compliance (30 pts)
        - Parallel tool calls (25 pts)
        - Glob/Grep preference over Bash (20 pts)

        Returns:
            Dict with score details
        """
        if not self.history_data:
            return {
                "score": 37,
                "max_score": self.WEIGHTS["tool_efficiency"],
                "percentage": 50.0,
                "message": "No history data available"
            }

        read_before_edit_count = 0
        edit_without_read_count = 0
        parallel_call_count = 0
        single_call_count = 0
        glob_grep_count = 0
        bash_find_grep_count = 0

        files_read = set()

        for session in self.history_data:
            messages = session.get("messages", [])

            for msg in messages:
                if msg.get("role") != "assistant":
                    continue

                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue

                # Count tool calls in this turn
                tool_calls = [c for c in content if c.get("type") == "tool_use"]

                if len(tool_calls) > 1:
                    parallel_call_count += 1
                elif len(tool_calls) == 1:
                    single_call_count += 1

                # Check read-before-edit and tool preferences
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "")

                    # Track Read calls
                    if tool_name == "Read":
                        file_path = tool_call.get("input", {}).get("file_path", "")
                        if file_path:
                            files_read.add(file_path)

                    # Track Edit calls (check if read first)
                    elif tool_name == "Edit":
                        file_path = tool_call.get("input", {}).get("file_path", "")
                        if file_path in files_read:
                            read_before_edit_count += 1
                        else:
                            edit_without_read_count += 1

                    # Track Glob/Grep usage
                    elif tool_name in ["Glob", "Grep"]:
                        glob_grep_count += 1

                    # Track Bash find/grep
                    elif tool_name == "Bash":
                        command = tool_call.get("input", {}).get("command", "")
                        if any(cmd in command for cmd in ["find ", "grep ", "rg "]):
                            bash_find_grep_count += 1

        # Calculate scores
        # 1. Read-before-edit compliance (30 pts)
        total_edits = read_before_edit_count + edit_without_read_count
        if total_edits > 0:
            read_compliance_pct = (read_before_edit_count / total_edits) * 100
            if read_compliance_pct >= 90:
                read_score = 30
            elif read_compliance_pct >= 75:
                read_score = 25
            elif read_compliance_pct >= 60:
                read_score = 20
            elif read_compliance_pct >= 40:
                read_score = 15
            else:
                read_score = 10
        else:
            read_score = 30  # No edits = no violation

        # 2. Parallel tool usage (25 pts)
        total_tool_turns = parallel_call_count + single_call_count
        if total_tool_turns > 0:
            parallel_pct = (parallel_call_count / total_tool_turns) * 100
            if parallel_pct >= 40:
                parallel_score = 25
            elif parallel_pct >= 30:
                parallel_score = 20
            elif parallel_pct >= 20:
                parallel_score = 15
            elif parallel_pct >= 10:
                parallel_score = 10
            else:
                parallel_score = 5
        else:
            parallel_score = 12  # Neutral

        # 3. Glob/Grep preference (20 pts)
        total_search = glob_grep_count + bash_find_grep_count
        if total_search > 0:
            glob_pct = (glob_grep_count / total_search) * 100
            if glob_pct >= 90:
                glob_score = 20
            elif glob_pct >= 75:
                glob_score = 16
            elif glob_pct >= 50:
                glob_score = 12
            elif glob_pct >= 25:
                glob_score = 8
            else:
                glob_score = 4
        else:
            glob_score = 20  # No searches = assume good practice

        total_score = read_score + parallel_score + glob_score

        return {
            "score": total_score,
            "max_score": self.WEIGHTS["tool_efficiency"],
            "percentage": round((total_score / self.WEIGHTS["tool_efficiency"]) * 100, 1),
            "read_before_edit": {
                "compliant": read_before_edit_count,
                "violations": edit_without_read_count,
                "score": read_score
            },
            "parallel_usage": {
                "parallel_turns": parallel_call_count,
                "single_turns": single_call_count,
                "percentage": round(parallel_pct if total_tool_turns > 0 else 0, 1),
                "score": parallel_score
            },
            "glob_grep_preference": {
                "glob_grep_count": glob_grep_count,
                "bash_find_grep_count": bash_find_grep_count,
                "percentage": round(glob_pct if total_search > 0 else 100, 1),
                "score": glob_score
            }
        }

    def calculate_cost_efficiency_score(self) -> Dict:
        """
        Calculate Cost Efficiency score (5.6%, 75 points max).

        Tracks cost-consciousness:
        - Cost per session vs baseline (40 pts)
        - Cache usage (saves 90% on input) (20 pts)
        - Budget compliance (15 pts)

        Returns:
            Dict with score details
        """
        # Calculate average cost per session
        # Model pricing: Sonnet 4.5 = $3/M input, $15/M output (avg ~$9/M)
        avg_tokens_per_session = self.total_tokens / self.total_sessions if self.total_sessions > 0 else 0
        avg_cost_per_session = (avg_tokens_per_session / 1_000_000) * 9.0  # $9 avg per million

        # Baseline cost per session (30K tokens = $0.27)
        baseline_cost = 0.27

        # 1. Cost per session vs baseline (40 pts)
        if avg_cost_per_session <= baseline_cost * 0.7:  # 30% better
            cost_score = 40
        elif avg_cost_per_session <= baseline_cost * 0.85:  # 15% better
            cost_score = 35
        elif avg_cost_per_session <= baseline_cost * 1.0:  # At baseline
            cost_score = 30
        elif avg_cost_per_session <= baseline_cost * 1.2:  # 20% worse
            cost_score = 20
        elif avg_cost_per_session <= baseline_cost * 1.5:  # 50% worse
            cost_score = 10
        else:
            cost_score = 5

        # 2. Cache effectiveness contribution (20 pts)
        # Already measured in cache_effectiveness, just check if using cache
        models_data = self.stats_data.get("models") or self.stats_data.get("modelUsage", {})
        total_cache_reads = sum(data.get("cacheReadInputTokens", 0) for data in models_data.values())

        if total_cache_reads > 10000:  # Actively using cache
            cache_contribution = 20
        elif total_cache_reads > 5000:
            cache_contribution = 15
        elif total_cache_reads > 1000:
            cache_contribution = 10
        else:
            cache_contribution = 5

        # 3. Budget compliance (15 pts) - check if staying under reasonable limits
        # Assume $5/day budget, user has 24 sessions total
        estimated_daily_sessions = 3  # Reasonable estimate
        daily_cost_estimate = avg_cost_per_session * estimated_daily_sessions

        if daily_cost_estimate <= 2.0:  # Well under budget
            budget_score = 15
        elif daily_cost_estimate <= 5.0:  # Within budget
            budget_score = 12
        elif daily_cost_estimate <= 7.0:  # Slightly over
            budget_score = 8
        else:
            budget_score = 4

        total_score = cost_score + cache_contribution + budget_score

        return {
            "score": total_score,
            "max_score": self.WEIGHTS["cost_efficiency"],
            "percentage": round((total_score / self.WEIGHTS["cost_efficiency"]) * 100, 1),
            "avg_cost_per_session": round(avg_cost_per_session, 4),
            "baseline_cost": baseline_cost,
            "cost_ratio": round(avg_cost_per_session / baseline_cost, 2) if baseline_cost > 0 else 1.0,
            "estimated_daily_cost": round(daily_cost_estimate, 2),
            "breakdown": {
                "cost_vs_baseline": cost_score,
                "cache_contribution": cache_contribution,
                "budget_compliance": budget_score
            }
        }

    def calculate_learning_growth_score(self) -> Dict:
        """
        Calculate Learning & Growth score (v3.0: 75 points max).

        Tracks improvement and skill development:
        - Efficiency improvement trend (25 pts)
        - Consistency in best practices (25 pts)
        - Autonomy growth (25 pts)

        v3.0 Change: Removed auto 25 pts for <10 sessions.
        Points must be earned through actual 5%+ improvement.

        Returns:
            Dict with score details
        """
        if self.total_sessions < 10:
            # NO warm-up bonus in v3.0 - must show real improvement
            # Give baseline score only if minimal data exists
            return {
                "score": 0,
                "max_score": self.WEIGHTS["learning_growth"],
                "percentage": 0.0,
                "message": "Keep improving! Scores will increase with real efficiency gains.",
                "sessions": self.total_sessions,
                "note": "v3.0: No warm-up bonuses - earn points through actual improvement"
            }

        # Split sessions into early (first 1/3) and recent (last 1/3)
        if not self.history_data:
            return {
                "score": 25,
                "max_score": self.WEIGHTS["learning_growth"],
                "percentage": 50.0,
                "message": "No history data available"
            }

        total_sessions = len(self.history_data)
        third = max(1, total_sessions // 3)

        early_sessions = self.history_data[:third]
        recent_sessions = self.history_data[-third:]

        # Calculate average tokens for early vs recent
        early_tokens = []
        recent_tokens = []

        for session in early_sessions:
            session_tokens = sum(
                msg.get("tokens", 0)
                for msg in session.get("messages", [])
                if msg.get("role") == "assistant"
            )
            if session_tokens > 0:
                early_tokens.append(session_tokens)

        for session in recent_sessions:
            session_tokens = sum(
                msg.get("tokens", 0)
                for msg in session.get("messages", [])
                if msg.get("role") == "assistant"
            )
            if session_tokens > 0:
                recent_tokens.append(session_tokens)

        # 1. Efficiency improvement (25 pts)
        if early_tokens and recent_tokens:
            early_avg = statistics.mean(early_tokens)
            recent_avg = statistics.mean(recent_tokens)
            improvement = ((early_avg - recent_avg) / early_avg) * 100 if early_avg > 0 else 0

            if improvement >= 20:  # 20%+ improvement
                efficiency_score = 25
            elif improvement >= 10:  # 10%+ improvement
                efficiency_score = 20
            elif improvement >= 5:  # 5%+ improvement (v3.0: raised from 0%)
                efficiency_score = 15
            elif improvement >= 0:  # Maintained
                efficiency_score = 10
            else:  # Degradation
                efficiency_score = 0
        else:
            efficiency_score = 0  # No baseline data - no bonus

        # 2. Consistency (25 pts) - check if maintaining good practices
        # Count sessions with optimal message count (5-15 messages)
        optimal_sessions = 0
        for session in recent_sessions:
            message_count = len(session.get("messages", []))
            if 5 <= message_count <= 15:
                optimal_sessions += 1

        consistency_pct = (optimal_sessions / len(recent_sessions)) * 100 if recent_sessions else 0

        if consistency_pct >= 70:
            consistency_score = 25
        elif consistency_pct >= 50:
            consistency_score = 18
        elif consistency_pct >= 30:
            consistency_score = 12
        else:
            consistency_score = 0

        # 3. Autonomy growth (25 pts) - fewer messages per session over time
        early_msg_counts = [len(s.get("messages", [])) for s in early_sessions]
        recent_msg_counts = [len(s.get("messages", [])) for s in recent_sessions]

        if early_msg_counts and recent_msg_counts:
            early_avg_msgs = statistics.mean(early_msg_counts)
            recent_avg_msgs = statistics.mean(recent_msg_counts)

            # Lower message count = more autonomy (doing more yourself)
            if recent_avg_msgs < early_avg_msgs * 0.8:  # 20%+ reduction
                autonomy_score = 25
            elif recent_avg_msgs < early_avg_msgs * 0.9:  # 10%+ reduction
                autonomy_score = 20
            elif recent_avg_msgs < early_avg_msgs:
                autonomy_score = 15
            elif recent_avg_msgs <= early_avg_msgs * 1.1:  # Within 10%
                autonomy_score = 10
            else:
                autonomy_score = 0
        else:
            autonomy_score = 0  # No baseline data - no bonus

        total_score = efficiency_score + consistency_score + autonomy_score

        return {
            "score": total_score,
            "max_score": self.WEIGHTS["learning_growth"],
            "percentage": round((total_score / self.WEIGHTS["learning_growth"]) * 100, 1),
            "efficiency_improvement": round(improvement if 'improvement' in locals() else 0, 1),
            "consistency_rate": round(consistency_pct, 1),
            "breakdown": {
                "efficiency_improvement": efficiency_score,
                "consistency": consistency_score,
                "autonomy_growth": autonomy_score
            },
            "early_avg_tokens": round(early_avg, 0) if 'early_avg' in locals() else 0,
            "recent_avg_tokens": round(recent_avg, 0) if 'recent_avg' in locals() else 0
        }

    def calculate_waste_awareness_score(self) -> Dict:
        """
        Calculate Waste Awareness score (v3.0: 100 points max).

        Tracks proactive efforts to reduce token waste:
        - Session optimization attempts
        - Prompt refinement patterns
        - Context pruning

        Returns:
            Dict with score details
        """
        # Detect waste reduction signals
        waste_signals = 0

        # Check for varied message lengths (indicates refinement)
        message_lengths = []
        for session in self.sessions:
            for msg in session.get("messages", []):
                content = msg.get("content", "")
                if isinstance(content, str):
                    message_lengths.append(len(content))

        if message_lengths and len(message_lengths) > 10:
            # Calculate coefficient of variation
            mean_length = statistics.mean(message_lengths)
            std_dev = statistics.stdev(message_lengths) if len(message_lengths) > 1 else 0

            # High variation (CV > 0.5) indicates attempts at varied prompt lengths
            cv = std_dev / mean_length if mean_length > 0 else 0
            if cv > 0.5:
                waste_signals += 1

        # Check for gradually decreasing tokens per session (trend toward efficiency)
        session_tokens = []
        for session in self.sessions:
            session_total = 0
            for msg in session.get("messages", []):
                session_total += msg.get("tokens", 0)
            if session_total > 0:
                session_tokens.append(session_total)

        if len(session_tokens) >= 5:
            # Compare first 1/3 vs last 1/3
            third = len(session_tokens) // 3
            early_avg = statistics.mean(session_tokens[:third]) if third > 0 else 0
            late_avg = statistics.mean(session_tokens[-third:]) if third > 0 else 0

            if early_avg > 0 and late_avg < early_avg:
                improvement = ((early_avg - late_avg) / early_avg) * 100
                if improvement >= 5:
                    waste_signals += 1

        # Check for project-specific optimization (multiple projects)
        projects = {s.get("project", "unknown") for s in self.sessions}
        if len(projects) >= 3:  # Using at least 3 different project contexts
            waste_signals += 1

        # Score based on waste reduction signals
        # Each signal = 20 pts, max 5 signals = 100 pts
        max_points = self.WEIGHTS["waste_awareness"]
        signal_weight = max_points / 5

        score = min(waste_signals * signal_weight, max_points)

        tier = "none"
        if waste_signals >= 4:
            tier = "excellent"
        elif waste_signals >= 3:
            tier = "good"
        elif waste_signals >= 2:
            tier = "aware"
        elif waste_signals >= 1:
            tier = "beginning"

        return {
            "score": round(score, 1),
            "max_score": max_points,
            "percentage": round((score / max_points) * 100, 1),
            "waste_signals_detected": waste_signals,
            "tier": tier,
            "details": {
                "varied_prompt_lengths": waste_signals > 0,
                "efficiency_trend": waste_signals > 1,
                "project_diversity": len(projects),
                "total_projects": len(projects)
            }
        }

    def calculate_total_score(self, previous_snapshot: Optional[Dict] = None) -> Dict:
        """
        Calculate total score across all categories (v3.0 - Integrated).

        Includes:
        - 10 base scoring categories
        - Difficulty modifier (rank-based)
        - Streak multiplier (1.0x - 1.25x)
        - Combo bonuses (25-150 pts)
        - Achievement rewards (20-200 pts)
        - Time-based modifiers (recency, decay)
        - Seasonal tracking

        Args:
            previous_snapshot: Previous snapshot for trend calculation

        Returns:
            Complete score breakdown with bonuses
        """
        # Calculate each category (v3.0: 10 categories, no self_sufficiency)
        token_efficiency = self.calculate_token_efficiency_score()
        optimization_adoption = self.calculate_optimization_adoption_score()
        improvement_trend = self.calculate_improvement_trend_score(previous_snapshot)
        waste_awareness = self.calculate_waste_awareness_score()
        best_practices = self.calculate_best_practices_score()

        # New categories
        cache_effectiveness = self.calculate_cache_effectiveness_score()
        tool_efficiency = self.calculate_tool_efficiency_score()
        cost_efficiency = self.calculate_cost_efficiency_score()
        session_focus = self.calculate_session_focus_score()
        learning_growth = self.calculate_learning_growth_score()

        # Sum base scores
        base_total_score = (
            token_efficiency["score"] +
            optimization_adoption["score"] +
            improvement_trend["score"] +
            waste_awareness["score"] +
            best_practices["score"] +
            cache_effectiveness["score"] +
            tool_efficiency["score"] +
            cost_efficiency["score"] +
            session_focus["score"] +
            learning_growth["score"]
        )

        # Calculate max possible (base weights only)
        max_base = sum(self.WEIGHTS.values())

        # Apply Streak Multiplier
        streak_info = self.streak_system.get_streak_bonus()
        streak_multiplier = streak_info["multiplier"]
        streak_bonus_points = streak_info["bonus_points"]

        # Apply Combo Bonuses
        category_scores = {
            "token_efficiency": token_efficiency,
            "optimization_adoption": optimization_adoption,
            "improvement_trend": improvement_trend,
            "waste_awareness": waste_awareness,
            "cache_effectiveness": cache_effectiveness,
            "tool_efficiency": tool_efficiency,
            "cost_efficiency": cost_efficiency,
            "session_focus": session_focus,
            "learning_growth": learning_growth,
            "best_practices": best_practices,
        }
        combo_result = ComboBonus.check_combo(category_scores)
        combo_bonus_points = combo_result["bonus_points"]

        # Calculate total with bonuses
        score_after_streak = base_total_score * streak_multiplier
        score_after_combo = score_after_streak + combo_bonus_points

        # Check and unlock achievements
        newly_unlocked_achievements = []
        newly_unlocked_achievements.extend(
            self.achievement_engine.check_progression_achievements(self.user_rank, score_after_combo)
        )
        newly_unlocked_achievements.extend(
            self.achievement_engine.check_excellence_achievements(category_scores)
        )

        # Final score (before time modifiers)
        final_score = score_after_combo + streak_bonus_points

        # Phase 10: Detect performance regression
        current_efficiency = token_efficiency.get("efficiency_ratio", 1.0)
        personal_best_efficiency = token_efficiency.get("personal_best_efficiency", current_efficiency)
        recent_scores = self.user_profile.get("recent_session_scores", [])

        regression_analysis = self.regression_detector.analyze_regression(
            current_score=final_score,
            current_efficiency=current_efficiency,
            personal_best_efficiency=personal_best_efficiency,
            recent_scores=recent_scores,
        )

        # Apply time-based mechanics (recency bonus, inactivity decay)
        time_adjusted = TimeBasedMechanics.apply_time_modifiers(
            final_score,
            datetime.now().isoformat(),
            self.user_profile.get("last_updated")
        )
        time_adjusted_score = time_adjusted["adjusted_score"]

        # Build comprehensive breakdown
        breakdown = {
            "token_efficiency": token_efficiency,
            "optimization_adoption": optimization_adoption,
            "improvement_trend": improvement_trend,
            "waste_awareness": waste_awareness,
            "best_practices": best_practices,
            "cache_effectiveness": cache_effectiveness,
            "tool_efficiency": tool_efficiency,
            "cost_efficiency": cost_efficiency,
            "session_focus": session_focus,
            "learning_growth": learning_growth,
        }

        # Build bonuses breakdown
        bonuses = {
            "streak": {
                "multiplier": round(streak_multiplier, 2),
                "bonus_points": round(streak_bonus_points, 1),
                "streak_length": streak_info["streak_length"],
            },
            "combo": {
                "bonus_points": round(combo_bonus_points, 1),
                "tier": combo_result["tier_name"],
                "excellent_categories": combo_result["excellent_categories"],
            },
            "time_modifiers": {
                "recency_multiplier": round(time_adjusted["recency"]["multiplier"], 2),
                "decay_multiplier": round(time_adjusted["decay"]["multiplier"] if time_adjusted["decay"] else 1.0, 2),
                "combined_multiplier": round(time_adjusted["combined_multiplier"], 2),
            },
            "achievements": {
                "newly_unlocked": len(newly_unlocked_achievements),
                "total_unlocked": len(self.achievement_engine.unlocked_achievements),
            }
        }

        # Calculate percentages
        max_achievable = max_base + sum(self.BONUS_WEIGHTS.values())

        return {
            "total_score": round(time_adjusted_score, 1),
            "base_score": round(base_total_score, 1),
            "with_bonuses": round(score_after_combo + streak_bonus_points, 1),
            "max_base": max_base,
            "max_achievable": max_achievable,
            "percentage": round((time_adjusted_score / max_achievable) * 100, 1),
            "percentage_of_base": round((base_total_score / max_base) * 100, 1),
            "breakdown": breakdown,
            "bonuses": bonuses,
            "newly_unlocked_achievements": [
                {
                    "id": ach["achievement_id"],
                    "name": ach["name"],
                    "points": ach["points"],
                }
                for ach in newly_unlocked_achievements
            ],
            "user_rank": self.user_rank,
            "difficulty_info": self.difficulty,
            "streak_info": streak_info,
            "combo_info": combo_result,
            "regression_analysis": {  # Phase 10: Performance regression detection
                "has_regressed": regression_analysis.get("has_regressed", False),
                "severity": regression_analysis.get("severity", "none"),
                "efficiency": regression_analysis.get("efficiency", {}),
                "score": regression_analysis.get("score", {}),
                "recommendation": regression_analysis.get("recommendation", ""),
            },
            "calculated_at": datetime.now().isoformat(),
            "version": "3.0"
        }
