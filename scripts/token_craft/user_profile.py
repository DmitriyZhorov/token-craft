"""
User Profile Management

Stores and manages user token optimization progress.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class UserProfile:
    """Manage user profile and state."""

    def __init__(self, user_email: Optional[str] = None, profile_dir: Optional[Path] = None):
        """
        Initialize user profile.

        Args:
            user_email: User's email (optional, will try to detect)
            profile_dir: Custom profile directory (optional)
        """
        self.user_email = user_email or self._detect_user_email()

        # Set profile directory
        if profile_dir:
            self.profile_dir = Path(profile_dir)
        else:
            self.profile_dir = Path.home() / ".claude" / "token-craft"

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.profile_dir / "user_profile.json"

        # Load or create profile
        self.data = self._load_profile()

    def _detect_user_email(self) -> str:
        """Try to detect user email from git config."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "config", "--global", "user.email"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        return "unknown@local"

    def _load_profile(self) -> Dict:
        """Load profile from disk or create new."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load profile: {e}")
                return self._create_new_profile()
        else:
            return self._create_new_profile()

    def _create_new_profile(self) -> Dict:
        """Create a new profile structure."""
        return {
            "user_email": self.user_email,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "current_rank": "Cadet",
            "current_score": 0,
            "rank_achieved_at": None,
            "total_sessions": 0,
            "total_messages": 0,
            "total_tokens": 0,
            "avg_tokens_per_session": 0,
            "scores": {
                "token_efficiency": 0,
                "optimization_adoption": 0,
                "self_sufficiency": 0,
                "improvement_trend": 0,
                "best_practices": 0,
                "cache_effectiveness": 0,
                "tool_efficiency": 0,
                "cost_efficiency": 0,
                "session_focus": 0,
                "learning_growth": 0,
                "waste_awareness": 0
            },
            "history": [],
            "achievements": [],
            "preferences": {
                "theme": "space_exploration",
                "notifications": True
            }
        }

    def update_from_analysis(self, score_data: Dict, rank_data: Dict):
        """
        Update profile with new analysis data.

        Args:
            score_data: Output from TokenCraftScorer.calculate_total_score()
            rank_data: Output from SpaceRankSystem.get_rank()
        """
        old_rank = self.data.get("current_rank")
        new_rank = rank_data["name"]
        new_score = score_data["total_score"]

        # Check for rank change
        rank_changed = old_rank != new_rank

        # Update profile
        self.data["last_updated"] = datetime.now().isoformat()
        self.data["current_rank"] = new_rank
        self.data["current_score"] = new_score

        if rank_changed:
            self.data["rank_achieved_at"] = datetime.now().isoformat()

            # Add to history
            self.data["history"].append({
                "timestamp": datetime.now().isoformat(),
                "event": "rank_change",
                "old_rank": old_rank,
                "new_rank": new_rank,
                "score": new_score
            })

        # Update detailed scores (dynamic - supports all categories)
        self.data["scores"] = {
            cat: cat_data["score"]
            for cat, cat_data in score_data["breakdown"].items()
        }

        # Update stats
        if "token_efficiency" in score_data.get("breakdown", {}):
            details = score_data["breakdown"]["token_efficiency"].get("details", {})
            self.data["total_sessions"] = details.get("total_sessions", 0)
            self.data["total_tokens"] = details.get("total_tokens", 0)
            self.data["avg_tokens_per_session"] = details.get("avg_tokens_per_session", 0)

        # Calculate total messages if not already done
        if self.data.get("total_messages", 0) == 0:
            # Count from history if available
            self.data["total_messages"] = self.data.get("total_sessions", 0) * 10  # Rough estimate

    def save(self):
        """Save profile to disk."""
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False

    def get_current_state(self) -> Dict:
        """Get complete current state."""
        return self.data.copy()

    def add_achievement(self, achievement_id: str, title: str, description: str):
        """Add an achievement to the profile."""
        achievement = {
            "id": achievement_id,
            "title": title,
            "description": description,
            "earned_at": datetime.now().isoformat()
        }

        # Don't add duplicates
        if not any(a["id"] == achievement_id for a in self.data["achievements"]):
            self.data["achievements"].append(achievement)
            return True

        return False

    def get_achievements(self) -> list:
        """Get all achievements."""
        return self.data.get("achievements", [])

    def get_rank_history(self) -> list:
        """Get rank change history."""
        return [h for h in self.data.get("history", []) if h.get("event") == "rank_change"]

    def get_progress_summary(self) -> Dict:
        """Get a summary of progress."""
        return {
            "current_rank": self.data["current_rank"],
            "current_score": self.data["current_score"],
            "total_sessions": self.data["total_sessions"],
            "total_messages": self.data.get("total_messages", 0),
            "avg_tokens_per_session": self.data["avg_tokens_per_session"],
            "achievements_count": len(self.data.get("achievements", [])),
            "rank_changes": len(self.get_rank_history())
        }
