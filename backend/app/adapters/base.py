# @PRODUCT Adapter — OS Core
"""Base adapter interface for data source adapters."""
from abc import ABC, abstractmethod
from typing import Any

class BaseAdapter(ABC):
    """Base class for runtime data source adapters."""

    @abstractmethod
    def sync(self) -> dict:
        """Sync data from source to SQLite. Returns summary dict."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Check if data source is accessible."""
        pass
