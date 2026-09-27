import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../src/app/App';

describe('NEXORA ATLAS Application Shell & Smoke Tests', () => {
  it('renders application shell with brand and demo banner', () => {
    render(<App />);

    // Brand check in Global Header
    expect(screen.getByText('ATLAS')).toBeInTheDocument();

    // Demo banner check
    expect(screen.getByText('DEMO ENVIRONMENT')).toBeInTheDocument();

    // Navigation Rail check
    expect(screen.getByRole('navigation', { name: /coordinate navigation rail/i })).toBeInTheDocument();
  });

  it('renders coordinate navigation spine items 01 through 09', () => {
    render(<App />);

    expect(screen.getByRole('link', { name: /01 — Command Center/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /02 — Spend/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /03 — Forecast/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /04 — Changes/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /05 — Optimization/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /06 — Scenarios/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /07 — Resources/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /08 — Integrations/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /09 — Settings/i })).toBeInTheDocument();
  });

  it('displays provider status and trust boundary in global header and demo banner', () => {
    render(<App />);

    expect(screen.getByText('PROD')).toBeInTheDocument();
    expect(screen.getByText('AP-SOUTH-1')).toBeInTheDocument();
    expect(screen.getByText('READ ONLY')).toBeInTheDocument();
    expect(screen.getByText('Zero Live Mutations')).toBeInTheDocument();
  });
});

