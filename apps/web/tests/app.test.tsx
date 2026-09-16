import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../src/app/App';

describe('NEXORA ATLAS Application Shell & Smoke Tests', () => {
  it('renders application shell with brand and demo banner', () => {
    render(<App />);

    // Brand check
    expect(screen.getByText('ATLAS')).toBeInTheDocument();
    expect(screen.getByText('Cost Intelligence')).toBeInTheDocument();

    // Demo banner check
    expect(screen.getByText('DEMO ENVIRONMENT')).toBeInTheDocument();

    // Default overview route check
    expect(screen.getByText('Overview Dashboard')).toBeInTheDocument();
  });

  it('renders primary navigation items in sidebar', () => {
    render(<App />);

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Spend')).toBeInTheDocument();
    expect(screen.getByText('Anomalies')).toBeInTheDocument();
    expect(screen.getByText('Optimization')).toBeInTheDocument();
    expect(screen.getByText('Scenarios')).toBeInTheDocument();
    expect(screen.getByText('Forecast')).toBeInTheDocument();
    expect(screen.getByText('Resources')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('displays provider status at bottom of sidebar', () => {
    render(<App />);

    expect(screen.getByText('PROVIDER:')).toBeInTheDocument();
    expect(screen.getByText('DEMO')).toBeInTheDocument();
  });
});
