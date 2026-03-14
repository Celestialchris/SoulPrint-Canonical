"""Read-only retrieval helpers that compose existing storage lanes."""

from .federated import FederatedReadResult, federated_search

__all__ = ["FederatedReadResult", "federated_search"]
