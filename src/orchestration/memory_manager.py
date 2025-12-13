from typing import Dict, Any, List
from collections import deque


class SimpleMemoryBank:
    """
    Very simple long-term memory store.
    - user_profiles: stores user preferences
    - merchant_history: stores recent merchants seen (for risk scoring)
    """

    def __init__(self, max_merchants: int = 50):
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self._recent_merchants = deque(maxlen=max_merchants)

    # ---------- Profiles ----------
    def upsert_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        existing = self.user_profiles.get(user_id, {})
        existing.update(profile)
        self.user_profiles[user_id] = existing

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        return self.user_profiles.get(user_id, {})

    # ---------- Merchant History ----------
    def add_recent_merchant(self, merchant_id: str, country: str) -> None:
        self._recent_merchants.appendleft({"merchant_id": merchant_id, "country": country})

    def get_recent_merchants(self) -> List[Dict[str, Any]]:
        return list(self._recent_merchants)
