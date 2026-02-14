"""
Pattern Library

Build evidence-based library of optimization patterns with success tracking.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class PatternLibrary:
    """Evidence-based pattern collection with validation."""

    def __init__(self):
        """Initialize pattern library."""
        self.token_craft_dir = Path.home() / ".claude" / "token-craft"
        self.patterns_file = self.token_craft_dir / "patterns.json"

        # Ensure directory exists
        self.token_craft_dir.mkdir(parents=True, exist_ok=True)

        # Load existing patterns
        self.patterns = self._load_patterns()

        # Seed with known patterns if empty
        if not self.patterns["patterns"]:
            self._seed_default_patterns()

    def _load_patterns(self) -> Dict:
        """Load patterns from file."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Default structure
        return {
            "patterns": [],
            "version": "1.0"
        }

    def _save_patterns(self):
        """Save patterns to file."""
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, indent=2)

    def _seed_default_patterns(self):
        """Seed library with known optimization patterns."""
        default_patterns = [
            {
                "id": "pattern_defer_docs",
                "name": "Defer Documentation",
                "category": "workflow",
                "description": "Delay all documentation until code is ready to push",
                "evidence": {
                    "trials": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "avg_improvement": 0.0,
                    "confidence": 0.0
                },
                "examples": [],
                "implementation_guide": {
                    "setup_steps": [
                        "Add 'Defer documentation until ready to push' to CLAUDE.md",
                        "Use phrases like 'skip docs for now' in prompts"
                    ],
                    "validation_criteria": "No doc-related tokens in first 80% of sessions",
                    "expected_roi": "25-35% token savings"
                },
                "retirement_criteria": {
                    "min_trials": 10,
                    "min_success_rate": 0.70
                },
                "status": "experimental",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "pattern_claude_md",
                "name": "CLAUDE.md Setup",
                "category": "configuration",
                "description": "Create CLAUDE.md files in projects with context and preferences",
                "evidence": {
                    "trials": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "avg_improvement": 0.0,
                    "confidence": 0.0
                },
                "examples": [],
                "implementation_guide": {
                    "setup_steps": [
                        "Create CLAUDE.md in project root",
                        "Add project overview, tech stack, coding preferences"
                    ],
                    "validation_criteria": "CLAUDE.md exists and is >500 bytes",
                    "expected_roi": "1500-2500 tokens saved per session"
                },
                "retirement_criteria": {
                    "min_trials": 10,
                    "min_success_rate": 0.70
                },
                "status": "experimental",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "pattern_concise_prompts",
                "name": "Concise Prompts",
                "category": "communication",
                "description": "Use short, direct prompts without pleasantries",
                "evidence": {
                    "trials": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "avg_improvement": 0.0,
                    "confidence": 0.0
                },
                "examples": [],
                "implementation_guide": {
                    "setup_steps": [
                        "Remove 'please', 'could you', 'thank you' from prompts",
                        "Be direct: 'Edit file.py' vs 'Could you please edit file.py'"
                    ],
                    "validation_criteria": "Avg message length <150 chars",
                    "expected_roi": "10-20% token savings on inputs"
                },
                "retirement_criteria": {
                    "min_trials": 10,
                    "min_success_rate": 0.70
                },
                "status": "experimental",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "pattern_fast_mode",
                "name": "Fast Mode Usage",
                "category": "efficiency",
                "description": "Use /fast mode for simple, straightforward tasks",
                "evidence": {
                    "trials": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "success_rate": 0.0,
                    "avg_improvement": 0.0,
                    "confidence": 0.0
                },
                "examples": [],
                "implementation_guide": {
                    "setup_steps": [
                        "Type /fast before simple tasks",
                        "Use for file edits, simple debugging, quick queries"
                    ],
                    "validation_criteria": "Sessions with /fast have lower token usage",
                    "expected_roi": "Faster responses, potentially lower tokens"
                },
                "retirement_criteria": {
                    "min_trials": 10,
                    "min_success_rate": 0.70
                },
                "status": "experimental",
                "created_at": datetime.now().isoformat()
            }
        ]

        self.patterns["patterns"].extend(default_patterns)
        self._save_patterns()

    def _find_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Find pattern by ID."""
        for pattern in self.patterns["patterns"]:
            if pattern["id"] == pattern_id:
                return pattern
        return None

    def record_trial(
        self,
        pattern_id: str,
        success: bool,
        before_tokens: int,
        after_tokens: int,
        session_id: str,
        details: str = ""
    ):
        """
        Record a trial of a pattern.

        Args:
            pattern_id: Pattern ID
            success: Whether trial was successful
            before_tokens: Tokens before applying pattern
            after_tokens: Tokens after applying pattern
            session_id: Session ID for this trial
            details: Additional details about the trial
        """
        pattern = self._find_pattern(pattern_id)
        if not pattern:
            return

        # Update evidence
        evidence = pattern["evidence"]
        evidence["trials"] += 1

        if success:
            evidence["success_count"] += 1
        else:
            evidence["failure_count"] += 1

        # Recalculate success rate
        evidence["success_rate"] = evidence["success_count"] / evidence["trials"]

        # Calculate improvement for this trial
        if before_tokens > 0:
            improvement = ((before_tokens - after_tokens) / before_tokens) * 100
        else:
            improvement = 0

        # Update average improvement (only from successful trials)
        if success:
            # Weighted average
            current_avg = evidence.get("avg_improvement", 0)
            success_count = evidence["success_count"]
            new_avg = ((current_avg * (success_count - 1)) + improvement) / success_count
            evidence["avg_improvement"] = round(new_avg, 1)

        # Update confidence (based on sample size and consistency)
        if evidence["trials"] >= 10:
            # High confidence if success rate is stable
            if evidence["success_rate"] >= 0.7:
                evidence["confidence"] = 0.90
            elif evidence["success_rate"] >= 0.5:
                evidence["confidence"] = 0.70
            else:
                evidence["confidence"] = 0.50
        else:
            # Lower confidence with fewer trials
            evidence["confidence"] = min(0.5, evidence["trials"] / 20)

        # Add example
        if success and len(pattern["examples"]) < 10:
            example = {
                "session_id": session_id,
                "before_tokens": before_tokens,
                "after_tokens": after_tokens,
                "improvement": round(improvement, 1),
                "details": details,
                "recorded_at": datetime.now().isoformat()
            }
            pattern["examples"].append(example)

        # Update status based on validation
        pattern["status"] = self._determine_pattern_status(pattern)

        self._save_patterns()

    def _determine_pattern_status(self, pattern: Dict) -> str:
        """
        Determine pattern status based on evidence.

        Returns:
            "experimental", "validated", or "deprecated"
        """
        evidence = pattern["evidence"]
        criteria = pattern["retirement_criteria"]

        min_trials = criteria.get("min_trials", 10)
        min_success_rate = criteria.get("min_success_rate", 0.70)

        # Not enough trials yet
        if evidence["trials"] < min_trials:
            return "experimental"

        # Enough trials - check success rate
        if evidence["success_rate"] >= min_success_rate:
            return "validated"
        else:
            return "deprecated"

    def validate_pattern(self, pattern_id: str) -> Dict:
        """
        Validate if a pattern actually works.

        Args:
            pattern_id: Pattern ID

        Returns:
            Validation results
        """
        pattern = self._find_pattern(pattern_id)
        if not pattern:
            return {"error": "Pattern not found"}

        evidence = pattern["evidence"]
        status = pattern["status"]

        # Calculate statistical significance (simplified)
        trials = evidence["trials"]
        success_rate = evidence["success_rate"]
        avg_improvement = evidence["avg_improvement"]

        # Simple significance test
        if trials >= 10:
            if success_rate >= 0.7 and avg_improvement >= 15:
                significance = "high"
                p_value = 0.01
            elif success_rate >= 0.6 and avg_improvement >= 10:
                significance = "medium"
                p_value = 0.05
            else:
                significance = "low"
                p_value = 0.10
        else:
            significance = "insufficient_data"
            p_value = 1.0

        recommendation = ""
        if status == "validated":
            recommendation = f"Use this pattern - proven effective ({success_rate*100:.0f}% success rate)"
        elif status == "experimental":
            recommendation = f"Continue testing ({trials}/{pattern['retirement_criteria']['min_trials']} trials)"
        else:  # deprecated
            recommendation = "Avoid this pattern - low success rate"

        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern["name"],
            "status": status,
            "trials": trials,
            "success_rate": success_rate,
            "avg_improvement": avg_improvement,
            "confidence": evidence["confidence"],
            "significance": significance,
            "p_value": p_value,
            "recommendation": recommendation
        }

    def get_validated_patterns(self) -> List[Dict]:
        """Get all validated patterns."""
        validated = []
        for pattern in self.patterns["patterns"]:
            if pattern["status"] == "validated":
                validated.append(pattern)
        return validated

    def get_top_patterns(self, limit: int = 5) -> List[Dict]:
        """
        Get top performing patterns.

        Args:
            limit: Number of patterns to return

        Returns:
            List of top patterns sorted by avg improvement
        """
        # Filter to patterns with enough evidence
        qualified = [
            p for p in self.patterns["patterns"]
            if p["evidence"]["trials"] >= 3 and p["status"] != "deprecated"
        ]

        # Sort by average improvement
        sorted_patterns = sorted(
            qualified,
            key=lambda p: p["evidence"]["avg_improvement"],
            reverse=True
        )

        return sorted_patterns[:limit]

    def discover_new_patterns(self, sessions: List[Dict]) -> List[Dict]:
        """
        Auto-discover successful patterns from usage history.

        Args:
            sessions: List of session data

        Returns:
            List of candidate patterns
        """
        candidates = []

        # Calculate average tokens across all sessions
        all_tokens = []
        for session in sessions:
            session_tokens = sum(
                msg.get("tokens", 0)
                for msg in session.get("messages", [])
            )
            if session_tokens > 0:
                all_tokens.append(session_tokens)

        if not all_tokens:
            return candidates

        avg_tokens = statistics.mean(all_tokens)

        # Find sessions with below-average tokens
        efficient_sessions = []
        for session in sessions:
            session_tokens = sum(
                msg.get("tokens", 0)
                for msg in session.get("messages", [])
            )
            if session_tokens > 0 and session_tokens < avg_tokens * 0.8:  # 20% below avg
                efficient_sessions.append(session)

        # Extract common characteristics
        if len(efficient_sessions) >= 5:
            # Check for concise prompts
            avg_msg_length = 0
            msg_count = 0
            for session in efficient_sessions:
                for msg in session.get("messages", []):
                    if msg.get("type") == "say":
                        avg_msg_length += len(msg.get("text", ""))
                        msg_count += 1

            if msg_count > 0:
                avg_msg_length = avg_msg_length / msg_count
                if avg_msg_length < 120:
                    candidates.append({
                        "name": "Ultra-Concise Prompts",
                        "category": "communication",
                        "description": f"Very short prompts (avg {avg_msg_length:.0f} chars) correlate with efficient sessions",
                        "evidence_count": len(efficient_sessions),
                        "avg_improvement": 20.0  # Estimated
                    })

        return candidates

    def generate_pattern_report(self) -> str:
        """Generate formatted pattern library report."""
        lines = []
        lines.append("Pattern Library:")
        lines.append("=" * 70)
        lines.append("")

        # Count by status
        experimental = sum(1 for p in self.patterns["patterns"] if p["status"] == "experimental")
        validated = sum(1 for p in self.patterns["patterns"] if p["status"] == "validated")
        deprecated = sum(1 for p in self.patterns["patterns"] if p["status"] == "deprecated")

        lines.append(f"Total patterns: {len(self.patterns['patterns'])}")
        lines.append(f"  Validated: {validated}")
        lines.append(f"  Experimental: {experimental}")
        lines.append(f"  Deprecated: {deprecated}")
        lines.append("")

        # Show top validated patterns
        top_patterns = self.get_top_patterns(limit=3)
        if top_patterns:
            lines.append("Top Validated Patterns:")
            lines.append("-" * 70)
            for pattern in top_patterns:
                evidence = pattern["evidence"]
                lines.append(f"  {pattern['name']}")
                lines.append(f"    Success rate: {evidence['success_rate']*100:.0f}%")
                lines.append(f"    Avg improvement: {evidence['avg_improvement']:.1f}%")
                lines.append(f"    Trials: {evidence['trials']}")
                lines.append(f"    Status: {pattern['status'].upper()}")
                lines.append("")

        return "\n".join(lines)
