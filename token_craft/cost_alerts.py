"""
Cost Alerts Module

Provides real-time cost tracking and budget alerts.
"""

from typing import Dict, Optional
from datetime import datetime, date
from pathlib import Path
import json


class CostAlerts:
    """Manage cost tracking and budget alerts."""

    def __init__(self, user_profile_path: Optional[Path] = None):
        """
        Initialize cost alerts.

        Args:
            user_profile_path: Path to user_profile.json
        """
        if user_profile_path is None:
            user_profile_path = Path.home() / ".claude" / "token-craft" / "user_profile.json"

        self.profile_path = user_profile_path
        self.config = self._load_budget_config()

    def _load_budget_config(self) -> Dict:
        """Load budget configuration from user profile."""
        default_config = {
            "daily_budget": 5.00,
            "monthly_budget": 100.00,
            "alerts_enabled": True,
            "alert_threshold": 0.80  # Alert at 80%
        }

        if not self.profile_path.exists():
            return default_config

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                return profile.get("budget_config", default_config)
        except Exception:
            return default_config

    def calculate_session_cost(self, tokens: int, model: str = "claude-sonnet-4-5") -> Dict:
        """
        Calculate cost for a session.

        Args:
            tokens: Total tokens used
            model: Model name

        Returns:
            Dict with cost breakdown
        """
        # Model pricing (per million tokens)
        pricing = {
            "claude-sonnet-4-5": {
                "input": 3.00,
                "output": 15.00,
                "avg": 9.00  # Assume 30% input, 70% output
            },
            "claude-opus-4-6": {
                "input": 15.00,
                "output": 75.00,
                "avg": 45.00
            },
            "claude-haiku-4-5": {
                "input": 0.80,
                "output": 4.00,
                "avg": 2.40
            }
        }

        model_price = pricing.get(model, pricing["claude-sonnet-4-5"])
        cost = (tokens / 1_000_000) * model_price["avg"]

        return {
            "cost": round(cost, 4),
            "tokens": tokens,
            "model": model,
            "price_per_million": model_price["avg"]
        }

    def get_daily_usage(self) -> Dict:
        """
        Get today's usage and budget status.

        Returns:
            Dict with daily usage info
        """
        # Load snapshots from today
        snapshot_dir = self.profile_path.parent / "snapshots"
        today_str = date.today().strftime("%Y%m%d")

        daily_cost = 0.0
        session_count = 0

        if snapshot_dir.exists():
            for snapshot_file in snapshot_dir.glob(f"snapshot_{today_str}_*.json"):
                try:
                    with open(snapshot_file, 'r', encoding='utf-8') as f:
                        snapshot = json.load(f)
                        profile = snapshot.get("profile", {})
                        tokens = profile.get("total_tokens", 0)
                        cost_info = self.calculate_session_cost(tokens)
                        daily_cost = cost_info["cost"]
                        session_count = profile.get("total_sessions", 0)
                        break  # Use latest snapshot
                except Exception:
                    continue

        daily_budget = self.config["daily_budget"]
        budget_used_pct = (daily_cost / daily_budget * 100) if daily_budget > 0 else 0

        return {
            "daily_cost": round(daily_cost, 2),
            "daily_budget": daily_budget,
            "budget_used_pct": round(budget_used_pct, 1),
            "budget_remaining": round(daily_budget - daily_cost, 2),
            "session_count": session_count,
            "avg_cost_per_session": round(daily_cost / session_count, 2) if session_count > 0 else 0
        }

    def get_monthly_projection(self, avg_daily_cost: float) -> Dict:
        """
        Calculate monthly cost projection.

        Args:
            avg_daily_cost: Average daily cost

        Returns:
            Dict with monthly projection
        """
        days_in_month = 30
        monthly_projection = avg_daily_cost * days_in_month
        monthly_budget = self.config["monthly_budget"]
        budget_used_pct = (monthly_projection / monthly_budget * 100) if monthly_budget > 0 else 0

        return {
            "monthly_projection": round(monthly_projection, 2),
            "monthly_budget": monthly_budget,
            "projection_pct": round(budget_used_pct, 1),
            "on_track": budget_used_pct <= 100
        }

    def check_alerts(self, daily_usage: Dict) -> list:
        """
        Check if any budget alerts should be triggered.

        Args:
            daily_usage: Daily usage dict from get_daily_usage()

        Returns:
            List of alert messages
        """
        if not self.config["alerts_enabled"]:
            return []

        alerts = []
        threshold = self.config["alert_threshold"]
        budget_used = daily_usage["budget_used_pct"] / 100

        if budget_used >= 1.0:
            alerts.append({
                "level": "critical",
                "message": f"⚠️  Daily budget EXCEEDED: ${daily_usage['daily_cost']:.2f} / ${daily_usage['daily_budget']:.2f}"
            })
        elif budget_used >= 0.90:
            alerts.append({
                "level": "warning",
                "message": f"⚠️  Alert: 90% of daily budget used (${daily_usage['daily_cost']:.2f})"
            })
        elif budget_used >= threshold:
            alerts.append({
                "level": "info",
                "message": f"ℹ️  Notice: {budget_used*100:.0f}% of daily budget used (${daily_usage['daily_cost']:.2f})"
            })

        return alerts

    def format_cost_summary(self, total_tokens: int, avg_tokens_per_session: float, total_sessions: int) -> str:
        """
        Format cost summary for terminal display.

        Args:
            total_tokens: Total tokens used
            avg_tokens_per_session: Average tokens per session
            total_sessions: Total number of sessions

        Returns:
            Formatted cost summary string
        """
        # Calculate costs
        session_cost_info = self.calculate_session_cost(int(avg_tokens_per_session))
        total_cost_info = self.calculate_session_cost(total_tokens)

        # Get daily usage
        daily_usage = self.get_daily_usage()

        # Get monthly projection
        monthly_proj = self.get_monthly_projection(daily_usage["avg_cost_per_session"])

        # Check for alerts
        alerts = self.check_alerts(daily_usage)

        # Build summary
        lines = []
        lines.append("Cost Analysis:")
        lines.append("─" * 70)
        lines.append(f"  Current Session (est):    ${session_cost_info['cost']:.4f}")
        lines.append(f"  Total All Sessions:       ${total_cost_info['cost']:.2f}")
        lines.append(f"  Avg Cost per Session:     ${session_cost_info['cost']:.4f}")
        lines.append("")
        lines.append(f"  Today's Usage:            ${daily_usage['daily_cost']:.2f} / ${daily_usage['daily_budget']:.2f}")
        lines.append(f"  Budget Remaining:         ${daily_usage['budget_remaining']:.2f}")
        lines.append(f"  Monthly Projection:       ${monthly_proj['monthly_projection']:.2f}")

        if monthly_proj["on_track"]:
            lines.append(f"  Status:                   ✅ On track")
        else:
            lines.append(f"  Status:                   ⚠️  Over budget ({monthly_proj['projection_pct']:.0f}%)")

        # Add alerts if any
        if alerts:
            lines.append("")
            lines.append("Alerts:")
            for alert in alerts:
                lines.append(f"  {alert['message']}")

        return "\n".join(lines)

    def format_cost_dashboard(self, total_tokens: int, total_sessions: int, avg_tokens_per_session: float) -> str:
        """
        Format comprehensive cost dashboard.

        Args:
            total_tokens: Total tokens used
            total_sessions: Total sessions
            avg_tokens_per_session: Average tokens per session

        Returns:
            Formatted dashboard string
        """
        # Session cost
        session_cost = self.calculate_session_cost(int(avg_tokens_per_session))

        # Daily usage
        daily = self.get_daily_usage()

        # Monthly projection
        monthly = self.get_monthly_projection(daily["avg_cost_per_session"])

        # Check alerts
        alerts = self.check_alerts(daily)

        # Build dashboard
        lines = []
        lines.append("═" * 70)
        lines.append("                      COST TRACKING DASHBOARD                      ")
        lines.append("═" * 70)
        lines.append("")

        # Current Session
        lines.append("Current Session:")
        lines.append(f"  Avg Tokens:      {int(avg_tokens_per_session):,}")
        lines.append(f"  Estimated Cost:  ${session_cost['cost']:.4f}")
        lines.append("")

        # Daily Budget
        budget_bar = self._create_progress_bar(daily["budget_used_pct"], 100)
        lines.append("Daily Budget:")
        lines.append(f"  {budget_bar} {daily['budget_used_pct']:.0f}%")
        lines.append(f"  Used:      ${daily['daily_cost']:.2f} / ${daily['daily_budget']:.2f}")
        lines.append(f"  Remaining: ${daily['budget_remaining']:.2f}")
        lines.append("")

        # Monthly Projection
        proj_bar = self._create_progress_bar(monthly["projection_pct"], 100)
        lines.append("Monthly Projection:")
        lines.append(f"  {proj_bar} {monthly['projection_pct']:.0f}%")
        lines.append(f"  Projected: ${monthly['monthly_projection']:.2f} / ${monthly['monthly_budget']:.2f}")
        lines.append(f"  Status:    {'✅ On track' if monthly['on_track'] else '⚠️  Over budget'}")
        lines.append("")

        # Alerts
        if alerts:
            lines.append("⚠️  Active Alerts:")
            for alert in alerts:
                lines.append(f"  • {alert['message']}")
            lines.append("")

        lines.append("═" * 70)

        return "\n".join(lines)

    def _create_progress_bar(self, value: float, max_value: float, width: int = 30) -> str:
        """Create ASCII progress bar."""
        pct = min(value / max_value, 1.0)
        filled = int(width * pct)
        empty = width - filled

        # Color coding
        if pct >= 1.0:
            bar_char = "█"
        elif pct >= 0.9:
            bar_char = "▓"
        elif pct >= 0.8:
            bar_char = "▒"
        else:
            bar_char = "█"

        bar = bar_char * filled + "░" * empty
        return f"[{bar}]"
