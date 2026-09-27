import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AskAtlasDrawer } from '../src/components/ai/AskAtlasDrawer';
import { AIAnswerView } from '../src/components/ai/AIAnswerView';
import { InteractiveEvidenceCitation } from '../src/components/ai/InteractiveEvidenceCitation';
import { AIProvenanceModal } from '../src/components/ai/AIProvenanceModal';
import { AIStatusFlyout } from '../src/components/ai/AIStatusFlyout';
import type {
  AIAskResponse,
  AIStatusResponse,
  AIInteractionDetailResponse,
} from '../src/types/api';

vi.mock('../src/lib/api', () => ({
  api: {
    askAtlas: vi.fn(),
    getAIStatus: vi.fn(),
    getAIInteraction: vi.fn(),
  },
}));

import { api } from '../src/lib/api';

const mockSpendResponse: AIAskResponse = {
  interaction_id: 'int-spend-001',
  session_id: 'sess-001',
  status: 'COMPLETED',
  question: 'Why did monthly spend increase?',
  scope_type: 'DASHBOARD',
  answer: {
    summary: 'EC2 compute spend increased by ₹2,14,000 (+18.7%) over baseline, driven by production API auto-scaling.',
    answer: 'Detailed investigation reveals that EC2 instances in ap-south-1 expanded compute hours by 38.2% following increased traffic. CloudWatch telemetry confirms 88.8% capacity headroom.',
    conclusions: [
      {
        statement: 'Observed monthly EC2 spend increased by ₹2,14,000 (+18.7%).',
        epistemic_class: 'OBSERVED',
        evidence_ids: ['ev-ce-ec2-01'],
        numeric_claims: [
          { value: 214000, unit: 'INR', evidence_id: 'ev-ce-ec2-01', description: 'Monthly EC2 delta' },
        ],
      },
      {
        statement: 'Production API nodes maintained 11.2% P95 CPU utilization over 14 days.',
        epistemic_class: 'OBSERVED',
        evidence_ids: ['ev-cw-p95-cpu'],
        numeric_claims: [
          { value: 11.2, unit: '%', evidence_id: 'ev-cw-p95-cpu', description: 'P95 CPU' },
        ],
      },
    ],
    limitations: [
      'Cost data current through 8 hours ago.',
    ],
    recommended_next_steps: [
      'Trace driver causality in Spend Explorer.',
      'Review rightsizing opportunities in Decision Room.',
    ],
    cited_entities: [
      {
        id: 'cit-01',
        title: 'Production Compute Cluster',
        entity_type: 'RESOURCE',
        entity_id: 'i-0eks-node-m5-4x-01',
        link_path: '/resources/i-0eks-node-m5-4x-01',
        description: 'Primary compute cluster node',
      },
    ],
    epistemic_notes: ['Numeric claims checked against Cost Explorer within ±1.0% tolerance.'],
    freshness_note: 'Cost data through 2026-09-26',
  },
  evidence_hash: 'e8f14b39a7c2d91f84b602e1c7593da502938475618293a4b5c6d7e8f9012345',
  evidence_count: 14,
  evidence_ids: ['ev-ce-ec2-01', 'ev-cw-p95-cpu', 'ev-raw-billing-01'],
  data_freshness: {
    status: 'FRESH',
    freshness_summary: 'Cost data synced 8 min ago · CloudWatch metrics 5m latency',
  },
  latency_ms: 312,
  token_count: 890,
  estimated_cost_usd: '0.00224',
  created_at: '2026-09-26T13:40:00Z',
};

const mockInsufficientTelemetryResponse: AIAskResponse = {
  interaction_id: 'int-telemetry-002',
  session_id: 'sess-002',
  status: 'COMPLETED',
  question: 'What is memory utilization for this unmanaged instance?',
  scope_type: 'RESOURCE',
  scope_id: 'i-0eks-node-m5-4x-01',
  answer: {
    summary: 'Memory telemetry is not configured for this resource.',
    answer: 'CloudWatch agent is not detected on instance i-0eks-node-m5-4x-01. Memory metrics are therefore unavailable.',
    conclusions: [
      {
        statement: 'Memory metrics are unconfigured. Downsizing recommendation is withheld.',
        epistemic_class: 'NOT_AVAILABLE',
        evidence_ids: ['ev-cw-mem-missing'],
        numeric_claims: [],
      },
    ],
    limitations: [
      'Memory telemetry coverage is 0% (CloudWatch agent missing). Recommendation withheld to prevent ungrounded downsizing.',
    ],
    recommended_next_steps: [
      'Install Amazon CloudWatch Agent to enable memory observation.',
    ],
    cited_entities: [],
    epistemic_notes: [],
  },
  evidence_hash: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b',
  evidence_count: 4,
  evidence_ids: ['ev-cw-mem-missing'],
  data_freshness: {
    status: 'FRESH',
    freshness_summary: 'Resource inventory synced 12 min ago',
  },
  latency_ms: 180,
  token_count: 450,
  estimated_cost_usd: '0.00112',
  created_at: '2026-09-26T13:42:00Z',
};

