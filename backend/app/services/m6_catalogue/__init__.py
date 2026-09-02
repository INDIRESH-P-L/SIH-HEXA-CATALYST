"""M6 · iGOT / NSSTA catalogue integration."""

from app.services.m6_catalogue.provider import (
    CatalogueProvider,
    EnrollmentDTO,
    NominationDTO,
    OfferingDTO,
    ProviderInfo,
    get_catalogue_provider,
)

__all__ = [
    "CatalogueProvider",
    "EnrollmentDTO",
    "NominationDTO",
    "OfferingDTO",
    "ProviderInfo",
    "get_catalogue_provider",
]
