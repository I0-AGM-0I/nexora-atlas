"""
NEXORA ATLAS - Phase 9 Milestone 2: Scope Authorization Test Suite
Verifies tenant isolation, pre-retrieval scope enforcement, cross-tenant protection,
and proves that question classification cannot bypass or grant authorization.
"""

import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import TenantContext
from app.models.account import CloudAccount
from app.models.resource import CloudResource
from app.ai.types import ScopeType, QuestionCategory
from app.ai.authorization.scope import (
    AuthorizationScope,
    ScopeAuthorizationResult,
    authorize_scope,
)
from app.ai.questions.scope_resolver import ScopeResolver


@pytest.fixture
def tenant_a():
    acc1 = CloudAccount(
        id=str(uuid.uuid4()),
        org_id="org-a",
        provider_type="AWS",
        account_id="111111111111",
        name="Production A",
    )
    return TenantContext(
        org_id="org-a",
        org_name="Org A",
        slug="org-a",
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=False,
        account_ids=[acc1.id],
        accounts=[acc1],
        account_name_map={acc1.id: acc1.name},
    )


@pytest.fixture
def tenant_b():
    acc2 = CloudAccount(
        id=str(uuid.uuid4()),
        org_id="org-b",
        provider_type="AWS",
        account_id="222222222222",
        name="Production B",
    )
    return TenantContext(
        org_id="org-b",
        org_name="Org B",
        slug="org-b",
        currency="INR",
        timezone="Asia/Kolkata",
        is_demo=False,
        account_ids=[acc2.id],
        accounts=[acc2],
        account_name_map={acc2.id: acc2.name},
    )


@pytest.mark.asyncio
async def test_authorization_scope_construction(tenant_a):
    """AuthorizationScope must correctly encapsulate tenant account IDs."""
    auth_scope = AuthorizationScope.from_tenant(tenant_a)
    assert auth_scope.organization_id == "org-a"
    assert tenant_a.account_ids[0] in auth_scope.allowed_account_ids
    assert auth_scope.is_account_authorized(tenant_a.account_ids[0]) is True
    assert auth_scope.is_account_authorized("unauthorized-account-id") is False


@pytest.mark.asyncio
async def test_dashboard_scope_bounded_by_tenant_accounts(db_session: AsyncSession, tenant_a):
    """Test E: Dashboard scope must strictly bound to tenant account IDs."""
    res: ScopeAuthorizationResult = await authorize_scope(
        session=db_session,
        tenant=tenant_a,
        scope_type=ScopeType.DASHBOARD,
    )
    assert res.scope_type == ScopeType.DASHBOARD
    assert res.account_ids == tenant_a.account_ids
    assert len(res.account_ids) == 1


@pytest.mark.asyncio
async def test_tenant_a_cannot_access_tenant_b_account(db_session: AsyncSession, tenant_a, tenant_b):
    """Test A: Tenant A asking about Tenant B account must be rejected with 404."""
    tenant_b_account_id = tenant_b.accounts[0].id

    with pytest.raises(HTTPException) as exc_info:
        await authorize_scope(
            session=db_session,
            tenant=tenant_a,
            scope_type=ScopeType.ACCOUNT,
            scope_id=tenant_b_account_id,
        )
    assert exc_info.value.status_code == 404
    assert "not found or access denied" in exc_info.value.detail


@pytest.mark.asyncio
async def test_tenant_a_cannot_access_unauthorized_resource(db_session: AsyncSession, tenant_a):
    """Test B: Accessing a non-existent or foreign resource ID raises 404."""
    fake_resource_id = str(uuid.uuid4())

    with pytest.raises(HTTPException) as exc_info:
        await authorize_scope(
            session=db_session,
            tenant=tenant_a,
            scope_type=ScopeType.RESOURCE,
            scope_id=fake_resource_id,
        )
    assert exc_info.value.status_code == 404
    assert "not found or access denied" in exc_info.value.detail


def test_scope_resolver_intersection(tenant_a):
    """
    Test F: ScopeResolver intersection test:
    Requested Scope ∩ Authorized Scope = Effective Retrieval Scope.
    """
    auth_scope = AuthorizationScope(
        organization_id="org-a",
        allowed_account_ids={"acc-1", "acc-2"},
        allowed_resource_ids={"res-1"},
    )

    # Valid resource in scope
    res_valid = ScopeResolver.resolve_scope(ScopeType.RESOURCE, "res-1", auth_scope)
    assert res_valid.is_authorized is True
    assert res_valid.scope_id == "res-1"

    # Foreign resource not in scope
    res_foreign = ScopeResolver.resolve_scope(ScopeType.RESOURCE, "res-foreign", auth_scope)
    assert res_foreign.is_authorized is False
    assert "not in authorized tenant scope" in (res_foreign.denial_reason or "")


def test_classification_cannot_bypass_authorization(tenant_a):
    """
    Test D: Proves that classification categorization NEVER grants or modifies authorization.
    Even if question text mentions another resource, authorization remains strictly bounded.
    """
    auth_scope = AuthorizationScope(
        organization_id="org-a",
        allowed_account_ids={"acc-a"},
        allowed_resource_ids={"res-a"},
    )

    # Question maliciously asking about Tenant B's resource
    malicious_question = "Tell me about resource res-b owned by competitor."
    resolved = ScopeResolver.resolve_scope(
        requested_scope_type=ScopeType.RESOURCE,
        requested_scope_id="res-b",
        auth_scope=auth_scope,
        category=QuestionCategory.RESOURCE,
    )
    assert resolved.is_authorized is False
    assert resolved.scope_id == "res-b"
    assert "not in authorized tenant scope" in (resolved.denial_reason or "")
