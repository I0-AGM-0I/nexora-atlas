import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Server,
  Search,
  Database,
  HardDrive,
  Cpu,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { TableSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { useAskAtlas } from '../lib/AskAtlasContext';
import { api } from '../lib/api';
import { formatCurrency } from '../lib/format';
import { ResourceListItem, ResourceListResponse } from '../types/api';

export const ResourcesPage: React.FC = () => {
  const { openAskAtlas } = useAskAtlas();
  const [data, setData] = useState<ResourceListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [accountId, setAccountId] = useState('');
  const [serviceName, setServiceName] = useState('');
  const [region, setRegion] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const loadResources = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getResources({
        search: appliedSearch.trim() || undefined,
        account_id: accountId || undefined,
        service_name: serviceName || undefined,
        region: region || undefined,
        status: status || undefined,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to load resources');
    } finally {
      setLoading(false);
    }
  }, [appliedSearch, accountId, serviceName, region, status, page]);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setAppliedSearch(search);
  };



  const getServiceIcon = (service: string) => {
    switch (service.toLowerCase()) {
      case 'amazonec2':
        return <Cpu className="w-4 h-4 text-amber-400" />;
      case 'amazonrds':
        return <Database className="w-4 h-4 text-blue-400" />;
      case 'amazons3':
        return <HardDrive className="w-4 h-4 text-emerald-400" />;
      default:
        return <Server className="w-4 h-4 text-atlas-primary" />;
    }
  };

  const getStatusBadge = (resStatus: string) => {
    const s = resStatus.toLowerCase();
    if (s === 'running' || s === 'active' || s === 'available') {
      return <Badge variant="success">{resStatus}</Badge>;
    }
    if (s === 'stopped' || s === 'inactive') {
      return <Badge variant="default">{resStatus}</Badge>;
    }
    if (s === 'deleting' || s === 'terminated') {
      return <Badge variant="critical">{resStatus}</Badge>;
    }
    return <Badge variant="info">{resStatus}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold tracking-tight text-atlas-text">Resource Inventory</h1>
            <Badge variant="info">Discovered Cloud Assets</Badge>
          </div>
          <p className="text-xs text-atlas-secondary">
            Discovered cloud infrastructure assets across compute, database, storage, and networking with 30-day attributed costs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              openAskAtlas({
                scopeType: 'RESOURCE',
                scopeLabel: 'Resource Inventory',
                initialQuestion: 'What are the highest-cost unattached or under-utilized resources in our cloud inventory?',
              })
            }
            className="flex items-center gap-1.5 text-xs text-atlas-primary border-atlas-primary/40 hover:bg-atlas-primary/10"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Atlas about Inventory</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-atlas-surface/50 border-atlas-border space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-atlas-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search resources by name, native ID, or type..."
              className="w-full bg-atlas-elevated border border-atlas-border rounded-lg pl-9 pr-4 py-1.5 text-xs text-atlas-text placeholder-atlas-muted focus:outline-none focus:ring-1 focus:ring-atlas-primary"
            />
          </div>
          <Button type="submit" variant="primary" size="sm">
            Search
          </Button>
        </form>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-1">
          {/* Account Filter */}
          <div>
            <label className="text-[11px] font-medium text-atlas-muted mb-1 block">Account</label>
            <select
              value={accountId}
              onChange={(e) => {
                setAccountId(e.target.value);
                setPage(1);
              }}
              className="w-full bg-atlas-elevated border border-atlas-border text-atlas-text text-xs rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-atlas-primary"
            >
              <option value="">All Accounts</option>
              <option value="Production Core">Production Core</option>
              <option value="Staging Workloads">Staging Workloads</option>
              <option value="Development Sandbox">Development Sandbox</option>
            </select>
          </div>

          {/* Service Filter */}
          <div>
            <label className="text-[11px] font-medium text-atlas-muted mb-1 block">Service</label>
            <select
              value={serviceName}
              onChange={(e) => {
                setServiceName(e.target.value);
                setPage(1);
              }}
              className="w-full bg-atlas-elevated border border-atlas-border text-atlas-text text-xs rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-atlas-primary"
            >
              <option value="">All Services</option>
              <option value="AmazonEC2">AmazonEC2</option>
              <option value="AmazonRDS">AmazonRDS</option>
              <option value="AmazonS3">AmazonS3</option>
              <option value="AmazonElastiCache">AmazonElastiCache</option>
              <option value="AWSDataTransfer">AWSDataTransfer</option>
            </select>
          </div>

          {/* Region Filter */}
          <div>
            <label className="text-[11px] font-medium text-atlas-muted mb-1 block">Region</label>
            <select
              value={region}
              onChange={(e) => {
                setRegion(e.target.value);
                setPage(1);
              }}
              className="w-full bg-atlas-elevated border border-atlas-border text-atlas-text text-xs rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-atlas-primary"
            >
              <option value="">All Regions</option>
              <option value="us-east-1">us-east-1 (N. Virginia)</option>
              <option value="eu-west-1">eu-west-1 (Ireland)</option>
              <option value="ap-south-1">ap-south-1 (Mumbai)</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="text-[11px] font-medium text-atlas-muted mb-1 block">Status</label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full bg-atlas-elevated border border-atlas-border text-atlas-text text-xs rounded px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-atlas-primary"
            >
              <option value="">All Statuses</option>
              <option value="running">running</option>
              <option value="stopped">stopped</option>
              <option value="available">available</option>
              <option value="in-use">in-use</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Content Section */}
      {loading ? (
        <Card className="p-4 bg-atlas-surface/50 border-atlas-border">
          <TableSkeleton rows={8} />
        </Card>
      ) : error ? (
        <ErrorState
          title="Unable to Load Resources"
          message={error}
          onRetry={loadResources}
        />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No Resources Found"
          message="No cloud resources match your current filter and search query."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setAccountId('');
            setServiceName('');
            setRegion('');
            setStatus('');
            setPage(1);
          }}
        />
      ) : (
        <Card className="bg-atlas-surface/50 border-atlas-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-atlas-border bg-atlas-surface/80 text-atlas-muted uppercase text-[10px] tracking-wider font-semibold">
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-3">Service & Type</th>
                  <th className="py-3 px-3">Account</th>
                  <th className="py-3 px-3">Region</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-4 text-right">30-Day Spend</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-atlas-border/50 font-mono">
                {data.items.map((res: ResourceListItem) => (
                  <tr
                    key={res.id}
                    className="hover:bg-atlas-elevated/40 transition-colors group"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded bg-atlas-elevated border border-atlas-border flex-shrink-0">
                          {getServiceIcon(res.service_name)}
                        </div>
                        <div className="min-w-0">
                          <Link
                            to={`/resources/${res.id}`}
                            className="font-sans font-medium text-atlas-text text-xs truncate max-w-xs hover:text-atlas-primary transition-colors block"
                          >
                            {res.name}
                          </Link>
                          <div className="text-[11px] text-atlas-muted truncate">
                            {res.native_id}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <div className="text-atlas-text font-sans font-medium text-xs">
                        {res.service_name}
                      </div>
                      <div className="text-[11px] text-atlas-muted">
                        {res.resource_type}
                      </div>
                    </td>

                    <td className="py-3 px-3 font-sans text-atlas-secondary">
                      {res.account_name}
                    </td>

                    <td className="py-3 px-3 text-atlas-muted text-[11px]">
                      {res.region_code}
                    </td>

                    <td className="py-3 px-3">
                      {getStatusBadge(res.status)}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <span className="font-bold text-atlas-text">
                        {res.cost_30d !== null && res.cost_30d !== undefined
                          ? formatCurrency(res.cost_30d)
                          : '₹0.00'}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2.5 font-sans text-[11px]">
                        <Link
                          to={`/resources/${res.id}`}
                          className="text-atlas-primary hover:underline font-medium"
                        >
                          Telemetry
                        </Link>
                        <span className="text-atlas-border">•</span>
                        <Link
                          to={`/spend?account_id=${encodeURIComponent(res.account_name)}&service_name=${encodeURIComponent(res.service_name)}`}
                          className="inline-flex items-center gap-0.5 text-atlas-muted hover:text-atlas-text"
                        >
                          <span>Spend</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div className="p-3.5 border-t border-atlas-border bg-atlas-surface/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-atlas-muted">
            <div>
              Showing <span className="font-mono text-atlas-text">{((page - 1) * pageSize) + 1}</span> to{' '}
              <span className="font-mono text-atlas-text">{Math.min(page * pageSize, data.total)}</span> of{' '}
              <span className="font-mono text-atlas-text">{data.total}</span> resources
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                icon={<ChevronLeft className="w-3.5 h-3.5" />}
              >
                Previous
              </Button>

              <span className="font-mono px-2 text-atlas-text text-xs">
                Page {page} of {data.total_pages || 1}
              </span>

              <Button
                variant="outline"
                size="sm"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                icon={<ChevronRight className="w-3.5 h-3.5" />}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
