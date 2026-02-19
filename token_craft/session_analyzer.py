"""
Session Analyzer - Structural efficiency analysis using /insights data.

Reads session-meta and facets from ~/.claude/usage-data/ to detect:
- Session length risk (cache write amplification)
- Cross-session repetition (same question asked multiple times)
- CLAUDE.md size impact (per-message tax)
- Failed session cost (tokens wasted on not_achieved sessions)
- Nudge patterns (impatient short messages in long sessions)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SessionAnalyzer:
    """Analyze session-level efficiency using /insights data."""

    # Thresholds
    SESSION_LENGTH_WARNING = 25   # messages before warning
    SESSION_LENGTH_DANGER = 50    # messages before danger
    NUDGE_MAX_CHARS = 15          # max chars for a "nudge" message
    NUDGE_MAX_RESPONSE_TIME = 120 # seconds - fast follow-up
    REPETITION_SIMILARITY = 0.85  # threshold for "same question"
    CLAUDE_MD_WARNING_TOKENS = 3000  # warn if CLAUDE.md > this

    # Cost rates (Sonnet 4.5 per million tokens)
    CACHE_WRITE_RATE = 3.75   # per MTok
    CACHE_READ_RATE = 0.30    # per MTok
    INPUT_RATE = 3.00         # per MTok
    OUTPUT_RATE = 15.00       # per MTok

    def __init__(self, claude_dir: Optional[Path] = None):
        """
        Initialize with path to ~/.claude directory.

        Args:
            claude_dir: Path to ~/.claude. Auto-detected if None.
        """
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        self.claude_dir = claude_dir
        self.usage_data_dir = claude_dir / "usage-data"
        self.session_meta_dir = self.usage_data_dir / "session-meta"
        self.facets_dir = self.usage_data_dir / "facets"

        self._sessions = None
        self._facets = None

    def _load_sessions(self) -> List[Dict]:
        """Load all session-meta JSON files."""
        if self._sessions is not None:
            return self._sessions

        self._sessions = []
        if not self.session_meta_dir.exists():
            return self._sessions

        for f in self.session_meta_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self._sessions.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        return self._sessions

    def _load_facets(self) -> Dict[str, Dict]:
        """Load all facets JSON files, keyed by session_id."""
        if self._facets is not None:
            return self._facets

        self._facets = {}
        if not self.facets_dir.exists():
            return self._facets

        for f in self.facets_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sid = data.get("session_id", f.stem)
                self._facets[sid] = data
            except (json.JSONDecodeError, OSError):
                continue

        return self._facets

    def analyze_all(self) -> Dict:
        """
        Run all analyses and return combined results.

        Returns:
            Dict with keys: session_risks, repetitions, claude_md_impact,
            failed_sessions, nudge_patterns, summary
        """
        sessions = self._load_sessions()
        if not sessions:
            return {"available": False, "reason": "No /insights data found"}

        results = {
            "available": True,
            "session_risks": self.analyze_session_lengths(),
            "repetitions": self.detect_cross_session_repetition(),
            "claude_md_impact": self.calculate_claude_md_impact(),
            "failed_sessions": self.analyze_failed_sessions(),
            "nudge_patterns": self.detect_nudge_patterns(),
        }

        results["summary"] = self._build_summary(results)
        return results

    def analyze_session_lengths(self) -> Dict:
        """
        Identify sessions with dangerous length (high cache write cost).

        Returns:
            Dict with risky_sessions list and total_estimated_waste.
        """
        sessions = self._load_sessions()
        risky = []

        for s in sessions:
            msg_count = s.get("user_message_count", 0)
            assistant_count = s.get("assistant_message_count", 0)
            total_msgs = msg_count + assistant_count
            duration = s.get("duration_minutes", 0)

            if msg_count < self.SESSION_LENGTH_WARNING:
                continue

            # Estimate cache write cost growth
            # Each message sends the entire growing context
            # Cache writes grow roughly quadratically with session length
            # Simplified model: sum of 1..N context sizes
            input_tokens = s.get("input_tokens", 0)
            output_tokens = s.get("output_tokens", 0)

            # Risk level
            if msg_count >= self.SESSION_LENGTH_DANGER:
                risk = "danger"
            else:
                risk = "warning"

            # Estimate what splitting into 15-msg sessions would save
            optimal_sessions = max(1, msg_count // 15)
            # Quadratic growth: cost ~ N^2 for one session vs N*k^2 for k sessions
            # Savings ratio: 1 - (optimal_sessions * (msg_count/optimal_sessions)^2) / msg_count^2
            # Simplifies to: 1 - 1/optimal_sessions
            savings_pct = (1 - 1 / optimal_sessions) * 100 if optimal_sessions > 1 else 0

            risky.append({
                "session_id": s.get("session_id", "unknown"),
                "project": Path(s.get("project_path", "")).name,
                "user_messages": msg_count,
                "total_messages": total_msgs,
                "duration_minutes": duration,
                "risk": risk,
                "output_tokens": output_tokens,
                "savings_if_split_pct": round(savings_pct),
                "recommended_splits": optimal_sessions,
            })

        risky.sort(key=lambda x: x["user_messages"], reverse=True)

        return {
            "risky_sessions": risky,
            "count": len(risky),
            "total_sessions_analyzed": len(sessions),
        }

    def detect_cross_session_repetition(self) -> Dict:
        """
        Find the same question asked across multiple sessions.

        Uses first_prompt from session-meta to detect duplicates.
        """
        sessions = self._load_sessions()
        prompt_map = {}  # normalized prompt → list of sessions

        for s in sessions:
            prompt = s.get("first_prompt", "").strip()
            if not prompt or len(prompt) < 10:
                continue

            # Normalize: lowercase, strip whitespace, collapse spaces
            normalized = " ".join(prompt.lower().split())

            # Group by similarity (exact match after normalization)
            found_group = False
            for key in prompt_map:
                if self._is_similar(normalized, key):
                    prompt_map[key].append(s)
                    found_group = True
                    break

            if not found_group:
                prompt_map[normalized] = [s]

        # Find prompts asked in 2+ sessions
        repeated = []
        for prompt, sessions_list in prompt_map.items():
            if len(sessions_list) >= 2:
                repeated.append({
                    "prompt": sessions_list[0].get("first_prompt", prompt)[:100],
                    "count": len(sessions_list),
                    "session_ids": [s.get("session_id", "") for s in sessions_list],
                    "projects": list(set(
                        Path(s.get("project_path", "")).name
                        for s in sessions_list
                    )),
                    "estimated_waste_sessions": len(sessions_list) - 1,
                })

        repeated.sort(key=lambda x: x["count"], reverse=True)

        return {
            "repeated_prompts": repeated,
            "total_repeated_sessions": sum(r["estimated_waste_sessions"] for r in repeated),
            "unique_prompts_analyzed": len(prompt_map),
        }

    def _is_similar(self, a: str, b: str) -> bool:
        """Check if two normalized strings are similar enough to be 'same question'."""
        if a == b:
            return True

        # Simple Jaccard similarity on word sets
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return False

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        similarity = intersection / union if union > 0 else 0

        return similarity >= self.REPETITION_SIMILARITY

    def calculate_claude_md_impact(self) -> Dict:
        """
        Estimate the token cost of CLAUDE.md files loaded into every message.

        Checks both global and project-level CLAUDE.md files.
        """
        claude_md_files = []
        total_chars = 0

        # Global CLAUDE.md
        global_md = self.claude_dir / "CLAUDE.md"
        if global_md.exists():
            try:
                content = global_md.read_text(encoding="utf-8")
                chars = len(content)
                # Rough estimate: 1 token ≈ 4 characters
                tokens = chars // 4
                claude_md_files.append({
                    "path": "~/.claude/CLAUDE.md",
                    "chars": chars,
                    "estimated_tokens": tokens,
                })
                total_chars += chars
            except OSError:
                pass

        # Home directory CLAUDE.md
        home_md = Path.home() / "CLAUDE.md"
        if home_md.exists() and home_md != global_md:
            try:
                content = home_md.read_text(encoding="utf-8")
                chars = len(content)
                tokens = chars // 4
                claude_md_files.append({
                    "path": "~/CLAUDE.md",
                    "chars": chars,
                    "estimated_tokens": tokens,
                })
                total_chars += chars
            except OSError:
                pass

        total_tokens_per_msg = total_chars // 4

        # Get total messages from stats-cache
        stats_file = self.claude_dir / "stats-cache.json"
        total_messages = 0
        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text(encoding="utf-8"))
                total_messages = stats.get("totalMessages", 0)
            except (json.JSONDecodeError, OSError):
                pass

        # Calculate total impact
        total_claude_md_tokens = total_tokens_per_msg * total_messages
        # Cost at cache read rate (loaded from cache after first message)
        cache_read_cost = (total_claude_md_tokens / 1_000_000) * self.CACHE_READ_RATE

        # Sessions count for cache write cost (one write per session)
        sessions = self._load_sessions()
        num_sessions = len(sessions) if sessions else 0
        cache_write_cost = (total_tokens_per_msg * num_sessions / 1_000_000) * self.CACHE_WRITE_RATE

        return {
            "files": claude_md_files,
            "total_chars": total_chars,
            "tokens_per_message": total_tokens_per_msg,
            "total_messages": total_messages,
            "total_claude_md_tokens": total_claude_md_tokens,
            "estimated_cache_read_cost": round(cache_read_cost, 2),
            "estimated_cache_write_cost": round(cache_write_cost, 2),
            "estimated_total_cost": round(cache_read_cost + cache_write_cost, 2),
            "is_oversized": total_tokens_per_msg > self.CLAUDE_MD_WARNING_TOKENS,
            "recommendation": self._claude_md_recommendation(total_tokens_per_msg),
        }

    def _claude_md_recommendation(self, tokens: int) -> str:
        """Generate recommendation based on CLAUDE.md size."""
        if tokens > 5000:
            return f"CLAUDE.md is very large (~{tokens} tokens). Cut 50%+ by removing verbose examples, duplicate rules, and bash snippets. Target <2000 tokens."
        elif tokens > 3000:
            return f"CLAUDE.md is large (~{tokens} tokens). Trim permission lists and examples. Target <2000 tokens."
        elif tokens > 2000:
            return f"CLAUDE.md is moderate (~{tokens} tokens). Consider trimming verbose sections."
        else:
            return f"CLAUDE.md is well-sized (~{tokens} tokens)."

    def analyze_failed_sessions(self) -> Dict:
        """
        Identify sessions marked as 'not_achieved' in facets data.

        These represent tokens spent without achieving the user's goal.
        """
        sessions = self._load_sessions()
        facets = self._load_facets()

        failed = []
        for s in sessions:
            sid = s.get("session_id", "")
            facet = facets.get(sid)
            if not facet:
                continue

            outcome = facet.get("outcome", "")
            if outcome in ("not_achieved", "unclear_from_transcript"):
                output_tokens = s.get("output_tokens", 0)
                duration = s.get("duration_minutes", 0)
                friction = facet.get("friction_detail", "Unknown")
                helpfulness = facet.get("claude_helpfulness", "unknown")

                failed.append({
                    "session_id": sid,
                    "project": Path(s.get("project_path", "")).name,
                    "goal": facet.get("underlying_goal", "Unknown")[:100],
                    "outcome": outcome,
                    "friction": friction[:150],
                    "helpfulness": helpfulness,
                    "output_tokens": output_tokens,
                    "duration_minutes": duration,
                    "user_messages": s.get("user_message_count", 0),
                    "tool_errors": s.get("tool_errors", 0),
                })

        failed.sort(key=lambda x: x["output_tokens"], reverse=True)

        total_wasted_tokens = sum(f["output_tokens"] for f in failed)
        wasted_cost = (total_wasted_tokens / 1_000_000) * self.OUTPUT_RATE

        return {
            "failed_sessions": failed,
            "count": len(failed),
            "total_wasted_output_tokens": total_wasted_tokens,
            "estimated_wasted_cost": round(wasted_cost, 2),
            "total_facets_analyzed": len(facets),
        }

    def detect_nudge_patterns(self) -> Dict:
        """
        Detect impatient 'nudge' messages (short follow-ups in long sessions).

        Uses user_response_times from session-meta: very fast response (<2min)
        combined with short messages suggests impatient nudging.
        """
        sessions = self._load_sessions()
        nudge_sessions = []

        for s in sessions:
            response_times = s.get("user_response_times", [])
            msg_count = s.get("user_message_count", 0)

            if msg_count < 5 or not response_times:
                continue

            # Count very fast responses (likely nudges)
            fast_responses = sum(
                1 for t in response_times
                if t < self.NUDGE_MAX_RESPONSE_TIME
            )
            # In a long session, fast responses are more concerning
            nudge_ratio = fast_responses / len(response_times) if response_times else 0

            if fast_responses >= 3 and nudge_ratio > 0.3:
                nudge_sessions.append({
                    "session_id": s.get("session_id", ""),
                    "project": Path(s.get("project_path", "")).name,
                    "user_messages": msg_count,
                    "fast_responses": fast_responses,
                    "nudge_ratio": round(nudge_ratio * 100),
                    "avg_response_time": round(
                        sum(response_times) / len(response_times), 1
                    ),
                    "duration_minutes": s.get("duration_minutes", 0),
                })

        nudge_sessions.sort(key=lambda x: x["fast_responses"], reverse=True)

        return {
            "nudge_sessions": nudge_sessions,
            "count": len(nudge_sessions),
        }

    def _build_summary(self, results: Dict) -> Dict:
        """Build a summary of all findings with total estimated waste."""
        issues = []
        total_waste_estimate = 0

        # Session length risks
        sr = results["session_risks"]
        if sr["count"] > 0:
            danger = sum(1 for s in sr["risky_sessions"] if s["risk"] == "danger")
            warning = sr["count"] - danger
            issues.append({
                "category": "Long Sessions",
                "severity": "high" if danger > 0 else "medium",
                "description": f"{sr['count']} sessions over {self.SESSION_LENGTH_WARNING} messages ({danger} critical)",
                "action": "Break sessions at 15-25 messages when switching topics",
            })

        # Repetitions
        rep = results["repetitions"]
        if rep["total_repeated_sessions"] > 0:
            issues.append({
                "category": "Repeated Questions",
                "severity": "medium",
                "description": f"{len(rep['repeated_prompts'])} questions repeated across {rep['total_repeated_sessions']} extra sessions",
                "action": "Use /resume to continue sessions; troubleshoot in-session instead of restarting",
            })

        # CLAUDE.md
        cmd = results["claude_md_impact"]
        if cmd["is_oversized"]:
            issues.append({
                "category": "Large CLAUDE.md",
                "severity": "medium",
                "description": f"~{cmd['tokens_per_message']} tokens loaded per message (est. ${cmd['estimated_total_cost']} total)",
                "action": cmd["recommendation"],
            })
            total_waste_estimate += cmd["estimated_total_cost"]

        # Failed sessions
        fs = results["failed_sessions"]
        if fs["count"] > 0:
            issues.append({
                "category": "Failed Sessions",
                "severity": "medium" if fs["count"] <= 2 else "high",
                "description": f"{fs['count']} sessions didn't achieve their goal (est. ${fs['estimated_wasted_cost']} wasted)",
                "action": "Clarify goals upfront; break complex tasks into smaller steps",
            })
            total_waste_estimate += fs["estimated_wasted_cost"]

        # Nudge patterns
        np = results["nudge_patterns"]
        if np["count"] > 0:
            issues.append({
                "category": "Impatient Messaging",
                "severity": "low",
                "description": f"{np['count']} sessions with rapid-fire follow-ups",
                "action": "Wait for responses before sending follow-ups; each message grows the context",
            })

        issues.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])

        return {
            "issues": issues,
            "total_issues": len(issues),
            "estimated_total_waste": round(total_waste_estimate, 2),
        }

    def format_report_section(self, results: Dict) -> str:
        """
        Format analysis results as an ASCII report section.

        Args:
            results: Output from analyze_all()

        Returns:
            Formatted string for inclusion in Token-Craft report.
        """
        if not results.get("available"):
            return ""

        lines = []
        lines.append("Structural Efficiency Analysis (from /insights data):")
        lines.append("=" * 70)

        summary = results.get("summary", {})
        issues = summary.get("issues", [])

        if not issues:
            lines.append("")
            lines.append("  No structural efficiency issues detected.")
            return "\n".join(lines)

        # Summary
        lines.append("")
        lines.append(f"  Found {summary['total_issues']} issue(s):")
        lines.append("")

        for i, issue in enumerate(issues, 1):
            severity_icon = {"high": "[!]", "medium": "[~]", "low": "[-]"}
            icon = severity_icon.get(issue["severity"], "[-]")
            lines.append(f"  {icon} {issue['category']}: {issue['description']}")
            lines.append(f"      Fix: {issue['action']}")
            lines.append("")

        # Detailed sections
        # Session Length Risks
        sr = results.get("session_risks", {})
        if sr.get("count", 0) > 0:
            lines.append("-" * 70)
            lines.append("Session Length Risk:")
            lines.append("")
            for s in sr["risky_sessions"][:3]:
                risk_label = "DANGER" if s["risk"] == "danger" else "WARNING"
                lines.append(f"  [{risk_label}] {s['project']}: {s['user_messages']} user msgs, {s['duration_minutes']} min")
                lines.append(f"           Split into {s['recommended_splits']}x sessions → save ~{s['savings_if_split_pct']}% cache cost")
            lines.append("")

        # Cross-session Repetition
        rep = results.get("repetitions", {})
        if rep.get("repeated_prompts"):
            lines.append("-" * 70)
            lines.append("Cross-Session Repetition:")
            lines.append("")
            for r in rep["repeated_prompts"][:3]:
                lines.append(f"  \"{r['prompt'][:70]}...\"")
                lines.append(f"  Asked {r['count']}x across sessions ({r['estimated_waste_sessions']} redundant)")
            lines.append("")

        # CLAUDE.md Impact
        cmd = results.get("claude_md_impact", {})
        if cmd.get("tokens_per_message", 0) > 1000:
            lines.append("-" * 70)
            lines.append("CLAUDE.md Size Impact:")
            lines.append("")
            for f in cmd.get("files", []):
                lines.append(f"  {f['path']}: ~{f['estimated_tokens']} tokens")
            lines.append(f"  Loaded into every message ({cmd.get('total_messages', 0)} total)")
            lines.append(f"  Estimated cost: ${cmd.get('estimated_total_cost', 0)}")
            lines.append(f"  {cmd.get('recommendation', '')}")
            lines.append("")

        # Failed Sessions
        fs = results.get("failed_sessions", {})
        if fs.get("count", 0) > 0:
            lines.append("-" * 70)
            lines.append("Failed Sessions (goal not achieved):")
            lines.append("")
            for f in fs["failed_sessions"][:3]:
                lines.append(f"  {f['project']}: \"{f['goal'][:60]}\"")
                lines.append(f"    Friction: {f['friction'][:80]}")
                lines.append(f"    Wasted: {f['output_tokens']:,} output tokens")
            lines.append(f"  Total estimated waste: ${fs.get('estimated_wasted_cost', 0)}")
            lines.append("")

        return "\n".join(lines)
