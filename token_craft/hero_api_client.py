"""
hero.epam.com API Client

Integrates with EPAM's hero platform for badge issuance.
"""

import json
from typing import Dict, Optional, List
from datetime import datetime

# Optional import
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class HeroAPIClient:
    """Client for hero.epam.com API."""

    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Initialize hero API client.

        Args:
            api_url: API base URL (default: https://hero.epam.com/api)
            api_key: API authentication key
        """
        self.api_url = api_url or "https://hero.epam.com/api"
        self.api_key = api_key

        if HAS_REQUESTS:
            self.session = requests.Session()
            if self.api_key:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                })
        else:
            self.session = None

    def issue_badge(self, user_email: str, badge_id: str, evidence: Dict) -> Dict:
        """
        Issue badge to user.

        Args:
            user_email: User's email address
            badge_id: Badge identifier (e.g., "token_craft_captain")
            evidence: Evidence data supporting the badge

        Returns:
            API response
        """
        payload = {
            "user_email": user_email,
            "badge_id": badge_id,
            "issued_date": datetime.now().isoformat(),
            "evidence": evidence,
            "issuer": "token-craft-system",
            "auto_issued": True
        }

        try:
            if not HAS_REQUESTS or not self.session:
                # Mock response when requests not available
                print(f"[MOCK] Would issue badge {badge_id} to {user_email}")
                return {
                    "success": True,
                    "badge_id": badge_id,
                    "user_email": user_email,
                    "message": "Badge issued successfully (mock)"
                }

            # TODO: Replace with actual API endpoint when available
            # response = self.session.post(f"{self.api_url}/badges/issue", json=payload)
            # response.raise_for_status()
            # return response.json()

            # Mock response for now
            print(f"[MOCK] Would issue badge {badge_id} to {user_email}")
            return {
                "success": True,
                "badge_id": badge_id,
                "user_email": user_email,
                "message": "Badge issued successfully (mock)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def revoke_badge(self, user_email: str, badge_id: str, reason: str = None) -> Dict:
        """
        Revoke badge from user (if rank drops).

        Args:
            user_email: User's email address
            badge_id: Badge identifier to revoke
            reason: Optional reason for revocation

        Returns:
            API response
        """
        payload = {
            "user_email": user_email,
            "badge_id": badge_id,
            "revoked_date": datetime.now().isoformat(),
            "reason": reason or "Rank dropped below threshold",
            "revoked_by": "token-craft-system"
        }

        try:
            if not HAS_REQUESTS or not self.session:
                # Mock response
                print(f"[MOCK] Would revoke badge {badge_id} from {user_email}")
                return {
                    "success": True,
                    "badge_id": badge_id,
                    "message": "Badge revoked successfully (mock)"
                }

            # TODO: Replace with actual API endpoint
            # response = self.session.post(f"{self.api_url}/badges/revoke", json=payload)
            # response.raise_for_status()
            # return response.json()

            # Mock response
            print(f"[MOCK] Would revoke badge {badge_id} from {user_email}")
            return {
                "success": True,
                "badge_id": badge_id,
                "message": "Badge revoked successfully (mock)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_user_badges(self, user_email: str) -> List[Dict]:
        """
        Get all badges for a user.

        Args:
            user_email: User's email address

        Returns:
            List of badges
        """
        try:
            if not HAS_REQUESTS or not self.session:
                # Mock response
                return [
                    {
                        "badge_id": "token_craft_captain",
                        "title": "Token Craft Captain",
                        "issued_date": "2026-01-15T10:00:00Z",
                        "expires": "2027-01-15T10:00:00Z",
                        "status": "active"
                    }
                ]

            # TODO: Replace with actual API endpoint
            # response = self.session.get(f"{self.api_url}/users/{user_email}/badges")
            # response.raise_for_status()
            # return response.json()

            # Mock response
            return [
                {
                    "badge_id": "token_craft_captain",
                    "title": "Token Craft Captain",
                    "issued_date": "2026-01-15T10:00:00Z",
                    "expires": "2027-01-15T10:00:00Z",
                    "status": "active"
                }
            ]

        except Exception as e:
            print(f"Error fetching badges: {e}")
            return []

    def create_certification(self, user_email: str, rank: str, score: int, metrics: Dict) -> Dict:
        """
        Create certification for user.

        Args:
            user_email: User's email
            rank: Current rank
            score: Current score
            metrics: Performance metrics

        Returns:
            Certification data
        """
        certification_levels = {
            "Navigator": "foundation",
            "Commander": "foundation",
            "Captain": "professional",
            "Admiral": "professional",
            "Galactic Legend": "master"
        }

        cert_level = certification_levels.get(rank, "foundation")

        certification = {
            "user_email": user_email,
            "certification_id": f"token_craft_{cert_level}_{user_email}",
            "level": cert_level,
            "title": f"Token-Craft {cert_level.title()} Certification",
            "issued_date": datetime.now().isoformat(),
            "valid_until": self._calculate_expiry(rank),
            "rank_achieved": rank,
            "score": score,
            "evidence": metrics,
            "issuer": "EPAM Token-Craft System"
        }

        try:
            if not HAS_REQUESTS or not self.session:
                # Mock response
                print(f"[MOCK] Would issue {cert_level} certification to {user_email}")
                return {
                    "success": True,
                    "certification": certification,
                    "message": "Certification issued successfully (mock)"
                }

            # TODO: Replace with actual API endpoint
            # response = self.session.post(f"{self.api_url}/certifications/issue", json=certification)
            # response.raise_for_status()
            # return response.json()

            # Mock response
            print(f"[MOCK] Would issue {cert_level} certification to {user_email}")
            return {
                "success": True,
                "certification": certification,
                "message": "Certification issued successfully (mock)"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _calculate_expiry(self, rank: str) -> str:
        """Calculate certification expiry date based on rank."""
        from datetime import timedelta

        expiry_months = {
            "Cadet": 3,
            "Pilot": 3,
            "Navigator": 6,
            "Commander": 6,
            "Captain": 12,
            "Admiral": 12,
            "Galactic Legend": 0  # No expiry
        }

        months = expiry_months.get(rank, 6)

        if months == 0:
            return "never"

        expiry_date = datetime.now() + timedelta(days=months * 30)
        return expiry_date.isoformat()

    def sync_badges_with_rank(self, user_email: str, current_rank: str, previous_rank: str = None) -> Dict:
        """
        Sync badges based on rank changes.

        Args:
            user_email: User's email
            current_rank: Current rank
            previous_rank: Previous rank (if changed)

        Returns:
            Sync result
        """
        result = {
            "badges_issued": [],
            "badges_revoked": [],
            "certifications_updated": []
        }

        # Map ranks to badge IDs
        rank_badges = {
            "Cadet": "token_craft_cadet",
            "Pilot": "token_craft_pilot",
            "Navigator": "token_craft_navigator",
            "Commander": "token_craft_commander",
            "Captain": "token_craft_captain",
            "Admiral": "token_craft_admiral",
            "Galactic Legend": "token_craft_legend"
        }

        current_badge = rank_badges.get(current_rank)

        # Issue new badge
        if current_badge:
            issue_result = self.issue_badge(
                user_email,
                current_badge,
                {"rank": current_rank, "timestamp": datetime.now().isoformat()}
            )
            if issue_result.get("success"):
                result["badges_issued"].append(current_badge)

        # Revoke old badge if rank changed
        if previous_rank and previous_rank != current_rank:
            previous_badge = rank_badges.get(previous_rank)
            if previous_badge:
                revoke_result = self.revoke_badge(
                    user_email,
                    previous_badge,
                    f"Rank changed from {previous_rank} to {current_rank}"
                )
                if revoke_result.get("success"):
                    result["badges_revoked"].append(previous_badge)

        return result


class MockHeroClient(HeroAPIClient):
    """Mock hero client for testing without API."""

    def __init__(self):
        """Initialize mock client."""
        super().__init__(api_url="http://mock", api_key="mock_key")
        self.badges = {}  # user_email -> [badges]
        self.certifications = {}  # user_email -> [certs]

    def issue_badge(self, user_email: str, badge_id: str, evidence: Dict) -> Dict:
        """Mock badge issuance."""
        if user_email not in self.badges:
            self.badges[user_email] = []

        badge = {
            "badge_id": badge_id,
            "issued_date": datetime.now().isoformat(),
            "evidence": evidence,
            "status": "active"
        }

        self.badges[user_email].append(badge)

        return {
            "success": True,
            "badge_id": badge_id,
            "user_email": user_email,
            "message": "Badge issued successfully (mock)"
        }

    def get_user_badges(self, user_email: str) -> List[Dict]:
        """Get mock badges."""
        return self.badges.get(user_email, [])
