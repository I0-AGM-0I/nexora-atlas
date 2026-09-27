"""
NEXORA ATLAS - Resource Inventory API Schemas
"""

from decimal import Decimal
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict


class ResourceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    account_name: str
    region_code: str
    native_id: str
    name: str
    service_name: str
    resource_type: str
    status: str
    tags: Dict[str, str] = {}
    cost_30d: Optional[Decimal] = None


class ResourceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ResourceListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
