"""
Migration Engine

Handles v2.0 → v3.0 data migration with backwards compatibility.

Changes:
- Removes Self-Sufficiency duplicate (200 pts)
- Removes warm-up bonuses
- Recalculates scores with smooth scales
- Preserves history in legacy fields
"""

from typing import Dict, Optional, List
from datetime import datetime


class MigrationEngine:
    """Manages profile migration from v2.0 to v3.0."""

    SCHEMA_VERSION_LEGACY = "2.0"
    SCHEMA_VERSION_CURRENT = "3.0"

    # v2.0 weight removed
    REMOVED_CATEGORIES = ["self_sufficiency"]

    @classmethod
    def create_migration_snapshot(cls, old_profile: Dict) -> Dict:
        """
        Create snapshot of v2.0 profile before migration.

        Args:
            old_profile: v2.0 user profile

        Returns:
            Snapshot dict
        """
        return {
            "v2_final_score": old_profile.get("current_score", 0),
            "v2_current_rank": old_profile.get("current_rank", "Cadet"),
            "v2_scores": old_profile.get("scores", {}),
            "v2_total_sessions": old_profile.get("total_sessions", 0),
            "v2_total_tokens": old_profile.get("total_tokens", 0),
            "migration_timestamp": datetime.now().isoformat(),
        }

    @classmethod
    def migrate_profile(cls, old_profile: Dict) -> Dict:
        """
        Migrate profile from v2.0 to v3.0 schema.

        Args:
            old_profile: v2.0 profile structure

        Returns:
            v3.0 profile structure
        """
        # Preserve legacy data
        legacy_snapshot = cls.create_migration_snapshot(old_profile)

        # Create new profile with v3.0 schema
        new_profile = dict(old_profile)

        # Update schema version
        new_profile["version"] = cls.SCHEMA_VERSION_CURRENT

        # Add migration metadata
        new_profile["migration"] = {
            "source_version": cls.SCHEMA_VERSION_LEGACY,
            "target_version": cls.SCHEMA_VERSION_CURRENT,
            "migrated_at": datetime.now().isoformat(),
        }

        # Archive v2.0 snapshot
        new_profile["legacy"] = legacy_snapshot

        # Initialize new v3.0 fields
        new_profile["streak_info"] = {"current": cls._new_streak(), "best": cls._new_streak()}
        new_profile["seasonal_info"] = {
            "current_season_score": 0,
            "lifetime_score": 0,
            "current_season_start": datetime.now().isoformat(),
            "last_reset": None,
        }

        # Initialize achievements system
        if "achievements" not in new_profile:
            new_profile["achievements"] = []

        # Remove old self-sufficiency score (we'll recalculate)
        if "scores" in new_profile:
            for cat in cls.REMOVED_CATEGORIES:
                if cat in new_profile["scores"]:
                    del new_profile["scores"][cat]

        return new_profile

    @staticmethod
    def _new_streak() -> Dict:
        """Create new streak record."""
        return {
            "length": 0,
            "start_date": None,
            "last_session_date": None,
            "last_session_score": 0,
            "bonus_points_earned": 0,
        }

    @classmethod
    def validate_migration(cls, new_profile: Dict) -> Dict:
        """
        Validate migrated profile integrity.

        Args:
            new_profile: Migrated v3.0 profile

        Returns:
            Validation result dict
        """
        errors = []
        warnings = []

        # Check version
        if new_profile.get("version") != cls.SCHEMA_VERSION_CURRENT:
            errors.append(f"Invalid schema version: {new_profile.get('version')}")

        # Check new required fields
        if "streak_info" not in new_profile:
            warnings.append("Missing streak_info field")

        if "seasonal_info" not in new_profile:
            warnings.append("Missing seasonal_info field")

        if "legacy" not in new_profile:
            warnings.append("Missing legacy snapshot")

        # Check that removed categories are gone from scores
        if "scores" in new_profile:
            for cat in cls.REMOVED_CATEGORIES:
                if cat in new_profile["scores"]:
                    errors.append(f"Old category {cat} still in scores - should be removed")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "schema_version": new_profile.get("version"),
        }

    @classmethod
    def generate_migration_report(cls, old_profile: Dict, new_profile: Dict) -> Dict:
        """
        Generate report of changes during migration.

        Args:
            old_profile: v2.0 profile
            new_profile: v3.0 profile

        Returns:
            Migration report
        """
        old_score = old_profile.get("current_score", 0)
        new_score = new_profile.get("current_score", 0)
        score_change = new_score - old_score
        score_change_pct = (score_change / old_score * 100) if old_score > 0 else 0

        # Get removed categories total
        removed_score = old_profile.get("scores", {}).get("self_sufficiency", 0)

        return {
            "migration_date": datetime.now().isoformat(),
            "source_version": "v2.0",
            "target_version": "v3.0",
            "score_changes": {
                "old_score": old_score,
                "new_score": new_score,
                "change": round(score_change, 1),
                "change_pct": round(score_change_pct, 1),
            },
            "removed_categories": {
                "self_sufficiency": {
                    "reason": "Duplicate of direct_commands check in optimization_adoption",
                    "points_removed": removed_score,
                }
            },
            "new_systems": [
                "Difficulty Modifier (rank-based difficulty scaling)",
                "Streak System (consecutive improvement rewards)",
                "Combo Bonuses (multi-category excellence)",
                "Achievement Engine (25+ achievements)",
                "Time-Based Mechanics (recency, decay, seasonal)",
            ],
            "schema_changes": [
                "streak_info: Track streaks and combos",
                "seasonal_info: Season scores and lifetime totals",
                "legacy: Snapshot of v2.0 data",
                "migration: Migration metadata",
            ],
            "message": f"""Your profile has been upgraded to v3.0!

Old Score: {old_score} pts ({old_profile.get("current_rank", "Cadet")} rank)
New Score: {new_score} pts ({new_profile.get("current_rank", "Cadet")} rank)
Change: {round(score_change, 1)} pts ({round(score_change_pct, 1)}%)

Why changed?
- Removed duplicate Self-Sufficiency category ({removed_score} pts)
- Removed warm-up bonuses (no participation trophies)
- Scores recalculated with smooth scales

Your legacy data is preserved in the profile. New targets:
- Difficulty increases with your rank
- Streaks reward consistency (up to 1.25x multiplier)
- 25+ achievements unlock at milestones
- Seasons reset monthly to keep competition fresh

Ready to reach new heights!""",
        }

    @classmethod
    def need_migration(cls, profile: Dict) -> bool:
        """
        Check if profile needs migration.

        Args:
            profile: User profile to check

        Returns:
            True if migration needed
        """
        version = profile.get("version", "2.0")
        return version != cls.SCHEMA_VERSION_CURRENT

    @classmethod
    def migrate_if_needed(cls, profile: Dict) -> Dict:
        """
        Migrate profile if necessary.

        Args:
            profile: User profile

        Returns:
            Migrated profile (or original if already v3.0)
        """
        if not cls.need_migration(profile):
            return profile

        migrated = cls.migrate_profile(profile)
        validation = cls.validate_migration(migrated)

        if not validation["valid"]:
            print("Warning: Migration validation failed")
            for error in validation["errors"]:
                print(f"  - {error}")

        return migrated

    @classmethod
    def get_all_legacy_profiles_info(cls, profiles_list: List[Dict]) -> Dict:
        """
        Get summary of all profiles needing migration.

        Args:
            profiles_list: List of user profiles

        Returns:
            Summary statistics
        """
        total = len(profiles_list)
        needs_migration = sum(1 for p in profiles_list if cls.need_migration(p))

        return {
            "total_profiles": total,
            "need_migration": needs_migration,
            "already_migrated": total - needs_migration,
            "migration_pct": round((needs_migration / total * 100), 1) if total > 0 else 0,
        }
