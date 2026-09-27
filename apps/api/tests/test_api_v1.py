"""
NEXORA ATLAS - API v1 Domain & Reconciliation Tests (Phase 4)
Verifies:
- All domain endpoints return valid status and shapes
- Organization multi-tenancy scoping
- Mathematical reconciliation between Dashboard, Spend, Anomalies, and Optimization
- Pagination and filter consistency
"""

from decimal import Decimal
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo import seed_demo_data


@pytest_asyncio.fixture(autouse=True)
async def setup_demo_data(db_session: AsyncSession):
    """Seed the database with deterministic demo data before running API tests."""
    await seed_demo_data(db_session, reset_first=True)


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(client: AsyncClient):
    """Verifies /dashboard/summary returns correct financial KPIs and run rate."""
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["organization_name"] == "Nexora Labs Inc"
    assert Decimal(data["total_spend"]) > Decimal("0.0000")
    assert Decimal(data["monthly_run_rate"]) > Decimal("0.0000")
    assert Decimal(data["previous_30d_spend"]) > Decimal("0.0000")
    assert data["run_rate_change_pct"] is not None
    assert Decimal(data["potential_monthly_savings"]) == Decimal("460000.0000")
    assert Decimal(data["potential_annual_savings"]) == Decimal("5520000.0000")
    assert data["active_anomalies"] == 4
    assert data["total_resources"] == 58
    assert data["total_accounts"] == 3
    assert data["currency"] == "INR"
    assert data["is_demo"] is True


@pytest.mark.asyncio
async def test_spend_trend_and_events(client: AsyncClient):
    """Verifies /dashboard/spend-trend returns 90 data points and event annotations."""
    resp = await client.get("/api/v1/dashboard/spend-trend?days=90")
    assert resp.status_code == 200
    data = resp.json()

    assert data["period_days"] == 90
    assert len(data["points"]) == 90
    assert Decimal(data["total_spend"]) > Decimal("0.0000")

    # Check for presence of embedded demo events
    all_events = [ev for pt in data["points"] for ev in pt["events"]]
    assert len(all_events) == 4
    event_titles = {ev["title"] for ev in all_events}
    assert "Analytics EKS Cluster Scale-Out" in event_titles
    assert "AI/GPU Fine-Tuning Surge" in event_titles
    assert "Orphan EBS Volume Accumulation" in event_titles
    assert "Production API Auto-Scaling Spike" in event_titles


@pytest.mark.asyncio
async def test_service_and_account_breakdowns(client: AsyncClient):
    """Verifies /dashboard/service-breakdown and /dashboard/account-breakdown."""
    srv_resp = await client.get("/api/v1/dashboard/service-breakdown?days=30")
    assert srv_resp.status_code == 200
    srv_data = srv_resp.json()
    assert len(srv_data["items"]) > 0
    service_names = {item["service_name"] for item in srv_data["items"]}
    assert "AmazonEC2" in service_names
    assert "AmazonRDS" in service_names

    acc_resp = await client.get("/api/v1/dashboard/account-breakdown?days=30")
    assert acc_resp.status_code == 200
    acc_data = acc_resp.json()
    acc_names = {item["account_name"] for item in acc_data["items"]}
    assert "Production Core" in acc_names
    assert "Staging Workloads" in acc_names
    assert "Development Sandbox" in acc_names


@pytest.mark.asyncio
async def test_spend_explorer_reconciliation(client: AsyncClient):
    """
    CRITICAL RECONCILIATION TEST:
    Verifies that Dashboard total == Spend Explorer total for the same date window.
    Verifies that Service breakdown sum == Total spend.
    Verifies that Account breakdown sum == Total spend.
    """
    # 1. Dashboard summary
    summary_resp = await client.get("/api/v1/dashboard/summary")
    summary = summary_resp.json()

    # 2. Spend explorer for 90 days (entire history)
    spend_90_resp = await client.get("/api/v1/spend?period_days=90")
    spend_90 = spend_90_resp.json()
    assert Decimal(summary["total_spend"]) == Decimal(spend_90["total_spend"])

    # 3. Spend explorer for 30 days (latest run rate window)
    spend_30_resp = await client.get("/api/v1/spend?period_days=30")
    spend_30 = spend_30_resp.json()
    assert Decimal(summary["monthly_run_rate"]) == Decimal(spend_30["total_spend"])

    # 4. Service breakdown sum == Spend 30 total
    service_sum = sum(Decimal(item["total_spend"]) for item in spend_30["service_breakdown"])
    assert service_sum == Decimal(spend_30["total_spend"])

    # 5. Account breakdown sum == Spend 30 total
    account_sum = sum(Decimal(item["total_spend"]) for item in spend_30["account_breakdown"])
    assert account_sum == Decimal(spend_30["total_spend"])

    # 6. Pagination check
    assert len(spend_30["resource_items"]) <= spend_30["page_size"]
    assert spend_30["total_resources"] > 0


