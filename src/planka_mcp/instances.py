from typing import Optional
from .cache import PlankaCache
from .api_client import PlankaAPIClient

# Global instances (initialized on startup)
api_client: Optional[PlankaAPIClient] = None
cache: Optional[PlankaCache] = None
