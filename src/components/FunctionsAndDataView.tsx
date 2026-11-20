import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import type { DataInventoryEntry, FunctionEntry } from '../types';

interface FunctionsAndDataViewProps {
  onJumpHex: (addr: string) => void;
}

export const FunctionsAndDataView: React.FC<FunctionsAndDataViewProps> = ({ onJumpHex }) => {
  const [subTab, setSubTab] = useState<'functions' | 'data'>('functions');
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const limit = 75;

  const [funcs, setFuncs] = useState<FunctionEntry[]>([]);
  const [funcTotal, setFuncTotal] = useState(0);
  const [selectedFunc, setSelectedFunc] = useState<FunctionEntry | null>(null);

  const [dataItems, setDataItems] = useState<DataInventoryEntry[]>([]);
  const [dataTotal, setDataTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setOffset(0);
  }, [query, subTab]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(true);
      const endpoint =
        subTab === 'functions'
          ? `/api/functions?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`
          : `/api/data-inventory?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`;
      fetch(endpoint)
        .then((r) => r.json())
        .then((d) => {
          if (subTab === 'functions') {
            setFuncs(d.items || []);
            setFuncTotal(d.total || 0);
            if (!selectedFunc && d.items?.length) {
              setSelectedFunc(d.items[0]);
            }
          } else {
            setDataItems(d.items || []);
            setDataTotal(d.total || 0);
          }
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }, 150);
    return () => clearTimeout(timer);
  }, [subTab, query, offset]);

  const total = subTab === 'functions' ? funcTotal : dataTotal;

  const jumpToFunctionRef = (ref: string) => {
    const addr = ref.includes('@') ? ref.split('@')[1] : ref;
    setQuery(addr);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setSubTab('functions')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              subTab === 'functions'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Function Index (1,581)
          </button>
          <button
            type="button"
            onClick={() => setSubTab('data')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              subTab === 'data'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Data Inventory (29,217)
          </button>
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              subTab === 'functions'
                ? 'Search sub_22E10, 0x403D8, sci_transmit...'
                : 'Search address, FFFF84BA, IVECT1, disasm...'
            }
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-3 pl-9 text-xs text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:bg-white focus:outline-none"
          />
        </div>
      </div>

      {subTab === 'functions' ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-7 rounded-lg border border-slate-200 bg-white overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2.5 text-xs text-slate-600">
              <span className="tabular-nums">
                {loading
                  ? 'Searching...'
                  : `Showing ${Math.min(offset + 1, total)}–${Math.min(offset + limit, total)} of ${total.toLocaleString()} functions`}
              </span>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={offset === 0}
                  onClick={() => setOffset((o) => Math.max(0, o - limit))}
                  className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset((o) => o + limit)}
                  className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="max-h-[640px] overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 border-b border-slate-200 bg-slate-50 text-slate-600">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Start EA</th>
                    <th className="px-3 py-2 font-semibold">Function Name</th>
                    <th className="px-3 py-2 font-semibold text-right">Size</th>
                    <th className="px-3 py-2 font-semibold text-right">In / Out</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {funcs.map((f) => {
                    const active = selectedFunc?.startEa === f.startEa;
                    return (
                      <tr
                        key={f.startEa}
                        onClick={() => setSelectedFunc(f)}
                        className={`cursor-pointer ${
                          active ? 'bg-sky-50/70' : 'hover:bg-slate-50'
                        }`}
                      >
                        <td className="px-3 py-2 font-mono text-sky-700 whitespace-nowrap">
                          {f.startEa}
                        </td>
                        <td className="px-3 py-2 font-mono font-medium text-slate-900 truncate max-w-[240px]">
                          {f.name}
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-slate-600 tabular-nums">
                          {f.size} B
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-slate-500 tabular-nums">
                          {f.callerCount} / {f.calleeCount}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white p-5">
            {selectedFunc ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3 border-b border-slate-200 pb-3">
                  <div className="min-w-0">
                    <div className="font-mono text-xs text-slate-500">
                      {selectedFunc.startEa} – {selectedFunc.endEa} · {selectedFunc.size} bytes
                    </div>
                    <h2 className="mt-0.5 font-mono text-base font-bold text-slate-900 break-all">
                      {selectedFunc.name}
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => onJumpHex(selectedFunc.startEa)}
                    className="shrink-0 rounded-lg bg-sky-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap"
                  >
                    Hex Bytes
                  </button>
                </div>

                <div>
                  <h3 className="text-xs font-semibold text-slate-500 mb-1.5">
                    Callers ({selectedFunc.callers.length})
                  </h3>
                  {selectedFunc.callers.length > 0 ? (
                    <div className="max-h-44 overflow-y-auto space-y-1">
                      {selectedFunc.callers.map((c, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => jumpToFunctionRef(c)}
                          className="block w-full rounded bg-slate-50 px-2.5 py-1.5 text-left font-mono text-xs text-sky-700 hover:bg-sky-50 truncate"
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">No recorded direct callers.</p>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <h3 className="text-xs font-semibold text-slate-500 mb-1.5">
                    Callees ({selectedFunc.callees.length})
                  </h3>
                  {selectedFunc.callees.length > 0 ? (
                    <div className="max-h-44 overflow-y-auto space-y-1">
                      {selectedFunc.callees.map((c, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => jumpToFunctionRef(c)}
                          className="block w-full rounded bg-slate-50 px-2.5 py-1.5 text-left font-mono text-xs text-slate-800 hover:bg-sky-50 hover:text-sky-700 truncate"
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">Leaf function (no recorded callees).</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500">
                Select a function to inspect its call graph neighborhood.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2.5 text-xs text-slate-600">
            <span className="tabular-nums">
              {loading
                ? 'Searching 29,217 records...'
                : `Showing ${Math.min(offset + 1, total)}–${Math.min(offset + limit, total)} of ${total.toLocaleString()} items`}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - limit))}
                className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                disabled={offset + limit >= total}
                onClick={() => setOffset((o) => o + limit)}
                className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className="max-h-[640px] overflow-auto">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 border-b border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-3 py-2 font-semibold">Start EA</th>
                  <th className="px-3 py-2 font-semibold">Size</th>
                  <th className="px-3 py-2 font-semibold">Name</th>
                  <th className="px-3 py-2 font-semibold">Disassembly / Data</th>
                  <th className="px-3 py-2 font-semibold">Target EA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {dataItems.map((d, idx) => (
                  <tr key={`${d.startEa}-${idx}`} className="hover:bg-slate-50">
                    <td className="px-3 py-1.5 whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => onJumpHex(d.startEa)}
                        className="text-sky-700 underline decoration-sky-300 underline-offset-2 hover:text-sky-900"
                      >
                        {d.startEa}
                      </button>
                    </td>
                    <td className="px-3 py-1.5 text-slate-500 tabular-nums">{d.size}</td>
                    <td className="px-3 py-1.5 text-slate-900">{d.name || '—'}</td>
                    <td className="px-3 py-1.5 text-slate-600 max-w-md truncate">
                      {d.disasm || d.hexPreview}
                    </td>
                    <td className="px-3 py-1.5 text-slate-600 whitespace-nowrap">
                      {d.targetEa || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
