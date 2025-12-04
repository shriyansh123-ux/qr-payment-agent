from typing import Dict


class SimpleMemoryBank(object):
    def __init__(self):
        self._store: Dict[str, Dict[str, str]] = {}

    def get_profile(self, user_id: str) -> Dict[str, str]:
        return self._store.get(user_id, {})

    def upsert_profile(self, user_id: str, updates: Dict[str, str]) -> None:
        profile = self._store.get(user_id, {})
        profile.update(updates)
        self._store[user_id] = profile
