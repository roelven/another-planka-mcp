from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import time

# ==================== CACHE SYSTEM ====================

@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: int  # seconds

    def is_valid(self) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - self.timestamp < self.ttl

class PlankaCache:
    """Multi-tier caching system optimized for low-concurrency environment."""

    def __init__(self):
        # Workspace structure (projects, boards, lists, labels, users)
        self.workspace: Optional[CacheEntry] = None

        # Board overview caches {board_id: CacheEntry}
        self.board_overviews: Dict[str, CacheEntry] = {}

        # Per-card detail caches {card_id: CacheEntry}
        self.card_details: Dict[str, CacheEntry] = {}

        # Statistics for monitoring
        self.stats = {
            "workspace_hits": 0,
            "workspace_misses": 0,
            "board_overview_hits": 0,
            "board_overview_misses": 0,
            "card_hits": 0,
            "card_misses": 0,
        }

    async def get_workspace(self, fetch_func):
        """Get workspace structure. TTL: 5 minutes. Expected hit rate: 90%+"""
        if self.workspace and self.workspace.is_valid():
            self.stats["workspace_hits"] += 1
            return self.workspace.data

        self.stats["workspace_misses"] += 1
        data = await fetch_func()
        self.workspace = CacheEntry(data=data, timestamp=time.time(), ttl=300)
        return data

    async def get_board_overview(self, board_id: str, fetch_func):
        """Get board overview. TTL: 3 minutes. Expected hit rate: 70-80%"""
        if board_id in self.board_overviews:
            entry = self.board_overviews[board_id]
            if entry.is_valid():
                self.stats["board_overview_hits"] += 1
                return entry.data

        self.stats["board_overview_misses"] += 1
        data = await fetch_func()
        self.board_overviews[board_id] = CacheEntry(
            data=data, timestamp=time.time(), ttl=180
        )
        return data

    async def get_card(self, card_id: str, fetch_func):
        """Get card details. TTL: 1 minute. Expected hit rate: 40-50%"""
        if card_id in self.card_details:
            entry = self.card_details[card_id]
            if entry.is_valid():
                self.stats["card_hits"] += 1
                return entry.data

        self.stats["card_misses"] += 1
        data = await fetch_func()
        self.card_details[card_id] = CacheEntry(
            data=data, timestamp=time.time(), ttl=60
        )
        return data

    def invalidate_workspace(self):
        """Invalidate workspace cache (call after structural changes)."""
        self.workspace = None

    def invalidate_board(self, board_id: str):
        """Invalidate board overview cache (call after board changes)."""
        if board_id in self.board_overviews:
            del self.board_overviews[board_id]

    def invalidate_card(self, card_id: str):
        """Invalidate card cache (call after card updates)."""
        if card_id in self.card_details:
            del self.card_details[card_id]

    def cleanup_card_cache(self):
        """Remove old entries to limit memory usage."""
        if len(self.card_details) > 300:  # Updated max card cache size
            sorted_entries = sorted(
                self.card_details.items(),
                key=lambda x: x[1].timestamp
            )
            # Keep only the most recent entries
            self.card_details = dict(sorted_entries[-100:])