const mockAuditRecord: AIInteractionDetailResponse = {
  id: 'int-spend-001',
  organization_id: 'org-demo-01',
  session_id: 'sess-001',
  question: 'Why did monthly spend increase?',
  question_category: 'SPEND_CHANGE',
  scope_type: 'DASHBOARD',
  provider: 'mock',
  model: 'mock-deterministic',
  prompt_version: 'v9.2.0',
  context_version: 'v9.1.4',
  evidence_hash: 'e8f14b39a7c2d91f84b602e1c7593da502938475618293a4b5c6d7e8f9012345',
  evidence_ids: ['ev-ce-ec2-01', 'ev-cw-p95-cpu'],
  response_status: 'COMPLETED',
  latency_ms: 312,
  input_token_count: 640,
  output_token_count: 250,
  estimated_cost_usd: '0.00224',
  evidence_count: 14,
  created_at: '2026-09-26T13:40:00Z',
  sanitized_evidence_preview: {
    scope_type: 'DASHBOARD',
    evidence_count: 14,
    items_sample: [
      {
        id: 'ev-ce-ec2-01',
        type: 'SPEND_TOTAL',
        epistemic_class: 'OBSERVED',
        statement: 'Observed monthly EC2 spend increased by ₹2,14,000 (+18.7%).',
        value: 214000,
        unit: 'INR',
        source: 'AWS Cost Explorer',
      },
      {
        id: 'ev-cw-p95-cpu',
        type: 'METRIC_P95',
        epistemic_class: 'OBSERVED',
        statement: 'CPU 95th percentile utilization over 14 days is 11.2%.',
        value: 11.2,
        unit: '%',
        source: 'CloudWatch Telemetry',
      },
    ],
  },
};

const mockAIStatusOnline: AIStatusResponse = {
  ai_enabled: true,
  provider: 'mock',
  model: 'mock-deterministic',
  max_context_tokens: 8192,
  max_output_tokens: 2048,
  rate_limit_per_minute: 60,
  system_version: 'v9.2.0',
  prompt_version: 'v9.2.0',
  is_offline_capable: true,
};

const mockAIStatusDisabled: AIStatusResponse = {
  ai_enabled: false,
  provider: 'disabled',
  model: 'none',
  max_context_tokens: 0,
  max_output_tokens: 0,
  rate_limit_per_minute: 0,
  system_version: 'v9.2.0',
  prompt_version: 'v9.2.0',
  is_offline_capable: true,
};

