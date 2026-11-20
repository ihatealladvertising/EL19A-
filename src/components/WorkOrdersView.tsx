import React, { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import type { WorkOrderSummary } from '../types';
import { MarkdownView } from './MarkdownView';

interface WorkOrdersViewProps {
  selectedWoId: string | null;
  onSelectWo: (woId: string) => void;
  onJumpHex: (addr: string) => void;
}

export const WorkOrdersView: React.FC<WorkOrdersViewProps> = ({
  selectedWoId,
  onSelectWo,
  onJumpHex,
}) => {
  const [items, setItems] = useState<WorkOrderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETE' | 'PARTIAL'>('ALL');
  const [detailContent, setDetailContent] = useState<string>('');
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      const params = new URLSearchParams({ status: statusFilter });
      if (query.trim()) params.set('q', query.trim());
      fetch(`/api/work-orders?${params.toString()}`)
        .then((r) => r.json())
        .then((d) => {
          const list: WorkOrderSummary[] = d.items || [];
          setItems(list);
          setLoading(false);
          if (!selectedWoId && list.length > 0) {
            onSelectWo(list[0].id);
          }
        })
        .catch(() => setLoading(false));
    }, 150);
    return () => clearTimeout(timer);
  }, [query, statusFilter]);

  useEffect(() => {
    if (!selectedWoId) return;
    let active = true;
    setDetailLoading(true);
    fetch(`/api/work-orders/${encodeURIComponent(selectedWoId)}`)
      .then((r) => r.json())
      .then((d) => {
        if (!active) return;
        setDetailContent(d.content || '');
        setDetailLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setDetailLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedWoId]);

  const activeSummary = items.find((w) => w.id === selectedWoId) || null;

  return (
    <div className="space-y-4">
      {/* Filter Toolbar */}
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          {(['ALL', 'COMPLETE', 'PARTIAL'] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                statusFilter === st
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {st === 'ALL' ? 'All Work Orders' : st === 'COMPLETE' ? 'Complete / Closed' : 'Partial / Parked'}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search WO ID, topic, or address (e.g. CD56)..."
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-3 pl-9 text-xs text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:bg-white focus:outline-none"
          />
        </div>
      </div>

      {/* Master-Detail Split */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="lg:col-span-4 rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-2.5 text-xs font-semibold text-slate-600 tabular-nums">
            {loading ? 'Loading...' : `${items.length} work orders`}
          </div>
          <div className="max-h-[680px] overflow-y-auto divide-y divide-slate-100">
            {items.map((wo) => {
              const active = wo.id === selectedWoId;
              return (
                <button
                  key={wo.id}
                  type="button"
                  onClick={() => onSelectWo(wo.id)}
                  className={`w-full px-4 py-3 text-left transition-colors ${
                    active ? 'bg-sky-50/70' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-semibold text-sky-700">{wo.id}</span>
                    <span className="text-[11px] text-slate-500 truncate">
                      {wo.status.split('—')[0].trim()}
                    </span>
                  </div>
                  <div className="mt-1 text-sm font-medium text-slate-900 line-clamp-1">
                    {wo.title.replace(/^WO\d+\s*[—-]\s*/i, '')}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500 line-clamp-2">{wo.objective}</div>
                </button>
              );
            })}
            {!loading && items.length === 0 && (
              <div className="p-6 text-center text-xs text-slate-500">
                No work orders match "{query}".
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-8 rounded-lg border border-slate-200 bg-white p-6">
          {detailLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-6 w-2/3 rounded bg-slate-100" />
              <div className="h-4 w-full rounded bg-slate-100" />
              <div className="h-4 w-5/6 rounded bg-slate-100" />
            </div>
          ) : detailContent ? (
            <div>
              {activeSummary?.addresses.length ? (
                <div className="mb-4 flex flex-wrap items-center gap-2 border-b border-slate-100 pb-3 text-xs text-slate-500">
                  <span>Referenced addresses:</span>
                  {activeSummary.addresses.slice(0, 8).map((addr) => {
                    const isRom = addr.startsWith('0X') && parseInt(addr, 16) < 0x100000;
                    return isRom ? (
                      <button
                        key={addr}
                        type="button"
                        onClick={() => onJumpHex(addr)}
                        className="font-mono text-sky-700 underline decoration-sky-300 underline-offset-2 hover:text-sky-900"
                      >
                        {addr}
                      </button>
                    ) : (
                      <span key={addr} className="font-mono text-slate-600">
                        {addr}
                      </span>
                    );
                  })}
                </div>
              ) : null}
              <MarkdownView content={detailContent} onSelectAddress={onJumpHex} />
            </div>
          ) : (
            <div className="py-12 text-center text-sm text-slate-500">
              Select a work order to view its audit trail and evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
