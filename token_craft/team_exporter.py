"""
Team Exporter

Exports user stats for team aggregation and leaderboards.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class TeamExporter:
    """Export user statistics for team analysis."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize team exporter.

        Args:
            output_dir: Directory to export stats to
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.home() / ".claude" / "token-craft" / "team-exports"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_user_stats(
        self,
        profile_data: Dict,
        score_data: Dict,
        rank_data: Dict,
        department: str = "Engineering"
    ) -> str:
        """
        Export user statistics to team directory.

        Args:
            profile_data: User profile data
            score_data: Score breakdown
            rank_data: Rank information
            department: User's department

        Returns:
            Filename of exported file
        """
        user_email = profile_data.get("user_email", "unknown@local")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize email for filename
        safe_email = user_email.replace("@", "_at_").replace(".", "_")
        filename = f"{safe_email}_{timestamp}.json"
        filepath = self.output_dir / filename

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "user_email": user_email,
            "department": department,
            "current_rank": rank_data["name"],
            "current_score": score_data["total_score"],
            "total_sessions": profile_data.get("total_sessions", 0),
            "total_messages": profile_data.get("total_messages", 0),
            "total_tokens": profile_data.get("total_tokens", 0),
            "avg_tokens_per_session": profile_data.get("avg_tokens_per_session", 0),
            "scores_breakdown": {
                "token_efficiency": score_data["breakdown"]["token_efficiency"]["score"],
                "optimization_adoption": score_data["breakdown"]["optimization_adoption"]["score"],
                "self_sufficiency": score_data["breakdown"]["self_sufficiency"]["score"],
                "improvement_trend": score_data["breakdown"]["improvement_trend"]["score"],
                "best_practices": score_data["breakdown"]["best_practices"]["score"]
            },
            "achievements": profile_data.get("achievements", []),
            "metadata": {
                "version": "1.0.0",
                "exporter": "token-craft"
            }
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)

            return filename

        except Exception as e:
            raise Exception(f"Failed to export stats: {e}")

    def get_export_count(self) -> int:
        """Get number of exported files."""
        return len(list(self.output_dir.glob("*.json")))

    def list_exports(self) -> list:
        """List all export files."""
        exports = list(self.output_dir.glob("*.json"))
        exports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return [e.name for e in exports]

    def cleanup_old_exports(self, keep_count: int = 10):
        """Keep only the most recent N exports per user."""
        # Group by user email
        from collections import defaultdict
        user_exports = defaultdict(list)

        for export_file in self.output_dir.glob("*.json"):
            # Extract user email from filename
            filename = export_file.stem
            user_part = filename.rsplit("_", 2)[0]  # Remove timestamp
            user_exports[user_part].append(export_file)

        # Keep only recent exports for each user
        for user, files in user_exports.items():
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Delete old exports
            for old_file in files[keep_count:]:
                try:
                    old_file.unlink()
                except Exception as e:
                    print(f"Error deleting {old_file.name}: {e}")