describe('Milestone 8: Ask Atlas Interrogation Layer & Research Console', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getAIStatus as any).mockResolvedValue(mockAIStatusOnline);
    (api.getAIInteraction as any).mockResolvedValue(mockAuditRecord);
    (api.askAtlas as any).mockResolvedValue(mockSpendResponse);
  });

  // Scenario A: Spend question returns grounded financial evidence
  it('Scenario A: submits spend inquiry and renders grounded financial evidence with numeric claims', async () => {
    render(
      <MemoryRouter>
        <AskAtlasDrawer isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );

    // Initial console renders welcome & suggestions
    expect(screen.getByText('ASK ATLAS')).toBeInTheDocument();
    expect(screen.getByText('Technology Financial Economics Research Console')).toBeInTheDocument();

    const textarea = screen.getByPlaceholderText(/Ask about cost deltas/i);
    fireEvent.change(textarea, { target: { value: 'Why did monthly spend increase?' } });

    const submitBtn = screen.getByRole('button', { name: /Investigate/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.askAtlas).toHaveBeenCalledWith({
        question: 'Why did monthly spend increase?',
        scope_type: 'DASHBOARD',
        scope_id: undefined,
        session_id: undefined,
      });
    });

    // Validates Executive Summary rendered
    await waitFor(() => {
      expect(screen.getByText(/EC2 compute spend increased by ₹2,14,000/i)).toBeInTheDocument();
    });

    // Validates Guardrail 2: Strict tolerance wording (NEVER "99% accurate")
    expect(screen.getByText(/NUMERIC CLAIMS VERIFIED · Tolerance: ±1.0%/i)).toBeInTheDocument();
    expect(screen.queryByText(/99% accurate/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/confidence: 99%/i)).not.toBeInTheDocument();

    // Validates verified numeric claim badge
    expect(screen.getAllByText(/₹(214,000|2,14,000)/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/(ev-ce-ec2-01)/i)).toBeInTheDocument();

    // Validates interactive citation pill rendered
    expect(screen.getAllByText('[E1]').length).toBeGreaterThanOrEqual(1);
  });

  // Scenario B: Resource question retrieves telemetry and capacity headroom
  it('Scenario B: contextual resource inquiry retrieves telemetry and capacity headroom', async () => {
    render(
      <MemoryRouter>
        <AskAtlasDrawer
          isOpen={true}
          onClose={vi.fn()}
          context={{
            scopeType: 'RESOURCE',
            resourceId: 'i-0eks-node-m5-4x-01',
            resourceName: 'prod-api-worker-01',
            scopeLabel: 'Resource: prod-api-worker-01',
          }}
        />
      </MemoryRouter>
    );

    // Context banner renders active entity
    expect(screen.getByText(/ACTIVE CONTEXT:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/RESOURCE/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/prod-api-worker-01/i)[0]).toBeInTheDocument();

    // Textarea has context-aware placeholder
    expect(
      screen.getByPlaceholderText(/Ask about Resource: prod-api-worker-01/i)
    ).toBeInTheDocument();
  });

  // Scenario C: Insufficient telemetry degrades gracefully without speculating
  it('Scenario C: displays DATA NOT AVAILABLE and explicit limitations when telemetry is missing', async () => {
    (api.askAtlas as any).mockResolvedValue(mockInsufficientTelemetryResponse);

    render(
      <MemoryRouter>
        <AIAnswerView response={mockInsufficientTelemetryResponse} />
      </MemoryRouter>
    );

    // Epistemic badge explicitly renders DATA NOT AVAILABLE
    expect(screen.getByText('DATA NOT AVAILABLE')).toBeInTheDocument();

    // Limitations callout explains missing CloudWatch agent without fabricating 0%
    expect(
      screen.getByText(/Memory telemetry coverage is 0% \(CloudWatch agent missing\)/i)
    ).toBeInTheDocument();
  });

  // Scenario D & Guardrail 2: Strict tolerance wording in AIAnswerView
  it('Scenario D: strictly adheres to NUMERIC CLAIMS VERIFIED wording avoiding confidence score illusions', () => {
    render(
      <MemoryRouter>
        <AIAnswerView response={mockSpendResponse} />
      </MemoryRouter>
    );

    const seal = screen.getByText(/NUMERIC CLAIMS VERIFIED · Tolerance: ±1.0%/i);
    expect(seal).toBeInTheDocument();
    expect(screen.queryByText(/99% confidence/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/99% accurate/i)).not.toBeInTheDocument();
  });

  // Scenario G: AI status flyout distinguishes AI availability from Atlas availability (Guardrails 8 & 9)
  it('Scenario G: distinguishes AI availability from Atlas availability when AI is disabled', async () => {
    (api.getAIStatus as any).mockResolvedValue(mockAIStatusDisabled);

    render(
      <MemoryRouter>
        <AIStatusFlyout />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AI: DISABLED')).toBeInTheDocument();
    });

    // Open flyout
    fireEvent.click(screen.getByRole('button', { name: /AI: DISABLED/i }));

    // Confirms deterministic foundation guarantees remain fully operational
    expect(screen.getByText('Deterministic Foundation Guarantees')).toBeInTheDocument();
    expect(screen.getByText('Spend Intelligence: Operational')).toBeInTheDocument();
    expect(screen.getByText('Anomaly & Driver Tracing: Operational')).toBeInTheDocument();
    expect(screen.getByText('Optimization Portfolio: Operational')).toBeInTheDocument();
    expect(screen.getByText('Future-State Scenarios: Operational')).toBeInTheDocument();
  });

  // Scenario H: Multi-turn conversational session continuity
  it('Scenario H: preserves session continuity and passes session_id on follow-up inquiries', async () => {
    render(
      <MemoryRouter>
        <AskAtlasDrawer isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );

    const textarea = screen.getByPlaceholderText(/Ask about cost deltas/i);
    fireEvent.change(textarea, { target: { value: 'Why did monthly spend increase?' } });
    fireEvent.click(screen.getByRole('button', { name: /Investigate/i }));

    await waitFor(() => {
      expect(screen.getByText('Q1')).toBeInTheDocument();
    });

    // Follow-up question
    fireEvent.change(textarea, { target: { value: 'What about that production compute cluster?' } });
    fireEvent.click(screen.getByRole('button', { name: /Investigate/i }));

    await waitFor(() => {
      // Confirms session_id was passed to backend for disambiguation
      expect(api.askAtlas).toHaveBeenLastCalledWith(
        expect.objectContaining({
          session_id: 'sess-001',
          question: 'What about that production compute cluster?',
        })
      );
    });

    // Both Q1 and Q2 are preserved in thread
    expect(screen.getByText('Q1')).toBeInTheDocument();
    expect(screen.getByText('Q2')).toBeInTheDocument();

    // Clicking New Inquiry resets thread
    const newInquiryBtn = screen.getByRole('button', { name: /New Inquiry/i });
    fireEvent.click(newInquiryBtn);
    expect(screen.queryByText('Q1')).not.toBeInTheDocument();
  });

  // Scenario I: Citation integrity with 3 distinct fallback states (Guardrail 4)
  it('Scenario I: resolves citations strictly against backend package with 3 fallback states', () => {
    const { rerender } = render(
      <MemoryRouter>
        {/* State A: Verified evidence */}
        <InteractiveEvidenceCitation
          evidenceId="ev-ce-ec2-01"
          index={0}
          response={mockSpendResponse}
        />
      </MemoryRouter>
    );

    const btnA = screen.getByRole('button', { name: /\[E1\]/i });
    expect(btnA).toBeInTheDocument();
    fireEvent.mouseEnter(btnA);
    expect(screen.getByText('AWS Cost Explorer Invoiced Item')).toBeInTheDocument();
    expect(screen.getByText(/INSPECT IN ATLAS WORKSPACE/i)).toBeInTheDocument();

    // State B: Valid evidence without dedicated navigation
    rerender(
      <MemoryRouter>
        <InteractiveEvidenceCitation
          evidenceId="ev-raw-billing-01"
          index={1}
          response={mockSpendResponse}
        />
      </MemoryRouter>
    );

    const btnB = screen.getByRole('button', { name: /\[E2\]/i });
    fireEvent.mouseEnter(btnB);
    expect(screen.getByText(/SOURCE AVAILABLE · NAV UNAVAILABLE/i)).toBeInTheDocument();

    // State C: Missing evidence fallback
    rerender(
      <MemoryRouter>
        <InteractiveEvidenceCitation
          evidenceId="ev-phantom-citation-999"
          index={2}
          response={mockSpendResponse}
        />
      </MemoryRouter>
    );

    const btnC = screen.getByRole('button', { name: /\[E3\]/i });
    fireEvent.mouseEnter(btnC);
    expect(screen.getAllByText('NOT_AVAILABLE')[0]).toBeInTheDocument();
    expect(screen.getByText(/Atlas could not verify this citation against the evidence package/i)).toBeInTheDocument();
  });

  // Scenario J: Provenance modal displays SHA-256 digest, tokens, and sanitized preview (Guardrail 3)
  it('Scenario J: opens AIProvenanceModal displaying cryptographic digest, accounting, and sanitized preview', async () => {
    render(
      <MemoryRouter>
        <AIProvenanceModal
          interactionId="int-spend-001"
          isOpen={true}
          onClose={vi.fn()}
        />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('AI PROVENANCE & AUDIT LOG')).toBeInTheDocument();
    });

    // Displays full SHA-256 digest
    expect(
      screen.getByText('e8f14b39a7c2d91f84b602e1c7593da502938475618293a4b5c6d7e8f9012345')
    ).toBeInTheDocument();

    // Displays execution metrics
    expect(screen.getByText('312 ms')).toBeInTheDocument();
    expect(screen.getByText('890')).toBeInTheDocument();
    expect(screen.getByText('$0.00224')).toBeInTheDocument();

    // Switch to Sanitized Evidence Preview tab
    const previewTab = screen.getByRole('button', { name: /SANITIZED EVIDENCE PREVIEW/i });
    fireEvent.click(previewTab);

    // Displays sanitized evidence items sample from backend
    expect(screen.getByText('ev-ce-ec2-01')).toBeInTheDocument();
    expect(screen.getByText('ev-cw-p95-cpu')).toBeInTheDocument();
  });

  // Scenario K: Strict read-only boundary (ZERO mutation controls)
  it('Scenario K: enforces strict read-only boundary with zero mutation controls in Ask Atlas', () => {
    render(
      <MemoryRouter>
        <AIAnswerView response={mockSpendResponse} />
      </MemoryRouter>
    );

    const prohibitedMutations = [
      /apply/i,
      /execute/i,
      /deploy/i,
      /modify/i,
      /scale/i,
      /delete/i,
      /stop/i,
      /terminate/i,
      /provision/i,
    ];

    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => {
      const text = btn.textContent || '';
      prohibitedMutations.forEach((regex) => {
        expect(text).not.toMatch(regex);
      });
    });
  });
});
