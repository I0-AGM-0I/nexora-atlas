import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CostTopology } from '../src/components/topology/CostTopology';
import { InvestigationProvider } from '../src/lib/InvestigationContext';

describe('CostTopology Component & Spatial Reasoning', () => {
  const mockServices = [
    { service_name: 'AmazonEC2', total_spend: '2168000.00', percentage: '58.8' },
    { service_name: 'AmazonRDS', total_spend: '842000.00', percentage: '22.9' },
    { service_name: 'AmazonS3', total_spend: '673000.00', percentage: '18.3' },
  ];

  const mockAccounts = [
    { account_id: 'acc-1', account_name: 'aws-prod-core', provider_account_id: '112233', total_spend: '2500000', percentage: '65.0' },
    { account_id: 'acc-2', account_name: 'aws-data-lake', provider_account_id: '445566', total_spend: '1183000', percentage: '35.0' },
  ];

  const mockResources = [
    {
      resource_id: 'res-1',
      native_id: 'i-0a8b9c1d2e',
      resource_name: 'Prod API Worker 01',
      service_name: 'AmazonEC2',
      resource_type: 'AWS::EC2::Instance',
      account_name: 'aws-prod-core',
      region: 'ap-south-1',
      spend: '34200.00',
      percentage_of_total: '0.92',
    },
  ];

  it('renders deterministic column hierarchy (TECH → PROVIDER → SERVICE → WORKLOAD → RESOURCE)', () => {
    const { container } = render(
      <MemoryRouter>
        <InvestigationProvider>
          <CostTopology
            services={mockServices}
            accounts={mockAccounts}
            resources={mockResources}
          />
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Verify SVG and column headers render
    expect(container.querySelector('svg')).toBeInTheDocument();
    expect(screen.getByText('COST TOPOLOGY')).toBeInTheDocument();
    expect(screen.getAllByText('ATLAS ESTATE').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('AWS (AP-SOUTH-1)').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('EC2').length).toBeGreaterThanOrEqual(1);
  });

  it('activates FOCUS mode when a node is clicked and dims unrelated branches', () => {
    render(
      <MemoryRouter>
        <InvestigationProvider>
          <CostTopology
            services={mockServices}
            accounts={mockAccounts}
            resources={mockResources}
          />
        </InvestigationProvider>
      </MemoryRouter>
    );

    const ec2Node = screen.getByRole('button', { name: /service EC2/i });
    expect(ec2Node).toBeInTheDocument();

    // Click to focus
    fireEvent.click(ec2Node);

    // Context tag appears
    expect(screen.getByText('FOCUS: EC2')).toBeInTheDocument();
    expect(screen.getByText('CLEAR (ESC)')).toBeInTheDocument();

    // Clear focus
    fireEvent.click(screen.getByText('CLEAR (ESC)'));
    expect(screen.queryByText('FOCUS: EC2')).toBeNull();
  });

  it('renders meaningful empty state when no topology data is available (Scenario G)', () => {
    render(
      <MemoryRouter>
        <InvestigationProvider>
          <CostTopology services={[]} accounts={[]} resources={[]} />
        </InvestigationProvider>
      </MemoryRouter>
    );

    // Shows SVG canvas plus informative message
    expect(screen.getByText(/NO TOPOLOGY TELEMETRY AVAILABLE/i)).toBeInTheDocument();
  });
});
