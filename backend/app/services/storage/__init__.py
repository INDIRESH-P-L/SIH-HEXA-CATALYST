"""The storage seam: local disk or Supabase Storage, one interface."""

from app.services.storage.provider import StorageProvider, StoredObject, get_storage_provider

__all__ = ["StorageProvider", "StoredObject", "get_storage_provider"]
