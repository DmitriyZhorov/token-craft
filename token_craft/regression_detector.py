"""
Regression Detection System

Detects when users backslide on performance metrics after improvement.
Triggers difficulty adjustments to prevent gaming the system.

Regression occurs when:
- Token efficiency drops 5%+ from personal best
- Session score drops 10%+ from recent trend
- Multiple sessions in row with declining scores

Consequences:
- Streak breaks (already handled by StreakSystem)
- Difficulty may auto-adjust down (regression cooldown)
- No absolute score penalty (encourages recovery attempts)
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta


class RegressionDetector:
    """Detects performance regression and triggers appropriate responses."""

    # Thresholds for regression detection
    TOKEN_EFFICIENCY_REGRESSION_THRESHOLD = 0.05  # 5% drop
    SCORE_DROP_THRESHOLD = 0.10  # 10% drop from trend
    CONSECUTIVE_DECLINES_FOR_REGRESSION = 3  # 3 sessions in row

    @classmethod
    def detect_efficiency_regression(
        cls,
        current_efficiency: float,
        personal_best_efficiency: float
    ) -> Dict:
        """
        Detect if current session shows regression in token efficiency.

        Args:
            current_efficiency: Current session token efficiency ratio (tokens/msg)
            personal_best_efficiency: Best achieved efficiency ratio

        Returns:
            Dict with regression status and details
        """
        if personal_best_efficiency <= 0:
            return {
                "has_regressed": False,
                "reason": "No baseline established",
                "efficiency_drop_pct": 0,
            }

        efficiency_ratio = current_efficiency / personal_best_efficiency
        drop_pct = max(0, 1.0 - efficiency_ratio)

        has_regressed = drop_pct >= cls.TOKEN_EFFICIENCY_REGRESSION_THRESHOLD

        return {
            "has_regressed": has_regressed,
            "current_efficiency": current_efficiency,
            "personal_best_efficiency": personal_best_efficiency,
            "efficiency_ratio": round(efficiency_ratio, 2),
            "efficiency_drop_pct": round(drop_pct * 100, 1),
            "threshold_pct": round(cls.TOKEN_EFFICIENCY_REGRESSION_THRESHOLD * 100, 1),
            "reason": (
                f"Token efficiency dropped {round(drop_pct * 100, 1)}% "
                f"(threshold: {round(cls.TOKEN_EFFICIENCY_REGRESSION_THRESHOLD * 100, 1)}%)"
            ) if has_regressed else "Within acceptable variance",
        }

    @classmethod
    def detect_score_regression(
        cls,
        current_score: float,
        recent_scores: List[float]
    ) -> Dict:
        """
        Detect if score dropped significantly from recent trend.

        Args:
            current_score: Current session score
            recent_scores: List of last N session scores (oldest first)

        Returns:
            Dict with regression status and trend analysis
        """
        if not recent_scores or len(recent_scores) < 2:
            return {
                "has_regressed": False,
                "reason": "Not enough history",
                "recent_average": current_score,
                "trend": "new_or_insufficient_data",
            }

        recent_avg = sum(recent_scores) / len(recent_scores)

        if recent_avg <= 0:
            return {
                "has_regressed": False,
                "reason": "Baseline is zero",
                "recent_average": 0,
                "trend": "baseline_zero",
            }

        drop_pct = max(0, (recent_avg - current_score) / recent_avg)
        has_regressed = drop_pct >= cls.SCORE_DROP_THRESHOLD

        # Determine trend
        if len(recent_scores) >= 2:
            trend_direction = "declining" if recent_scores[-1] < recent_scores[-2] else "stable"
        else:
            trend_direction = "new"

        return {
            "has_regressed": has_regressed,
            "current_score": current_score,
            "recent_average": round(recent_avg, 1),
            "score_drop_pct": round(drop_pct * 100, 1),
            "threshold_pct": round(cls.SCORE_DROP_THRESHOLD * 100, 1),
            "recent_count": len(recent_scores),
            "trend": trend_direction,
            "reason": (
                f"Score dropped {round(drop_pct * 100, 1)}% "
                f"from recent avg {round(recent_avg, 1)} "
                f"(threshold: {round(cls.SCORE_DROP_THRESHOLD * 100, 1)}%)"
            ) if has_regressed else f"Score within variance of recent avg {round(recent_avg, 1)}",
        }

    @classmethod
    def detect_consecutive_decline(cls, recent_scores: List[float]) -> Dict:
        """
        Detect if multiple consecutive sessions show declining scores.

        Args:
            recent_scores: List of last N session scores (oldest first)

        Returns:
            Dict with consecutive decline status
        """
        if not recent_scores or len(recent_scores) < cls.CONSECUTIVE_DECLINES_FOR_REGRESSION:
            return {
                "has_consecutive_decline": False,
                "consecutive_count": 0,
                "reason": "Not enough history",
            }

        # Check last N sessions for consecutive declines
        consecutive_declines = 0
        for i in range(len(recent_scores) - 1, 0, -1):
            if recent_scores[i] < recent_scores[i - 1]:
                consecutive_declines += 1
            else:
                break

        has_decline = consecutive_declines >= cls.CONSECUTIVE_DECLINES_FOR_REGRESSION

        return {
            "has_consecutive_decline": has_decline,
            "consecutive_count": consecutive_declines,
            "threshold_count": cls.CONSECUTIVE_DECLINES_FOR_REGRESSION,
            "reason": (
                f"{consecutive_declines} consecutive declining sessions "
                f"(threshold: {cls.CONSECUTIVE_DECLINES_FOR_REGRESSION})"
            ) if has_decline else f"Declining streak broken or insufficient data",
        }

    @classmethod
    def analyze_regression(
        cls,
        current_score: float,
        current_efficiency: float,
        personal_best_efficiency: float,
        recent_scores: List[float],
        session_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Comprehensive regression analysis combining multiple signals.

        Args:
            current_score: Current session score
            current_efficiency: Current token efficiency
            personal_best_efficiency: Best achieved efficiency
            recent_scores: Recent session scores
            session_history: Full session history for context

        Returns:
            Comprehensive regression analysis dict
        """
        efficiency_reg = cls.detect_efficiency_regression(
            current_efficiency, personal_best_efficiency
        )
        score_reg = cls.detect_score_regression(current_score, recent_scores)
        consecutive_reg = cls.detect_consecutive_decline(recent_scores)

        # Count regression signals
        regression_signals = sum([
            efficiency_reg.get("has_regressed", False),
            score_reg.get("has_regressed", False),
            consecutive_reg.get("has_consecutive_decline", False),
        ])

        # Determine severity
        if regression_signals == 0:
            severity = "none"
        elif regression_signals == 1:
            severity = "minor"
        elif regression_signals == 2:
            severity = "moderate"
        else:
            severity = "severe"

        return {
            "has_regressed": regression_signals > 0,
            "severity": severity,
            "regression_signals": regression_signals,
            "efficiency": efficiency_reg,
            "score": score_reg,
            "consecutive": consecutive_reg,
            "recommendation": cls._get_recommendation(severity, efficiency_reg, score_reg),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def _get_recommendation(severity: str, efficiency_reg: Dict, score_reg: Dict) -> str:
        """Generate recommendation based on regression analysis."""
        if severity == "none":
            return "Keep improving! You're maintaining your high standards."

        if severity == "minor":
            return (
                "Small dip detected. Nothing to worry about - "
                "everyone has variance. Focus on consistency."
            )

        if severity == "moderate":
            return (
                "Performance decline detected. Review your recent patterns: "
                f"Efficiency {efficiency_reg.get('efficiency_drop_pct', 0)}% drop, "
                f"Score {score_reg.get('score_drop_pct', 0)}% drop. "
                "No penalty yet, but your streak will reset if scores don't improve."
            )

        if severity == "severe":
            return (
                "Significant backsliding detected across multiple metrics. "
                "Your temporary difficulty will be adjusted to allow recovery. "
                "Focus on fundamentals: efficient tool use, focused sessions. "
                "You've done it before - get back on track!"
            )

        return "Regression analysis complete."

    @classmethod
    def calculate_difficulty_adjustment(
        cls,
        regression_analysis: Dict
    ) -> Dict:
        """
        Calculate difficulty adjustment based on regression severity.

        Args:
            regression_analysis: Output from analyze_regression()

        Returns:
            Dict with difficulty adjustment recommendation
        """
        severity = regression_analysis.get("severity", "none")

        if severity == "none":
            return {
                "should_adjust": False,
                "adjustment_factor": 1.0,
                "duration_days": 0,
                "reason": "No regression detected",
            }

        if severity == "minor":
            return {
                "should_adjust": False,
                "adjustment_factor": 1.0,
                "duration_days": 0,
                "reason": "Minor variance - no adjustment needed",
            }

        if severity == "moderate":
            return {
                "should_adjust": True,
                "adjustment_factor": 0.95,  # 5% easier for 1 week
                "duration_days": 7,
                "reason": "Moderate regression - temporary 5% difficulty reduction for recovery",
            }

        if severity == "severe":
            return {
                "should_adjust": True,
                "adjustment_factor": 0.85,  # 15% easier for 2 weeks
                "duration_days": 14,
                "reason": "Severe regression - temporary 15% difficulty reduction for recovery",
            }

        return {
            "should_adjust": False,
            "adjustment_factor": 1.0,
            "duration_days": 0,
            "reason": "Unknown severity",
        }

    @classmethod
    def get_recovery_guidance(cls, regression_analysis: Dict) -> str:
        """Get user-friendly recovery guidance."""
        severity = regression_analysis.get("severity", "none")
        efficiency = regression_analysis.get("efficiency", {})
        score = regression_analysis.get("score", {})

        parts = []

        if efficiency.get("has_regressed"):
            parts.append(
                f"📊 Token efficiency dropped {efficiency.get('efficiency_drop_pct', 0)}% "
                f"from your best. Try: shorter messages, fewer tool calls, focused context."
            )

        if score.get("has_regressed"):
            parts.append(
                f"📈 Session score dropped {score.get('score_drop_pct', 0)}% "
                f"from recent average. Back to fundamentals: plan before acting, verify tool outputs."
            )

        if regression_analysis.get("consecutive", {}).get("has_consecutive_decline"):
            consecutive = regression_analysis.get("consecutive", {}).get("consecutive_count", 0)
            parts.append(
                f"⚠️ {consecutive} sessions declining - this is a trend. "
                f"Take a step back, identify what changed, reset your approach."
            )

        if not parts:
            parts.append("No specific recovery guidance - you're doing great!")

        return " ".join(parts)
