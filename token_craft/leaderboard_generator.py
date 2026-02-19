"""
Leaderboard Generator

Creates company-wide, project-level, and department leaderboards.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


class LeaderboardGenerator:
    """Generate leaderboards from team data."""

    def __init__(self, stats_dir: Optional[Path] = None):
        """
        Initialize leaderboard generator.

        Args:
            stats_dir: Directory containing team stat exports
        """
        self.stats_dir = Path(stats_dir) if stats_dir else Path.home() / ".claude" / "token-craft" / "team-stats"
        self.stats_dir.mkdir(parents=True, exist_ok=True)

    def load_team_stats(self) -> List[Dict]:
        """
        Load all team member statistics.

        Returns:
            List of team member stats
        """
        team_stats = []

        # Look for exported stat files
        stat_files = list(self.stats_dir.glob("*_2026*.json"))

        for stat_file in stat_files:
            try:
                with open(stat_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    team_stats.append(data)
            except Exception as e:
                print(f"Warning: Could not load {stat_file.name}: {e}")

        return team_stats

    def generate_company_leaderboard(self, anonymous: bool = True) -> Dict:
        """
        Generate company-wide leaderboard.

        Args:
            anonymous: If True, use anonymous IDs instead of names

        Returns:
            Leaderboard data
        """
        team_stats = self.load_team_stats()

        if not team_stats:
            return {
                "leaderboard_type": "company",
                "rankings": [],
                "total_participants": 0
            }

        # Sort by score
        sorted_stats = sorted(
            team_stats,
            key=lambda x: x.get("current_score", 0),
            reverse=True
        )

        rankings = []
        for i, member in enumerate(sorted_stats, 1):
            ranking = {
                "rank": i,
                "score": member.get("current_score", 0),
                "rank_title": member.get("current_rank", "Unknown"),
                "sessions": member.get("total_sessions", 0),
                "avg_tokens": member.get("avg_tokens_per_session", 0)
            }

            # Anonymous or named
            if anonymous:
                # Generate consistent anonymous ID from email
                email = member.get("user_email", "unknown")
                anon_id = f"Anonymous_#{abs(hash(email)) % 10000:04d}"
                ranking["name"] = anon_id
            else:
                ranking["name"] = member.get("user_email", "Unknown")

            rankings.append(ranking)

        return {
            "leaderboard_type": "company",
            "time_period": "current",
            "rankings": rankings,
            "total_participants": len(rankings)
        }

    def generate_project_leaderboard(self, project_name: str) -> Dict:
        """
        Generate project-specific leaderboard.

        Args:
            project_name: Name of the project

        Returns:
            Project leaderboard data
        """
        team_stats = self.load_team_stats()

        project_contributors = []

        for member in team_stats:
            # Check if this member worked on this project
            # (This requires project breakdown data from exports)
            projects = member.get("projects", {})

            if project_name in projects:
                project_data = projects[project_name]
                project_contributors.append({
                    "user_email": member.get("user_email", "Unknown"),
                    "name": member.get("user_email", "Unknown").split("@")[0],
                    "score": member.get("current_score", 0),
                    "rank_title": member.get("current_rank", "Unknown"),
                    "sessions": project_data.get("sessions", 0),
                    "messages": project_data.get("messages", 0)
                })

        # Sort by sessions contributed to this project
        sorted_contributors = sorted(
            project_contributors,
            key=lambda x: x["sessions"],
            reverse=True
        )

        rankings = []
        for i, contributor in enumerate(sorted_contributors, 1):
            rankings.append({
                "rank": i,
                **contributor
            })

        return {
            "leaderboard_type": "project",
            "project_name": project_name,
            "rankings": rankings,
            "total_contributors": len(rankings)
        }

    def generate_department_leaderboard(self, department: str) -> Dict:
        """
        Generate department-level leaderboard.

        Args:
            department: Department name

        Returns:
            Department leaderboard data
        """
        team_stats = self.load_team_stats()

        dept_members = []

        for member in team_stats:
            member_dept = member.get("department", "Unknown")

            if member_dept.lower() == department.lower():
                dept_members.append({
                    "name": member.get("user_email", "Unknown"),
                    "score": member.get("current_score", 0),
                    "rank_title": member.get("current_rank", "Unknown"),
                    "sessions": member.get("total_sessions", 0),
                    "efficiency_rating": self._get_efficiency_rating(member)
                })

        # Sort by score
        sorted_members = sorted(
            dept_members,
            key=lambda x: x["score"],
            reverse=True
        )

        rankings = []
        for i, member in enumerate(sorted_members, 1):
            rankings.append({
                "rank": i,
                **member
            })

        # Calculate department average
        dept_avg = sum(m["score"] for m in dept_members) / len(dept_members) if dept_members else 0

        return {
            "leaderboard_type": "department",
            "department": department,
            "rankings": rankings,
            "department_avg_score": dept_avg,
            "total_members": len(rankings)
        }

    def _get_efficiency_rating(self, member_data: Dict) -> str:
        """Get efficiency rating label."""
        avg_tokens = member_data.get("avg_tokens_per_session", 15000)

        if avg_tokens < 7000:
            return "excellent"
        elif avg_tokens < 10000:
            return "good"
        elif avg_tokens < 15000:
            return "average"
        else:
            return "needs_improvement"

    def find_your_rank(self, user_email: str) -> Optional[Dict]:
        """
        Find user's rank in company leaderboard.

        Args:
            user_email: User's email

        Returns:
            Rank info or None
        """
        leaderboard = self.generate_company_leaderboard(anonymous=False)

        for ranking in leaderboard["rankings"]:
            if ranking["name"] == user_email:
                total = leaderboard["total_participants"]
                percentile = (ranking["rank"] / total) * 100

                return {
                    "rank": ranking["rank"],
                    "total_participants": total,
                    "percentile": percentile,
                    "score": ranking["score"],
                    "rank_title": ranking["rank_title"]
                }

        return None

    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        """
        Get top performers.

        Args:
            limit: Number of top performers to return

        Returns:
            List of top performers
        """
        leaderboard = self.generate_company_leaderboard(anonymous=False)
        return leaderboard["rankings"][:limit]

    def calculate_team_stats(self) -> Dict:
        """
        Calculate overall team statistics.

        Returns:
            Team-wide stats
        """
        team_stats = self.load_team_stats()

        if not team_stats:
            return {
                "team_size": 0,
                "total_sessions": 0,
                "total_tokens": 0,
                "avg_score": 0,
                "avg_rank": "Unknown"
            }

        total_sessions = sum(m.get("total_sessions", 0) for m in team_stats)
        total_tokens = sum(m.get("total_tokens", 0) for m in team_stats)
        avg_score = sum(m.get("current_score", 0) for m in team_stats) / len(team_stats)

        # Most common rank
        from collections import Counter
        ranks = [m.get("current_rank", "Unknown") for m in team_stats]
        most_common_rank = Counter(ranks).most_common(1)[0][0]

        return {
            "team_size": len(team_stats),
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "avg_score": round(avg_score, 1),
            "avg_rank": most_common_rank,
            "total_participants": len(team_stats)
        }

    def format_leaderboard(self, leaderboard_data: Dict) -> str:
        """
        Format leaderboard for display.

        Args:
            leaderboard_data: Leaderboard data

        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 80)

        lb_type = leaderboard_data["leaderboard_type"].upper()
        title = f"{lb_type} LEADERBOARD"

        if lb_type == "PROJECT":
            title += f" - {leaderboard_data.get('project_name', 'Unknown')}"
        elif lb_type == "DEPARTMENT":
            title += f" - {leaderboard_data.get('department', 'Unknown')}"

        lines.append(title.center(80))
        lines.append("=" * 80)
        lines.append("")

        rankings = leaderboard_data.get("rankings", [])

        if not rankings:
            lines.append("No data available yet.".center(80))
            lines.append("")
            lines.append("=" * 80)
            return "\n".join(lines)

        # Header
        lines.append(f"{'Rank':<6} {'Name':<30} {'Level':<18} {'Score':<12}")
        lines.append("-" * 80)

        # Rankings
        for entry in rankings[:25]:  # Top 25
            rank = entry.get("rank", "?")
            name = entry.get("name", "Unknown")[:29]
            level = entry.get("rank_title", "Unknown")
            score = entry.get("score", 0)

            # Add medal for top 3
            if rank == 1:
                rank_display = "🥇 1"
            elif rank == 2:
                rank_display = "🥈 2"
            elif rank == 3:
                rank_display = "🥉 3"
            else:
                rank_display = f"  {rank}"

            lines.append(f"{rank_display:<6} {name:<30} {level:<18} {score:<12.0f}")

        lines.append("")
        lines.append(f"Total participants: {leaderboard_data.get('total_participants', 0)}")
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_leaderboard(self, leaderboard_data: Dict, output_file: Path) -> bool:
        """
        Export leaderboard to JSON file.

        Args:
            leaderboard_data: Leaderboard data
            output_file: Output file path

        Returns:
            True if successful
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(leaderboard_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting leaderboard: {e}")
            return False
