"""
NEXORA ATLAS - Domain Models Package
Exports all 16 domain entities to ensure clean Alembic autodiscovery.
"""

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from app.models.organization import Organization, AuditLog
from app.models.account import CloudRegion, CloudAccount, Integration, SyncJob
from app.models.resource import CloudResource, Tag
from app.models.cost import CostRecord, CostSnapshot
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.models.scenario import Scenario, ScenarioChange
from app.models.forecast import Forecast

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "Organization",
    "CloudAccount",
    "CloudRegion",
    "CloudResource",
    "CostRecord",
    "CostSnapshot",
    "Anomaly",
    "OptimizationOpportunity",
    "Recommendation",
    "Scenario",
    "ScenarioChange",
    "Forecast",
    "Tag",
    "SyncJob",
    "Integration",
    "AuditLog",
]
