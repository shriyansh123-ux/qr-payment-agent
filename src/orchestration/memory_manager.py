from typing import Dict, Any


class SimpleMemoryBank:
    """
    In-process user preferences for reference conversion.
    """

    def __init__(self):
        self.user_profiles: Dict[str, Dict[str, Any]] = {}

    # ---------- Profiles ----------
    def upsert_profile(self, user_id: str, profile: Dict[str, Any]) -> None:
        existing = self.user_profiles.get(user_id, {})
        existing.update(profile)
        self.user_profiles[user_id] = existing

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        return self.user_profiles.get(user_id, {})
