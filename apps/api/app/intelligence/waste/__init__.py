"""
NEXORA ATLAS - Waste Intelligence Module Exports
"""

from app.intelligence.waste.calculators import (
    calculate_unattached_storage_waste,
    calculate_off_hours_idle_waste,
    calculate_gp3_migration_waste,
    calculate_rightsizing_waste,
)
from app.intelligence.waste.rules import (
    UnattachedVolumeRule,
    OversizedInstanceRule,
    OffHoursIdleRule,
    IdleDatabaseRule,
    LegacyStorageTierRule,
    UnassociatedEIPRule,
    UnmanagedObjectVersionsRule,
)
from app.intelligence.waste.detector import WasteDetector

__all__ = [
    "calculate_unattached_storage_waste",
    "calculate_off_hours_idle_waste",
    "calculate_gp3_migration_waste",
    "calculate_rightsizing_waste",
    "UnattachedVolumeRule",
    "OversizedInstanceRule",
    "OffHoursIdleRule",
    "IdleDatabaseRule",
    "LegacyStorageTierRule",
    "UnassociatedEIPRule",
    "UnmanagedObjectVersionsRule",
    "WasteDetector",
]
