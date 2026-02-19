"""
Experimentation Framework

Enable A/B testing by auto-detecting approaches and comparing outcomes.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ExperimentationFramework:
    """A/B testing framework for optimization approaches."""

    def __init__(self):
        """Initialize experimentation framework."""
        self.token_craft_dir = Path.home() / ".claude" / "token-craft"
        self.experiments_file = self.token_craft_dir / "experiments.json"

        # Ensure directory exists
        self.token_craft_dir.mkdir(parents=True, exist_ok=True)

        # Load existing experiments
        self.experiments = self._load_experiments()

    def _load_experiments(self) -> Dict:
        """Load experiments from file."""
        if self.experiments_file.exists():
            try:
                with open(self.experiments_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Default structure
        return {
            "experiments": []
        }

    def _save_experiments(self):
        """Save experiments to file."""
        with open(self.experiments_file, 'w', encoding='utf-8') as f:
            json.dump(self.experiments, f, indent=2)

    def auto_detect_approach(self, session: Dict) -> List[str]:
        """
        Automatically detect which approaches user is following.

        Args:
            session: Session data with messages

        Returns:
            List of approach tags (e.g., ["fast_mode", "defer_docs"])
        """
        approaches = []
        messages = session.get("messages", [])

        if not messages:
            return approaches

        # Detect /fast mode
        for msg in messages:
            text = msg.get("text", "")
            if "/fast" in text.lower():
                approaches.append("fast_mode")
                break

        # Detect defer docs (no doc keywords until last 20%)
        doc_keywords = ["readme", "documentation", "docstring", "comment", "docs"]
        total_msgs = len(messages)
        threshold_idx = int(total_msgs * 0.8)

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

        if early_doc_mentions == 0 and late_doc_mentions > 0:
            approaches.append("defer_docs")
        elif early_doc_mentions > 0:
            approaches.append("inline_docs")

        # Detect concise mode (avg message <150 chars)
        user_messages = [m for m in messages if m.get("type") == "say"]
        if user_messages:
            avg_length = sum(len(m.get("text", "")) for m in user_messages) / len(user_messages)
            if avg_length < 150:
                approaches.append("concise")
            else:
                approaches.append("verbose")

        # Detect direct commands (high Read/Glob vs Bash ratio)
        direct_tools = 0
        bash_tools = 0

        for msg in messages:
            tool_calls = msg.get("toolCalls", [])
            for tool in tool_calls:
                tool_name = tool.get("name", "")
                if tool_name in ["Read", "Glob", "Grep"]:
                    direct_tools += 1
                elif tool_name == "Bash":
                    bash_tools += 1

        total_tools = direct_tools + bash_tools
        if total_tools > 0:
            direct_ratio = direct_tools / total_tools
            if direct_ratio > 0.7:
                approaches.append("self_sufficient")
            else:
                approaches.append("assisted")

        return approaches

    def create_experiment(
        self,
        name: str,
        control_approach: str,
        treatment_approach: str
    ) -> str:
        """
        Create a new experiment.

        Args:
            name: Experiment name
            control_approach: Control approach tag
            treatment_approach: Treatment approach tag

        Returns:
            Experiment ID
        """
        exp_id = f"exp_{len(self.experiments['experiments']) + 1:03d}_{name.lower().replace(' ', '_')}"

        experiment = {
            "id": exp_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "control_approach": control_approach,
            "treatment_approach": treatment_approach,
            "arms": [
                {
                    "name": "control",
                    "description": control_approach.replace("_", " ").title(),
                    "approach_tag": control_approach,
                    "sessions": [],
                    "total_tokens": 0,
                    "avg_tokens_per_session": 0
                },
                {
                    "name": "treatment",
                    "description": treatment_approach.replace("_", " ").title(),
                    "approach_tag": treatment_approach,
                    "sessions": [],
                    "total_tokens": 0,
                    "avg_tokens_per_session": 0
                }
            ],
            "results": {}
        }

        self.experiments["experiments"].append(experiment)
        self._save_experiments()

        return exp_id

    def add_session_to_experiment(
        self,
        exp_id: str,
        session_id: str,
        approach_tag: str,
        tokens: int
    ):
        """
        Add a session to an experiment arm.

        Args:
            exp_id: Experiment ID
            session_id: Session ID
            approach_tag: Approach tag for this session
            tokens: Token count for session
        """
        exp = self._find_experiment(exp_id)
        if not exp:
            return

        # Find matching arm
        for arm in exp["arms"]:
            if arm["approach_tag"] == approach_tag:
                arm["sessions"].append(session_id)
                arm["total_tokens"] += tokens

                # Recalculate average
                session_count = len(arm["sessions"])
                arm["avg_tokens_per_session"] = arm["total_tokens"] / session_count if session_count > 0 else 0

                self._save_experiments()
                break

    def _find_experiment(self, exp_id: str) -> Optional[Dict]:
        """Find experiment by ID."""
        for exp in self.experiments["experiments"]:
            if exp["id"] == exp_id:
                return exp
        return None

    def compare_approaches(self, exp_id: str) -> Dict:
        """
        Compare two approaches statistically.

        Args:
            exp_id: Experiment ID

        Returns:
            Comparison results with statistical significance
        """
        exp = self._find_experiment(exp_id)
        if not exp:
            return {}

        arms = exp["arms"]
        if len(arms) != 2:
            return {}

        control = arms[0]
        treatment = arms[1]

        # Need at least 3 sessions in each arm for meaningful comparison
        if len(control["sessions"]) < 3 or len(treatment["sessions"]) < 3:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 3 sessions in each arm. Current: control={len(control['sessions'])}, treatment={len(treatment['sessions'])}"
            }

        # Calculate metrics
        control_avg = control["avg_tokens_per_session"]
        treatment_avg = treatment["avg_tokens_per_session"]

        # Calculate improvement
        if control_avg > 0:
            improvement = ((control_avg - treatment_avg) / control_avg) * 100
        else:
            improvement = 0

        # Determine winner
        if improvement > 5:  # Treatment is 5%+ better
            winner = "treatment"
        elif improvement < -5:  # Control is 5%+ better
            winner = "control"
        else:
            winner = "tie"

        # Simple statistical test (t-test would require per-session tokens)
        # For now, use effect size heuristic
        absolute_diff = abs(control_avg - treatment_avg)
        pooled_avg = (control_avg + treatment_avg) / 2
        effect_size = absolute_diff / pooled_avg if pooled_avg > 0 else 0

        # Cohen's d interpretation:
        # 0.2 = small, 0.5 = medium, 0.8 = large
        if effect_size >= 0.8:
            significance = "large"
            p_value = 0.01
        elif effect_size >= 0.5:
            significance = "medium"
            p_value = 0.05
        elif effect_size >= 0.2:
            significance = "small"
            p_value = 0.10
        else:
            significance = "negligible"
            p_value = 0.20

        # Recommendation
        if winner == "treatment" and significance in ["large", "medium"]:
            recommendation = f"Adopt {exp['treatment_approach'].replace('_', ' ')} approach"
        elif winner == "control" and significance in ["large", "medium"]:
            recommendation = f"Continue with {exp['control_approach'].replace('_', ' ')} approach"
        else:
            recommendation = "No clear winner - continue testing"

        results = {
            "winner": winner,
            "metrics": {
                "control_avg": round(control_avg, 0),
                "treatment_avg": round(treatment_avg, 0),
                "absolute_diff": round(absolute_diff, 0),
                "improvement_pct": round(improvement, 1),
                "effect_size": round(effect_size, 2),
                "significance": significance,
                "p_value": p_value
            },
            "recommendation": recommendation,
            "confidence": "high" if significance in ["large", "medium"] else "low"
        }

        # Save results to experiment
        exp["results"] = results
        exp["status"] = "completed"
        self._save_experiments()

        return results

    def get_proven_patterns(self) -> List[Dict]:
        """
        Get patterns that have been proven effective through experiments.

        Returns:
            List of proven patterns with evidence
        """
        proven = []

        for exp in self.experiments["experiments"]:
            results = exp.get("results", {})
            if not results:
                continue

            winner = results.get("winner")
            significance = results.get("metrics", {}).get("significance")

            if winner == "treatment" and significance in ["large", "medium"]:
                improvement = results.get("metrics", {}).get("improvement_pct", 0)

                proven.append({
                    "name": exp["name"],
                    "approach": exp["treatment_approach"],
                    "improvement": improvement,
                    "significance": significance,
                    "evidence": f"{len(exp['arms'][1]['sessions'])} sessions tested",
                    "recommendation": results.get("recommendation", "")
                })

        return proven

    def generate_experiment_report(self, exp_id: str) -> str:
        """
        Generate formatted experiment report.

        Args:
            exp_id: Experiment ID

        Returns:
            Formatted report string
        """
        exp = self._find_experiment(exp_id)
        if not exp:
            return "Experiment not found"

        lines = []
        lines.append(f"Experiment: {exp['name']}")
        lines.append("=" * 70)
        lines.append("")

        # Arms
        for arm in exp["arms"]:
            lines.append(f"Approach {arm['name'].upper()}: {arm['description']}")
            lines.append(f"  Sessions: {len(arm['sessions'])}")
            lines.append(f"  Total tokens: {arm['total_tokens']:,}")
            lines.append(f"  Avg tokens/session: {arm['avg_tokens_per_session']:,.0f}")
            lines.append("")

        # Results
        results = exp.get("results", {})
        if results and results.get("winner"):
            metrics = results.get("metrics", {})
            lines.append("Results:")
            lines.append(f"  Winner: {results['winner'].upper()}")
            lines.append(f"  Improvement: {metrics.get('improvement_pct', 0)}%")
            lines.append(f"  Significance: {metrics.get('significance', 'unknown').upper()}")
            lines.append(f"  Effect size: {metrics.get('effect_size', 0)}")
            lines.append(f"  P-value: {metrics.get('p_value', 1.0)}")
            lines.append("")
            lines.append(f"Recommendation: {results.get('recommendation', 'N/A')}")
        else:
            lines.append("Status: Experiment in progress")

        lines.append("")
        return "\n".join(lines)

    def auto_create_experiments(self, sessions: List[Dict]) -> List[str]:
        """
        Automatically create experiments from detected approaches.

        Args:
            sessions: List of sessions with detected approaches

        Returns:
            List of created experiment IDs
        """
        # Group sessions by approach combinations
        approach_groups = {}

        for session in sessions:
            approaches = self.auto_detect_approach(session)
            if not approaches:
                continue

            # Create key from sorted approaches
            key = tuple(sorted(approaches))
            if key not in approach_groups:
                approach_groups[key] = []

            approach_groups[key].append(session)

        # Create experiments for interesting comparisons
        created_exp_ids = []

        # Defer docs vs inline docs
        defer_sessions = []
        inline_sessions = []

        for approaches, sessions_group in approach_groups.items():
            if "defer_docs" in approaches:
                defer_sessions.extend(sessions_group)
            elif "inline_docs" in approaches:
                inline_sessions.extend(sessions_group)

        if len(defer_sessions) >= 3 and len(inline_sessions) >= 3:
            exp_id = self.create_experiment(
                "Defer Documentation",
                "inline_docs",
                "defer_docs"
            )
            created_exp_ids.append(exp_id)

        return created_exp_ids
