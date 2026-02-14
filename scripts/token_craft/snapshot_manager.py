"""
Snapshot Management

Creates and manages historical snapshots of user progress.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class SnapshotManager:
    """Manage user progress snapshots."""

    def __init__(self, snapshot_dir: Optional[Path] = None):
        """
        Initialize snapshot manager.

        Args:
            snapshot_dir: Custom snapshot directory (optional)
        """
        if snapshot_dir:
            self.snapshot_dir = Path(snapshot_dir)
        else:
            self.snapshot_dir = Path.home() / ".claude" / "token-craft" / "snapshots"

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, profile_data: Dict, score_data: Dict, rank_data: Dict) -> str:
        """
        Create a timestamped snapshot.

        Args:
            profile_data: User profile data
            score_data: Score calculation results
            rank_data: Rank information

        Returns:
            Filename of created snapshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{timestamp}.json"
        filepath = self.snapshot_dir / filename

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "profile": profile_data,
            "scores": score_data,
            "rank": rank_data,
            "version": "1.0.0"
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            return filename
        except Exception as e:
            raise Exception(f"Failed to create snapshot: {e}")

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the most recent snapshot."""
        snapshots = self.list_snapshots()
        if not snapshots:
            return None

        latest = snapshots[-1]
        return self.get_snapshot(latest)

    def get_snapshot(self, filename: str) -> Optional[Dict]:
        """
        Get specific snapshot by filename.

        Args:
            filename: Snapshot filename

        Returns:
            Snapshot data or None if not found
        """
        filepath = self.snapshot_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading snapshot {filename}: {e}")
            return None

    def list_snapshots(self) -> List[str]:
        """
        List all available snapshots sorted by timestamp.

        Returns:
            List of snapshot filenames
        """
        snapshots = list(self.snapshot_dir.glob("snapshot_*.json"))
        snapshots.sort()
        return [s.name for s in snapshots]

    def get_snapshot_count(self) -> int:
        """Get total number of snapshots."""
        return len(self.list_snapshots())

    def get_first_snapshot(self) -> Optional[Dict]:
        """Get the first (oldest) snapshot."""
        snapshots = self.list_snapshots()
        if not snapshots:
            return None

        return self.get_snapshot(snapshots[0])

    def delete_snapshot(self, filename: str) -> bool:
        """
        Delete a specific snapshot.

        Args:
            filename: Snapshot filename

        Returns:
            True if deleted successfully
        """
        filepath = self.snapshot_dir / filename

        if filepath.exists():
            try:
                filepath.unlink()
                return True
            except Exception as e:
                print(f"Error deleting snapshot {filename}: {e}")
                return False

        return False

    def cleanup_old_snapshots(self, keep_count: int = 30):
        """
        Keep only the most recent N snapshots.

        Args:
            keep_count: Number of snapshots to keep
        """
        snapshots = self.list_snapshots()

        if len(snapshots) <= keep_count:
            return

        # Delete oldest snapshots
        to_delete = snapshots[:-keep_count]
        for filename in to_delete:
            self.delete_snapshot(filename)

    def export_snapshots(self, export_dir: Path) -> int:
        """
        Export all snapshots to a directory.

        Args:
            export_dir: Directory to export to

        Returns:
            Number of snapshots exported
        """
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)

        snapshots = self.list_snapshots()
        exported = 0

        for filename in snapshots:
            snapshot_data = self.get_snapshot(filename)
            if snapshot_data:
                export_path = export_dir / filename
                try:
                    with open(export_path, "w", encoding="utf-8") as f:
                        json.dump(snapshot_data, f, indent=2)
                    exported += 1
                except Exception as e:
                    print(f"Error exporting {filename}: {e}")

        return exported
