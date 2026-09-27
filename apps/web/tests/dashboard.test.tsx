import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SpendTrendChart } from '../src/components/charts/SpendTrendChart';
import { ServiceBreakdownChart } from '../src/components/charts/ServiceBreakdownChart';
import { ObservedVsInferredCard } from '../src/components/ui/ObservedVsInferredCard';
import { AnomalyItem } from '../src/types/api';

describe('Dashboard Charts and FinOps Components', () => {
  it('renders SpendTrendChart with SVG area, gridlines, and event markers', () => {
    const points = [
      {
        date: '2026-03-01',
        spend: '12000.00',
        cumulative_spend: '12000.00',
        events: [],
      },
      {
        date: '2026-03-02',
        spend: '14500.00',
        cumulative_spend: '26500.00',
        events: [
          {
            id: 'ev-1',
            occurred_at: '2026-03-02T10:00:00Z',
            title: 'K8s Cluster Autoscaling Event',
            description: 'Autoscaler triggered 10 additional nodes during peak traffic.',
            category: 'DEPLOYMENT',
            impact_service: 'AmazonEC2',
          },
        ],
      },
      {
        date: '2026-03-03',
        spend: '11000.00',
        cumulative_spend: '37500.00',
        events: [],
      },
    ];

    const { container } = render(<SpendTrendChart points={points} height={260} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    // Verify gradient defs exist
    expect(container.querySelector('#spendGradient')).toBeInTheDocument();
    // Verify event pin renders
    expect(container.querySelector('circle[fill="#F59E0B"]')).toBeInTheDocument();
  });

  it('renders ServiceBreakdownChart with ranked bars and rupee formatting', () => {
    const items = [
      { service_name: 'AmazonEC2', total_spend: '2168000.00', percentage: '58.8' },
      { service_name: 'AmazonRDS', total_spend: '842000.00', percentage: '22.9' },
      { service_name: 'AmazonS3', total_spend: '673194.61', percentage: '18.3' },
    ];

    render(
      <MemoryRouter>
        <ServiceBreakdownChart items={items} />
      </MemoryRouter>
    );

    expect(screen.getByText('AmazonEC2')).toBeInTheDocument();
    expect(screen.getByText('AmazonRDS')).toBeInTheDocument();
    expect(screen.getByText('AmazonS3')).toBeInTheDocument();
    expect(screen.getByText('58.8%')).toBeInTheDocument();
  });

  it('renders ObservedVsInferredCard cleanly separating observed facts from inference', () => {
    const anomaly: AnomalyItem = {
      id: 'anom-123',
      account_id: 'acc-1',
      account_name: 'Production Core',
      resource_id: 'res-1',
      resource_name: 'Analytics Worker Pool',
      resource_native_id: 'i-0a8b9c1d2e',
      service_name: 'AmazonEC2',
      observed: {
        observed_cost: '34200.00',
        baseline_cost: '8500.00',
        percentage_change: '302.35',
        detected_at: '2026-03-10T14:30:00Z',
        detection_rule: 'STATISTICAL_ZSCORE',
        observed_metrics_json: {
          z_score: 3.84,
          avg_baseline: 8500.0,
        },
      },
      inference: {
        severity: 'CRITICAL',
        status: 'OPEN',
        inferred_cause: 'Uncontrolled GPU node autoscaling loop triggered by failed batch ETL pipeline.',
        confidence_pct: '92.5',
        inference_details_json: {
          hypothesis: 'ETL worker restart loop with excessive spot preemption',
        },
      },
    };

    render(
      <MemoryRouter>
        <ObservedVsInferredCard anomaly={anomaly} defaultExpanded={true} />
      </MemoryRouter>
    );

    // Header & Resource
    expect(screen.getByText('Analytics Worker Pool')).toBeInTheDocument();
    expect(screen.getByText('Production Core')).toBeInTheDocument();

    // Observed Facts section
    expect(screen.getByText(/Observed Facts/i)).toBeInTheDocument();
    expect(screen.getByText(/Empirical Truth/i)).toBeInTheDocument();
    expect(screen.getAllByText('+302.35%').length).toBe(2);

    // Inferred Analysis section
    expect(screen.getByText(/Inferred Analysis/i)).toBeInTheDocument();
    expect(screen.getByText(/Uncontrolled GPU node autoscaling/i)).toBeInTheDocument();
    expect(screen.getByText('92.5%')).toBeInTheDocument();
  });
});
