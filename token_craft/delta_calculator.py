"""
Delta Calculator

Calculates and formats changes between snapshots.
"""

from typing import Dict, Optional


class DeltaCalculator:
    """Calculate deltas between snapshots."""

    @staticmethod
    def calculate_delta(current: Dict, previous: Dict) -> Dict:
        """
        Calculate changes between two snapshots.

        Args:
            current: Current snapshot data
            previous: Previous snapshot data

        Returns:
            Dict with delta information
        """
        delta = {
            "score_change": 0,
            "rank_change": None,
            "category_changes": {},
            "metric_changes": {},
            "time_delta": None
        }

        # Score change
        current_score = current.get("scores", {}).get("total_score", 0)
        previous_score = previous.get("scores", {}).get("total_score", 0)
        delta["score_change"] = current_score - previous_score

        # Rank change
        current_rank = current.get("rank", {}).get("name", "Unknown")
        previous_rank = previous.get("rank", {}).get("name", "Unknown")
        if current_rank != previous_rank:
            delta["rank_change"] = {
                "from": previous_rank,
                "to": current_rank,
                "promoted": DeltaCalculator._is_promotion(previous_rank, current_rank)
            }

        # Category changes
        current_breakdown = current.get("scores", {}).get("breakdown", {})
        previous_breakdown = previous.get("scores", {}).get("breakdown", {})

        for category in ["token_efficiency", "optimization_adoption", "self_sufficiency",
                        "improvement_trend", "best_practices"]:
            current_cat_score = current_breakdown.get(category, {}).get("score", 0)
            previous_cat_score = previous_breakdown.get(category, {}).get("score", 0)
            change = current_cat_score - previous_cat_score

            delta["category_changes"][category] = {
                "current": current_cat_score,
                "previous": previous_cat_score,
                "change": change,
                "change_pct": (change / previous_cat_score * 100) if previous_cat_score > 0 else 0
            }

        # Metric changes
        current_profile = current.get("profile", {})
        previous_profile = previous.get("profile", {})

        metrics = {
            "avg_tokens_per_session": "Average tokens/session",
            "total_sessions": "Total sessions",
            "total_tokens": "Total tokens"
        }

        for metric_key, metric_name in metrics.items():
            current_value = current_profile.get(metric_key, 0)
            previous_value = previous_profile.get(metric_key, 0)
            change = current_value - previous_value

            delta["metric_changes"][metric_key] = {
                "name": metric_name,
                "current": current_value,
                "previous": previous_value,
                "change": change,
                "change_pct": (change / previous_value * 100) if previous_value > 0 else 0
            }

        # Time delta
        from datetime import datetime
        try:
            current_time = datetime.fromisoformat(current.get("timestamp", ""))
            previous_time = datetime.fromisoformat(previous.get("timestamp", ""))
            time_diff = current_time - previous_time
            delta["time_delta"] = {
                "days": time_diff.days,
                "hours": time_diff.seconds // 3600,
                "total_hours": time_diff.total_seconds() / 3600
            }
        except Exception:
            delta["time_delta"] = None

        return delta

    @staticmethod
    def _is_promotion(from_rank: str, to_rank: str) -> bool:
        """Check if rank change is a promotion."""
        rank_order = [
            "Cadet", "Pilot", "Navigator", "Commander",
            "Captain", "Admiral", "Galactic Legend"
        ]

        try:
            from_index = rank_order.index(from_rank)
            to_index = rank_order.index(to_rank)
            return to_index > from_index
        except ValueError:
            return False

    @staticmethod
    def format_delta(delta: Dict) -> str:
        """
        Format delta for display with arrows and colors.

        Args:
            delta: Delta data from calculate_delta()

        Returns:
            Formatted string
        """
        lines = []

        # Score change
        score_change = delta.get("score_change", 0)
        if score_change > 0:
            lines.append(f"Score: +{score_change:.1f} points (UP)")
        elif score_change < 0:
            lines.append(f"Score: {score_change:.1f} points (DOWN)")
        else:
            lines.append("Score: No change (SAME)")

        # Rank change
        rank_change = delta.get("rank_change")
        if rank_change:
            if rank_change["promoted"]:
                lines.append(f"Rank: {rank_change['from']} -> {rank_change['to']} (PROMOTED!)")
            else:
                lines.append(f"Rank: {rank_change['from']} -> {rank_change['to']} (DEMOTED)")
        else:
            lines.append("Rank: No change")

        # Time since last snapshot
        time_delta = delta.get("time_delta")
        if time_delta:
            if time_delta["days"] > 0:
                lines.append(f"Time since last check: {time_delta['days']} days")
            else:
                lines.append(f"Time since last check: {time_delta['hours']} hours")

        # Category changes (top 3)
        category_changes = delta.get("category_changes", {})
        sorted_categories = sorted(
            category_changes.items(),
            key=lambda x: abs(x[1]["change"]),
            reverse=True
        )

        lines.append("\nBiggest Changes:")
        for i, (category, data) in enumerate(sorted_categories[:3], 1):
            category_name = category.replace("_", " ").title()
            change = data["change"]
            arrow = "UP" if change > 0 else "DOWN" if change < 0 else "SAME"
            lines.append(f"  {i}. {category_name}: {change:+.1f} ({arrow})")

        return "\n".join(lines)

    @staticmethod
    def get_improvement_summary(delta: Dict) -> str:
        """
        Get a brief improvement summary.

        Args:
            delta: Delta data

        Returns:
            One-line summary
        """
        score_change = delta.get("score_change", 0)
        rank_change = delta.get("rank_change")

        if rank_change and rank_change["promoted"]:
            return f"Promoted to {rank_change['to']}! (+{score_change:.0f} points)"
        elif rank_change and not rank_change["promoted"]:
            return f"Demoted to {rank_change['to']}. ({score_change:.0f} points)"
        elif score_change > 50:
            return f"Great progress! +{score_change:.0f} points"
        elif score_change > 0:
            return f"Steady improvement: +{score_change:.0f} points"
        elif score_change == 0:
            return "Maintaining current level"
        elif score_change > -50:
            return f"Slight decline: {score_change:.0f} points"
        else:
            return f"Significant decline: {score_change:.0f} points"