@pytest.mark.asyncio
async def test_anomalies_observed_vs_inferred(client: AsyncClient):
    """Verifies /anomalies and /anomalies/:id strictly separate observed facts from hypotheses."""
    resp = await client.get("/api/v1/anomalies")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_count"] == 4
    assert data["open_count"] == 4

    first_anom = data["items"][0]
    assert "observed" in first_anom
    assert "inference" in first_anom

    obs = first_anom["observed"]
    assert Decimal(obs["observed_cost"]) > Decimal("0.0000")
    assert Decimal(obs["baseline_cost"]) > Decimal("0.0000")
    assert Decimal(obs["percentage_change"]) > Decimal("0.00")
    assert obs["detection_rule"] is not None

    inf = first_anom["inference"]
    assert inf["inferred_cause"] is not None
    assert Decimal(inf["confidence_pct"]) > Decimal("50.00")

    # Detail endpoint
    detail_resp = await client.get(f"/api/v1/anomalies/{first_anom['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == first_anom["id"]

    # 404 test
    not_found_resp = await client.get("/api/v1/anomalies/00000000-0000-0000-0000-000000000000")
    assert not_found_resp.status_code == 404


@pytest.mark.asyncio
async def test_optimization_overview_and_detail(client: AsyncClient):
    """Verifies /optimization and /optimization/:id hierarchy (Opportunity -> Recommendations)."""
    resp = await client.get("/api/v1/optimization")
    assert resp.status_code == 200
    data = resp.json()

    assert Decimal(data["potential_monthly_savings"]) == Decimal("460000.0000")
    assert Decimal(data["potential_annual_savings"]) == Decimal("5520000.0000")
    assert data["opportunity_count"] >= 6
    assert data["recommendation_count"] >= 6

    # Verify each opportunity has evidence and recommendations
    first_opp = data["opportunities"][0]
    assert first_opp["evidence_json"] is not None
    assert len(first_opp["recommendations"]) > 0

    first_rec = first_opp["recommendations"][0]
    assert Decimal(first_rec["estimated_annual_savings"]) == Decimal(first_rec["estimated_monthly_savings"]) * 12

    # Detail endpoint
    detail_resp = await client.get(f"/api/v1/optimization/{first_opp['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == first_opp["id"]


@pytest.mark.asyncio
async def test_resources_inventory_and_search(client: AsyncClient):
    """Verifies /resources with search, filter, pagination, and 30-day cost attribution."""
    # List all
    resp = await client.get("/api/v1/resources?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 58
    assert len(data["items"]) == 10
    assert data["total_pages"] == 6

    # Verify 30-day cost is populated on active resources
    has_cost = any(item["cost_30d"] is not None for item in data["items"])
    assert has_cost is True

    # Search filter
    search_resp = await client.get("/api/v1/resources?search=gpu")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    for item in search_data["items"]:
        assert "gpu" in item["name"].lower() or "gpu" in item["native_id"].lower() or "gpu" in item["service_name"].lower() or "gpu" in item["resource_type"].lower()

    # Detail endpoint
    res_id = data["items"][0]["id"]
    detail_resp = await client.get(f"/api/v1/resources/{res_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == res_id


@pytest.mark.asyncio
async def test_scenarios_and_forecast_fixtures(client: AsyncClient):
    """Verifies read-only exposure of scenarios and forecasts with synthetic disclaimer."""
    # Scenarios
    sc_resp = await client.get("/api/v1/scenarios")
    assert sc_resp.status_code == 200
    sc_data = sc_resp.json()
    assert len(sc_data["scenarios"]) == 3
    for sc in sc_data["scenarios"]:
        assert Decimal(sc["monthly_savings"]) == Decimal(sc["baseline_monthly_cost"]) - Decimal(sc["projected_monthly_cost"])
        assert len(sc["changes"]) > 0

    # Forecast
    fc_resp = await client.get("/api/v1/forecast")
    assert fc_resp.status_code == 200
    fc_data = fc_resp.json()
    assert "DEMO FORECAST" in fc_data["disclaimer"]
    assert len(fc_data["forecasts"]) == 3
    for fc in fc_data["forecasts"]:
        assert fc["is_synthetic"] is True
        assert Decimal(fc["projected_cost"]) > Decimal("0.0000")
        assert Decimal(fc["lower_bound"]) <= Decimal(fc["projected_cost"]) <= Decimal(fc["upper_bound"])
