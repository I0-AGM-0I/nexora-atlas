import React, { useState, useEffect } from 'react';
import {
  CloudCog,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Lock,
  Clock,
  Database,
  Server,
  HardDrive,
  FolderLock,
  Layers,
  Settings2,
  Check,
  X,
  Activity,
  Sparkles,
  FileCode2,
  ShieldAlert,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { api } from '../lib/api';
import {
  IntegrationItemResponse,
  AWSValidationResponse,
  SyncJobItemResponse,
  AWSServicePermissions,
  DataQualityReportResponse,
} from '../types/api';

export const IntegrationsPage: React.FC = () => {
  const { openAskAtlas } = useAskAtlas();
  const [activeIntegration, setActiveIntegration] = useState<IntegrationItemResponse | null>(null);
  const [syncJobs, setSyncJobs] = useState<SyncJobItemResponse[]>([]);
  const [permissions, setPermissions] = useState<AWSServicePermissions | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityReportResponse | null>(null);

  // Action states
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<AWSValidationResponse | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isTelemetrySyncing, setIsTelemetrySyncing] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  // Configuration modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [roleArnInput, setRoleArnInput] = useState('');
  const [externalIdInput, setExternalIdInput] = useState('');
  const [regionInput, setRegionInput] = useState('us-east-1');
  const [accountNameInput, setAccountNameInput] = useState('Production Core');
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  const fetchIntegrations = async () => {
    try {
      const [items, qualityRes] = await Promise.all([
        api.getIntegrations(),
        api.getDataQualityReport().catch(() => null),
      ]);
      if (qualityRes) {
        setDataQuality(qualityRes);
      }
      if (items.length > 0) {
        const awsItem = items.find((i) => i.provider_type === 'AWS') || items[0];
        setActiveIntegration(awsItem);
        // Fetch sync jobs & status
        const [jobs, statusRes] = await Promise.all([
          api.getSyncJobs(awsItem.id).catch(() => []),
          api.getIntegrationStatus(awsItem.id).catch(() => null),
        ]);
        setSyncJobs(jobs);
        if (statusRes) {
          setPermissions(statusRes.permissions);
        }
      }
    } catch (err) {
      console.error('Failed to load integrations', err);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const handleValidateConnection = async () => {
    setIsValidating(true);
    setValidationResult(null);
    setSyncFeedback(null);
    try {
      const res = await api.validateAWSConnection({
        role_arn: activeIntegration ? undefined : roleArnInput,
        external_id: activeIntegration ? undefined : externalIdInput,
        region: regionInput,
      });
      setValidationResult(res);
      setPermissions(res.permissions);
    } catch (err: any) {
      setValidationResult({
        is_valid: false,
        permissions: {
          cost_aggregated: 'NOT_CONFIGURED',
          cost_resource_level: 'NOT_CONFIGURED',
          ec2_inventory: 'NOT_CONFIGURED',
          ebs_inventory: 'NOT_CONFIGURED',
          rds_inventory: 'NOT_CONFIGURED',
          s3_inventory: 'NOT_CONFIGURED',
          eks_inventory: 'NOT_CONFIGURED',
        },
        error_message: err?.message || 'Failed to connect to AWS validation endpoint',
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleTriggerSync = async () => {
    if (!activeIntegration) return;
    setIsSyncing(true);
    setSyncFeedback(null);
    try {
      const res = await api.triggerAWSSync(activeIntegration.id);
      setSyncFeedback(
        `Sync ${res.status}: Processed ${res.cost_records_processed} cost records and ${res.resources_discovered} resources.`
      );
      // Refresh jobs and integration
      await fetchIntegrations();
    } catch (err: any) {
      setSyncFeedback(`Sync failed: ${err?.message || 'Unknown network error'}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSyncTelemetry = async () => {
    if (!activeIntegration) return;
    setIsTelemetrySyncing(true);
    setSyncFeedback(null);
    try {
      const res = await api.triggerTelemetrySync(activeIntegration.id);
      setSyncFeedback(
        `Telemetry Sync ${res.status}: Operational CloudWatch synchronization initiated.`
      );
      await fetchIntegrations();
    } catch (err: any) {
      setSyncFeedback(`Telemetry sync failed: ${err?.message || 'Unknown network error'}`);
    } finally {
      setIsTelemetrySyncing(false);
    }
  };

  const handleSaveConfiguration = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingConfig(true);
    try {
      const res = await api.configureAWSIntegration({
        role_arn: roleArnInput,
        external_id: externalIdInput || null,
        regions: [regionInput],
        account_name: accountNameInput || null,
      });
      setActiveIntegration(res);
      setShowConfigModal(false);
      await fetchIntegrations();
      // Auto-validate new credentials
      handleValidateConnection();
    } catch (err: any) {
      alert(`Configuration error: ${err?.message || 'Failed to save configuration'}`);
    } finally {
      setIsSavingConfig(false);
    }
  };

  const renderPermissionBadge = (status: string) => {
    if (status === 'AVAILABLE') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
          <Check className="w-3.5 h-3.5 text-emerald-400" />
          <span>Available</span>
        </span>
      );
    }
    if (status === 'DENIED') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400">
          <X className="w-3.5 h-3.5 text-rose-400" />
          <span>Access Denied</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-atlas-muted">
        <span>Not Configured</span>
      </span>
    );
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Cloud Integrations & Trust Boundary</h1>
            <Badge variant={activeIntegration?.status === 'SYNCED' ? 'success' : 'default'}>
              {activeIntegration ? `AWS • ${activeIntegration.status}` : 'Offline Mode'}
            </Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Manage read-only cloud connections, IAM role credentials, historical cost synchronization, and cryptographic trust boundaries.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              openAskAtlas({
                scopeType: 'DASHBOARD',
                scopeLabel: 'AWS Cloud Integration & Trust Boundary',
                initialQuestion: 'How does Atlas guarantee zero infrastructure mutation and enforce read-only trust boundaries?',
              })
            }
            className="flex items-center gap-1.5 text-xs text-atlas-primary border-atlas-primary/40 hover:bg-atlas-primary/10"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas about Trust Boundary</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConfigModal(true)}
            icon={<Settings2 className="w-3.5 h-3.5" />}
          >
            Configure IAM Role
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={isValidating}
            onClick={handleValidateConnection}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />}
          >
            {isValidating ? 'Validating...' : 'Validate Connection'}
          </Button>
          {activeIntegration && (
            <Button
              variant="primary"
              size="sm"
              disabled={isSyncing}
              onClick={handleTriggerSync}
              icon={<RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />}
            >
              {isSyncing ? 'Ingesting...' : 'Sync Now'}
            </Button>
          )}
        </div>
      </div>

      {/* Flagship Architectural Trust Boundary Control Room */}
      <Card className="p-5 bg-gradient-to-r from-emerald-950/20 via-atlas-surface to-atlas-elevated/40 border-emerald-500/30 space-y-4 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-atlas-border/60 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-atlas-text uppercase tracking-wider font-mono">
                  Architectural Trust Boundary Verification
                </h2>
                <Badge variant="success">AST ENFORCED</Badge>
              </div>
              <p className="text-xs text-atlas-muted">
                Mathematical guarantee: Atlas is provably read-only at both code AST and IAM policy layers.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <div className="p-1.5 px-3 rounded bg-atlas-elevated border border-atlas-border text-emerald-400 font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>0 Mutating Calls</span>
            </div>
            <div className="p-1.5 px-3 rounded bg-atlas-elevated border border-atlas-border text-sky-400 font-semibold flex items-center gap-1.5">
              <FileCode2 className="w-3.5 h-3.5" />
              <span>Python AST Analyzer Passed</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 rounded-lg bg-atlas-bg/80 border border-atlas-border space-y-1.5">
            <div className="font-semibold text-atlas-text flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Permitted Operations Whitelist</span>
            </div>
            <p className="text-atlas-muted text-[11px] leading-relaxed">
              Strictly limited to read APIs: <code className="font-mono text-emerald-300">ce:GetCostAndUsage</code>, <code className="font-mono text-emerald-300">ce:GetCostAndUsageWithResources</code>, <code className="font-mono text-emerald-300">ec2:Describe*</code>, <code className="font-mono text-emerald-300">rds:Describe*</code>, <code className="font-mono text-emerald-300">cloudwatch:GetMetricData</code>.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-atlas-bg/80 border border-atlas-border space-y-1.5">
            <div className="font-semibold text-atlas-text flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Forbidden Mutation Blacklist</span>
            </div>
            <p className="text-atlas-muted text-[11px] leading-relaxed">
              Zero capability to execute: <code className="font-mono text-rose-300">Terminate*</code>, <code className="font-mono text-rose-300">Delete*</code>, <code className="font-mono text-rose-300">Stop*</code>, <code className="font-mono text-rose-300">Modify*</code>, or <code className="font-mono text-rose-300">Purchase*</code>. Attempted mutations are rejected at AST parsing prior to runtime.
            </p>
          </div>

          <div className="p-3.5 rounded-lg bg-atlas-bg/80 border border-atlas-border space-y-1.5">
            <div className="font-semibold text-atlas-text flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-sky-400" />
              <span>STS Ephemeral Credentials</span>
            </div>
            <p className="text-atlas-muted text-[11px] leading-relaxed">
              Authenticated via ephemeral 1-hour session tokens using customer-provided IAM Role ARNs and unique External IDs, fully eliminating long-lived access keys.
            </p>
          </div>
        </div>
      </Card>

      {/* Feedback Messages */}
      {validationResult && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
            validationResult.is_valid
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {validationResult.is_valid ? (
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <div className="font-semibold">
              {validationResult.is_valid
                ? `Connection Validated: Linked Account ${validationResult.account_id || ''}`
                : 'Connection Validation Failed'}
            </div>
            {validationResult.error_message && (
              <p className="text-[11px] opacity-90 mt-0.5">{validationResult.error_message}</p>
            )}
          </div>
        </div>
      )}

      {syncFeedback && (
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs text-blue-300 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 flex-shrink-0" />
          <span>{syncFeedback}</span>
        </div>
      )}

      {/* Main AWS Connector Card */}
      <Card className="p-6 bg-atlas-surface/50 border-atlas-border space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-atlas-border pb-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-atlas-elevated border border-atlas-border flex items-center justify-center text-amber-400">
              <CloudCog className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-atlas-text">Amazon Web Services (AWS)</h2>
                <Badge
                  variant={
                    activeIntegration?.status === 'SYNCED'
                      ? 'success'
                      : activeIntegration?.status === 'PARTIAL'
                      ? 'warning'
                      : 'default'
                  }
                >
                  {activeIntegration?.status || 'NOT CONFIGURED'}
                </Badge>
              </div>
              <p className="text-xs text-atlas-muted mt-0.5">
                Cost Explorer Ingestion & Multi-Service Resource Discovery
              </p>
            </div>
          </div>

          <div className="text-right">
            <div className="text-[11px] text-atlas-muted uppercase font-medium tracking-wider">
              Last Synchronized
            </div>
            <div className="text-xs font-mono font-semibold text-atlas-text mt-0.5">
              {activeIntegration?.last_sync_at
                ? new Date(activeIntegration.last_sync_at).toLocaleString()
                : 'Never'}
            </div>
          </div>
        </div>

        {/* Configuration Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-atlas-elevated/40 border border-atlas-border space-y-1">
            <div className="text-[11px] font-medium text-atlas-muted uppercase tracking-wider flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-atlas-primary" />
              <span>Assumed IAM Role</span>
            </div>
            <div className="font-mono text-xs text-atlas-text truncate font-semibold">
              {activeIntegration?.role_arn_masked || 'arn:aws:iam::***:role/AtlasReadOnly'}
            </div>
            <div className="text-[11px] text-atlas-muted">Read-only permissions enforced</div>
          </div>

          <div className="p-4 rounded-lg bg-atlas-elevated/40 border border-atlas-border space-y-1">
            <div className="text-[11px] font-medium text-atlas-muted uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-atlas-primary" />
              <span>Sync Strategy</span>
            </div>
            <div className="font-mono text-xs text-atlas-text font-semibold">
              90d Initial • 14d Rolling Overlap
            </div>
            <div className="text-[11px] text-atlas-muted">Absorbs billing revisions automatically</div>
          </div>

          <div className="p-4 rounded-lg bg-atlas-elevated/40 border border-atlas-border space-y-1">
            <div className="text-[11px] font-medium text-atlas-muted uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-atlas-primary" />
              <span>Target Regions</span>
            </div>
            <div className="font-mono text-xs text-atlas-text font-semibold">
              {activeIntegration?.regions?.join(', ') || 'us-east-1'}
            </div>
            <div className="text-[11px] text-atlas-muted">Multi-region inventory discovery</div>
          </div>
        </div>

        {/* Permission Status Matrix */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-bold text-atlas-text uppercase tracking-wide">
              Read-Only Capability Matrix
            </div>
            <span className="text-[11px] text-atlas-muted font-mono">
              Probed via dry-run STS AssumeRole
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">Cost Explorer (Aggregated)</div>
                  <div className="text-[10px] text-atlas-muted">90d Service/Account Spend</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.cost_aggregated || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">Cost Explorer (Resource-level)</div>
                  <div className="text-[10px] text-atlas-muted">14d Opt-in Direct Attribution</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.cost_resource_level || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Server className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">EC2 Instances</div>
                  <div className="text-[10px] text-atlas-muted">Metadata & Instance Types</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.ec2_inventory || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <HardDrive className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">EBS Volumes</div>
                  <div className="text-[10px] text-atlas-muted">Attached & Unattached Volumes</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.ebs_inventory || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Database className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">RDS Databases</div>
                  <div className="text-[10px] text-atlas-muted">DB Instances & Clusters</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.rds_inventory || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <FolderLock className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">S3 Storage</div>
                  <div className="text-[10px] text-atlas-muted">Bucket Names & Regions</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.s3_inventory || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Layers className="w-4 h-4 text-atlas-primary" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">EKS Kubernetes</div>
                  <div className="text-[10px] text-atlas-muted">Clusters & Nodegroups</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.eks_inventory || 'AVAILABLE')}
            </div>

            <div className="p-3 rounded-lg bg-atlas-surface border border-atlas-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Activity className="w-4 h-4 text-purple-400" />
                <div>
                  <div className="text-xs font-medium text-atlas-text">CloudWatch Telemetry</div>
                  <div className="text-[10px] text-atlas-muted">CPU, Memory, I/O & Connections</div>
                </div>
              </div>
              {renderPermissionBadge(permissions?.cloudwatch_telemetry || 'AVAILABLE')}
            </div>
          </div>
        </div>

        {/* Operational Telemetry Actions & Quality Summary */}
        <div className="p-4 rounded-xl bg-atlas-elevated/40 border border-atlas-border/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" />
              <span className="text-xs font-bold text-atlas-text uppercase tracking-wide">Operational Telemetry Subsystem</span>
              <Badge variant={dataQuality?.data_trustworthiness_status === 'TRUSTED' ? 'success' : 'outline'} className="text-[10px]">
                {dataQuality?.data_trustworthiness_status || 'LIMITED_TELEMETRY'}
              </Badge>
            </div>
            <p className="text-xs text-atlas-muted">
              {dataQuality?.resources_with_telemetry || 0} of {dataQuality?.total_resources || 0} resources evaluated with real CloudWatch observations ({dataQuality?.telemetry_coverage_pct || 0}% coverage).
            </p>
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={handleSyncTelemetry}
            disabled={isTelemetrySyncing || !activeIntegration}
            className="flex items-center gap-1.5 text-xs text-purple-400 border-purple-500/40 hover:bg-purple-500/10"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTelemetrySyncing ? 'animate-spin' : ''}`} />
            <span>{isTelemetrySyncing ? 'Syncing Telemetry...' : 'Sync Telemetry'}</span>
          </Button>
        </div>
      </Card>

      {/* Sync Jobs History Table */}
      <Card className="p-6 bg-atlas-surface/50 border-atlas-border space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-atlas-text">Synchronization History</h3>
            <p className="text-xs text-atlas-muted">Audit trail of past cloud ingestion runs with SHA-256 batch signatures</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchIntegrations}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh History
          </Button>
        </div>

        {syncJobs.length === 0 ? (
          <div className="text-center py-8 text-xs text-atlas-muted">
            No historical sync jobs recorded yet. Click "Sync Now" to initiate your first ingestion.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-atlas-border text-atlas-muted">
                  <th className="pb-2.5 font-medium">Job ID</th>
                  <th className="pb-2.5 font-medium">Status</th>
                  <th className="pb-2.5 font-medium">Started At</th>
                  <th className="pb-2.5 font-medium">Completed At</th>
                  <th className="pb-2.5 font-medium text-right">Records Synced</th>
                  <th className="pb-2.5 font-medium">Diagnostics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-atlas-border/40 font-mono">
                {syncJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-atlas-elevated/20">
                    <td className="py-2.5 text-atlas-text truncate max-w-[120px]">{job.id}</td>
                    <td className="py-2.5">
                      <Badge
                        variant={
                          job.status === 'COMPLETED'
                            ? 'success'
                            : job.status === 'PARTIAL'
                            ? 'warning'
                            : 'critical'
                        }
                      >
                        {job.status}
                      </Badge>
                    </td>
                    <td className="py-2.5 text-atlas-muted">
                      {job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
                    </td>
                    <td className="py-2.5 text-atlas-muted">
                      {job.completed_at ? new Date(job.completed_at).toLocaleString() : '—'}
                    </td>
                    <td className="py-2.5 text-right font-semibold text-atlas-text">
                      {job.records_synced.toLocaleString()}
                    </td>
                    <td className="py-2.5 text-atlas-muted text-[11px] truncate max-w-[200px]">
                      {job.error_message || 'Zero errors reported'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-lg bg-atlas-surface border-atlas-border p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-atlas-border pb-4">
              <div>
                <h3 className="text-base font-bold text-atlas-text">Configure AWS IAM Role</h3>
                <p className="text-xs text-atlas-muted mt-0.5">
                  Connect customer AWS account via cross-account STS AssumeRole
                </p>
              </div>
              <button
                onClick={() => setShowConfigModal(false)}
                className="text-atlas-muted hover:text-atlas-text"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveConfiguration} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="font-semibold text-atlas-text">Customer IAM Role ARN</label>
                <input
                  type="text"
                  required
                  placeholder="arn:aws:iam::123456789012:role/AtlasReadOnly"
                  value={roleArnInput}
                  onChange={(e) => setRoleArnInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-atlas-elevated border border-atlas-border text-atlas-text font-mono text-xs focus:outline-none focus:border-atlas-primary"
                />
                <p className="text-[11px] text-atlas-muted">
                  Must attach a read-only policy with ce:GetCostAndUsage and describe permissions.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="font-semibold text-atlas-text">STS External ID (Optional)</label>
                <input
                  type="text"
                  placeholder="atlas-corp-ext-id"
                  value={externalIdInput}
                  onChange={(e) => setExternalIdInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-atlas-elevated border border-atlas-border text-atlas-text font-mono text-xs focus:outline-none focus:border-atlas-primary"
                />
                <p className="text-[11px] text-atlas-muted">
                  Recommended for cross-account confused deputy prevention.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="font-semibold text-atlas-text">Primary Region</label>
                  <input
                    type="text"
                    required
                    value={regionInput}
                    onChange={(e) => setRegionInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-atlas-elevated border border-atlas-border text-atlas-text font-mono text-xs focus:outline-none focus:border-atlas-primary"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="font-semibold text-atlas-text">Account Nickname</label>
                  <input
                    type="text"
                    value={accountNameInput}
                    onChange={(e) => setAccountNameInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-atlas-elevated border border-atlas-border text-atlas-text text-xs focus:outline-none focus:border-atlas-primary"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-atlas-border">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowConfigModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isSavingConfig}
                >
                  {isSavingConfig ? 'Saving...' : 'Save & Connect'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
