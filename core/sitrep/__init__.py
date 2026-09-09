"""Authoritative, read-only SITREP ingestion."""
from .service import SitrepService, get_sitrep_service
__all__ = ["SitrepService", "get_sitrep_service"]
