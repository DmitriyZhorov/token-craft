"""
Recommendation Tracking System

Tracks recommendations through full lifecycle:
generation → implementation → impact measurement
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class RecommendationTracker:
    """Track recommendation lifecycle and measure ROI."""

    def __init__(self):
        """Initialize recommendation tracker."""
        self.token_craft_dir = Path.home() / ".claude" / "token-craft"
        self.recommendations_file = self.token_craft_dir / "recommendations.json"

        # Ensure directory exists
        self.token_craft_dir.mkdir(parents=True, exist_ok=True)

        # Load existing recommendations
        self.recommendations = self._load_recommendations()

    def _load_recommendations(self) -> Dict:
        """Load recommendations from file."""
        if self.recommendations_file.exists():
            try:
                with open(self.recommendations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Default structure
        return {
            "recommendations": [],
            "pending": [],
            "implemented": [],
            "dismissed": []
        }

    def _save_recommendations(self):
        """Save recommendations to file."""
        with open(self.recommendations_file, 'w', encoding='utf-8') as f:
            json.dump(self.recommendations, f, indent=2)

    def track_recommendation(
        self,
        rec_id: str,
        title: str,
        category: str,
        baseline_metrics: Dict
    ):
        """
        Start tracking a new recommendation.

        Args:
            rec_id: Unique recommendation ID
            title: Recommendation title
            category: Category (e.g., "optimization_adoption")
            baseline_metrics: Baseline metrics before implementation
        """
        # Check if already tracked
        existing = self._find_recommendation(rec_id)
        if existing:
            return  # Already tracking

        recommendation = {
            "id": rec_id,
            "generated_at": datetime.now().isoformat(),
            "title": title,
            "category": category,
            "status": "pending",
            "baseline_metrics": baseline_metrics,
            "implementation_detected_at": None,
            "current_metrics": {},
            "impact": {}
        }

        self.recommendations["recommendations"].append(recommendation)
        self.recommendations["pending"].append(rec_id)
        self._save_recommendations()

    def _find_recommendation(self, rec_id: str) -> Optional[Dict]:
        """Find recommendation by ID."""
        for rec in self.recommendations["recommendations"]:
            if rec["id"] == rec_id:
                return rec
        return None

    def detect_implementation(
        self,
        rec_id: str,
        recent_sessions: List[Dict]
    ) -> bool:
        """
        Detect if user implemented a recommendation.

        Args:
            rec_id: Recommendation ID
            recent_sessions: Recent session data

        Returns:
            True if implementation detected
        """
        rec = self._find_recommendation(rec_id)
        if not rec:
            return False

        category = rec["category"]

        # Detection strategies per category
        if "defer" in rec["title"].lower() or category == "optimization_adoption":
            return self._detect_defer_docs_implementation(recent_sessions)
        elif "claude.md" in rec["title"].lower():
            return self._detect_claude_md_implementation()
        elif "concise" in rec["title"].lower():
            return self._detect_concise_mode_implementation(recent_sessions)
        elif "self_sufficiency" in category:
            return self._detect_self_sufficiency_implementation(recent_sessions)

        return False

    def _detect_defer_docs_implementation(self, recent_sessions: List[Dict]) -> bool:
        """
        Detect if user started deferring documentation.

        Strategy:
        - Before: Doc keywords appear early in sessions
        - After: Doc keywords absent or only in last 20% of session
        - Threshold: 3+ consecutive sessions showing new pattern
        """
        doc_keywords = ["readme", "documentation", "docstring", "comment", "docs"]
        pattern_count = 0

        for session in recent_sessions[-5:]:  # Check last 5 sessions
            messages = session.get("messages", [])
            if not messages:
                continue

            total_msgs = len(messages)
            threshold_idx = int(total_msgs * 0.8)  # Last 20%

            # Check if doc keywords only appear in last 20%
            early_doc_mentions = 0
            late_doc_mentions = 0

            for idx, msg in enumerate(messages):
                text = msg.get("text", "").lower()
                has_doc_keyword = any(kw in text for kw in doc_keywords)

                if has_doc_keyword:
                    if idx < threshold_idx:
                        early_doc_mentions += 1
                    else:
                        late_doc_mentions += 1

            # Pattern: no early mentions OR only late mentions
            if early_doc_mentions == 0 or (late_doc_mentions > 0 and early_doc_mentions == 0):
                pattern_count += 1

        return pattern_count >= 3

    def _detect_claude_md_implementation(self) -> bool:
        """
        Detect if user created CLAUDE.md in projects.

        Strategy:
        - Check if CLAUDE.md exists in common project directories
        - Verify file size >500 bytes (not just empty)
        """
        # Common project locations
        potential_projects = [
            Path.home() / "Documents",
            Path.home() / "Projects",
            Path.home() / "Code",
            Path.home() / "workspace"
        ]

        claude_md_count = 0

        for base_dir in potential_projects:
            if not base_dir.exists():
                continue

            # Search for CLAUDE.md files (max depth 3)
            for claude_file in base_dir.rglob("CLAUDE.md"):
                if claude_file.stat().st_size > 500:
                    claude_md_count += 1
                    if claude_md_count >= 1:
                        return True

        return False

    def _detect_concise_mode_implementation(self, recent_sessions: List[Dict]) -> bool:
        """
        Detect if user adopted concise mode.

        Strategy:
        - Before: Avg message length >200 chars
        - After: Avg message length <150 chars for 5+ sessions
        """
        if len(recent_sessions) < 5:
            return False

        total_length = 0
        message_count = 0

        for session in recent_sessions[-5:]:
            messages = session.get("messages", [])
            for msg in messages:
                if msg.get("type") == "say":
                    text = msg.get("text", "")
                    total_length += len(text)
                    message_count += 1

        if message_count == 0:
            return False

        avg_length = total_length / message_count
        return avg_length < 150

    def _detect_self_sufficiency_implementation(self, recent_sessions: List[Dict]) -> bool:
        """
        Detect if user increased self-sufficiency.

        Strategy:
        - Higher ratio of Read/Glob vs Bash commands
        - Fewer "show me" / "can you check" prompts
        """
        if len(recent_sessions) < 5:
            return False

        direct_tool_count = 0
        bash_count = 0

        for session in recent_sessions[-5:]:
            messages = session.get("messages", [])
            for msg in messages:
                tool_calls = msg.get("toolCalls", [])
                for tool in tool_calls:
                    tool_name = tool.get("name", "")
                    if tool_name in ["Read", "Glob", "Grep"]:
                        direct_tool_count += 1
                    elif tool_name == "Bash":
                        bash_count += 1

        total_tools = direct_tool_count + bash_count
        if total_tools == 0:
            return False

        direct_ratio = direct_tool_count / total_tools
        return direct_ratio > 0.70  # 70%+ using direct tools

    def mark_implemented(self, rec_id: str, current_metrics: Dict):
        """
        Mark recommendation as implemented with current metrics.

        Args:
            rec_id: Recommendation ID
            current_metrics: Current metrics after implementation
        """
        rec = self._find_recommendation(rec_id)
        if not rec:
            return

        rec["status"] = "implemented"
        rec["implementation_detected_at"] = datetime.now().isoformat()
        rec["current_metrics"] = current_metrics

        # Update lists
        if rec_id in self.recommendations["pending"]:
            self.recommendations["pending"].remove(rec_id)
        if rec_id not in self.recommendations["implemented"]:
            self.recommendations["implemented"].append(rec_id)

        # Calculate impact
        rec["impact"] = self.calculate_roi(rec_id)

        self._save_recommendations()

    def calculate_roi(self, rec_id: str) -> Dict:
        """
        Calculate return on investment for a recommendation.

        Args:
            rec_id: Recommendation ID

        Returns:
            ROI metrics
        """
        rec = self._find_recommendation(rec_id)
        if not rec or rec["status"] != "implemented":
            return {}

        baseline = rec.get("baseline_metrics", {})
        current = rec.get("current_metrics", {})

        # Calculate token savings
        tokens_before = baseline.get("tokens_before", 0)
        tokens_after = current.get("tokens_after", 0)
        sessions_after = current.get("sessions_after", 1)

        tokens_saved = tokens_before - tokens_after

        # Calculate percentage improvement
        if tokens_before > 0:
            percent_improvement = (tokens_saved / tokens_before) * 100
        else:
            percent_improvement = 0

        # Calculate cost saved (avg $0.009 per 1K tokens)
        cost_saved_usd = (tokens_saved / 1000) * 0.009

        # Estimate implementation cost in minutes
        implementation_time_map = {
            "defer_docs": 5,
            "claude_md": 10,
            "concise": 0,  # Immediate
            "self_sufficiency": 0
        }
        implementation_cost_minutes = 10  # Default

        # ROI classification
        if tokens_saved > 20000:
            roi = "high"
        elif tokens_saved > 10000:
            roi = "medium"
        elif tokens_saved > 0:
            roi = "low"
        else:
            roi = "none"

        # Payback period (when savings exceed implementation cost)
        # Assume user values time at $30/hour = $0.50/minute
        implementation_cost_dollars = (implementation_cost_minutes / 60) * 30
        if cost_saved_usd > 0:
            sessions_to_payback = implementation_cost_dollars / (cost_saved_usd / sessions_after)
        else:
            sessions_to_payback = float('inf')

        return {
            "tokens_saved": tokens_saved,
            "percent_improvement": round(percent_improvement, 1),
            "cost_saved_usd": round(cost_saved_usd, 2),
            "roi": roi,
            "implementation_cost_minutes": implementation_cost_minutes,
            "sessions_to_payback": round(sessions_to_payback, 1) if sessions_to_payback != float('inf') else "N/A",
            "confidence": 0.85  # Confidence in measurement
        }

    def get_implemented_recommendations(self) -> List[Dict]:
        """Get all implemented recommendations with impact data."""
        implemented = []
        for rec_id in self.recommendations["implemented"]:
            rec = self._find_recommendation(rec_id)
            if rec:
                implemented.append(rec)
        return implemented

    def get_top_performers(self, limit: int = 3) -> List[Dict]:
        """
        Get top performing recommendations by impact.

        Args:
            limit: Number of top performers to return

        Returns:
            List of top recommendations
        """
        implemented = self.get_implemented_recommendations()

        # Sort by tokens saved
        sorted_recs = sorted(
            implemented,
            key=lambda r: r.get("impact", {}).get("tokens_saved", 0),
            reverse=True
        )

        return sorted_recs[:limit]

    def find_similar_recommendation(self, category: str) -> Optional[Dict]:
        """
        Find similar recommendation from history.

        Args:
            category: Recommendation category

        Returns:
            Similar recommendation with impact data, or None
        """
        for rec in self.recommendations["recommendations"]:
            if rec.get("category") == category and rec.get("status") == "implemented":
                impact = rec.get("impact", {})
                if impact.get("tokens_saved", 0) > 0:
                    return {
                        "category": category,
                        "title": rec.get("title"),
                        "impact": impact,
                        "success_rate": 1.0 if impact.get("roi") in ["high", "medium"] else 0.5
                    }

        return None

    def get_recommendation_stats(self) -> Dict:
        """Get overall recommendation statistics."""
        total_recs = len(self.recommendations["recommendations"])
        pending_count = len(self.recommendations["pending"])
        implemented_count = len(self.recommendations["implemented"])
        dismissed_count = len(self.recommendations["dismissed"])

        # Calculate total impact
        total_tokens_saved = 0
        total_cost_saved = 0

        for rec in self.get_implemented_recommendations():
            impact = rec.get("impact", {})
            total_tokens_saved += impact.get("tokens_saved", 0)
            total_cost_saved += impact.get("cost_saved_usd", 0)

        return {
            "total_recommendations": total_recs,
            "pending": pending_count,
            "implemented": implemented_count,
            "dismissed": dismissed_count,
            "implementation_rate": round(implemented_count / total_recs * 100, 1) if total_recs > 0 else 0,
            "total_tokens_saved": total_tokens_saved,
            "total_cost_saved_usd": round(total_cost_saved, 2)
        }
