# app/schemas/system.py
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ServiceStatus(BaseModel):
    """Status of a single service."""
    status: str  # 'ok' or 'error'
    latency_ms: Optional[float] = None


class ServicesStatus(BaseModel):
    """Status of all services."""
    database: ServiceStatus
    redis: ServiceStatus
    storage: ServiceStatus


class MaintenanceStatus(BaseModel):
    """Maintenance mode status."""
    enabled: bool = False
    message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Response for /system/status endpoint."""
    status: str  # 'ok' or 'degraded'
    timestamp: str
    version: str
    environment: str
    services: ServicesStatus
    maintenance: MaintenanceStatus
    
    class Config:
        from_attributes = True


class MaintenanceEnableRequest(BaseModel):
    """Request to enable maintenance mode."""
    message: Optional[str] = None


class MaintenanceEnableResponse(BaseModel):
    """Response for enabling/disabling maintenance."""
    status: str
    message: str
    data: MaintenanceStatus
    
    class Config:
        from_attributes = True


class MaintenanceStatusResponse(BaseModel):
    """Response for /system/maintenance/status endpoint."""
    maintenance_mode: bool
    message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================
# Version Check Schemas
# ============================================

class VersionCheckResponse(BaseModel):
    """Response for /system/version-check endpoint."""
    status: str  # 'ok', 'update_required', 'maintenance'
    message: Optional[str] = None
    current_version: str
    minimum_version: str
    platform: str
    update_url: Optional[str] = None
    force_update: bool = False
    
    class Config:
        from_attributes = True


class VersionCheckRequest(BaseModel):
    """Request for /system/version-check endpoint."""
    platform: str  # 'android' or 'ios'
    version: str   # e.g., '1.2.3'