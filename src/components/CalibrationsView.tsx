import React, { useEffect, useMemo, useState } from 'react';
import { Download, Search, SlidersHorizontal } from 'lucide-react';
import type {
  CalibrationsResponse,
  CandidateRow,
  OpenLeadRow,
  TablePreset,
  XmlDefinitionSet,
  XmlTable,
} from '../types';

interface CalibrationsViewProps {
  onJumpHex: (addr: string) => void;
  onOpenPresetTable: (preset: TablePreset) => void;
}

type CalTab = 'merged' | 'ignition' | 'fragment' | 'candidates' | 'leads' | 'raw-xml';
type SpecFilter = 'ALL' | 'VERIFIED' | 'SPECULATIVE';

function buildTablePreset(tbl: XmlTable): TablePreset {
  const storage = tbl.scaling?.storagetype === 'uint16' ? 'uint16' : 'uint8';
  const endian = tbl.scaling?.endian === 'little' ? 'little' : 'big';
  return {
    label: tbl.name,
    address: tbl.storageaddress,
    rows: tbl.sizey,
    cols: tbl.sizex,
    storage,
    endian,
    mult: 1,
    offset: 0,
    expr: tbl.scaling?.expression || 'x',
    yAxisAddr: tbl.yAxis && !tbl.yAxis.isStatic ? tbl.yAxis.storageaddress : undefined,
    yAxisStorage: tbl.yAxis?.storagetype === 'uint16' ? 'uint16' : 'uint8',
    yAxisMult: 1,
    yAxisExpr: tbl.yAxis?.scaling?.expression || 'x',
    xAxisAddr: tbl.xAxis && !tbl.xAxis.isStatic ? tbl.xAxis.storageaddress : undefined,
    xAxisStorage: tbl.xAxis?.storagetype === 'uint16' ? 'uint16' : 'uint8',
    xAxisMult: 1,
    xAxisExpr: tbl.xAxis?.scaling?.expression || 'x',
  };
}

function heatCellClass(val: number, min: number, max: number): string {
  const span = max - min;
  if (span <= 0) return 'bg-slate-50 text-slate-900';
  const ratio = (val - min) / span;
  if (ratio >= 0.85) return 'bg-amber-200/80 text-slate-950 font-semibold';
  if (ratio >= 0.65) return 'bg-amber-100/80 text-slate-900';
  if (ratio >= 0.4) return 'bg-sky-100/80 text-slate-900';
  if (ratio >= 0.15) return 'bg-sky-50 text-slate-800';
  return 'bg-white text-slate-700';
}

export const CalibrationsView: React.FC<CalibrationsViewProps> = ({
  onJumpHex,
  onOpenPresetTable,
}) => {
  const [tab, setTab] = useState<CalTab>('merged');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [mergedV3, setMergedV3] = useState<XmlDefinitionSet | null>(null);
  const [ignitionDecoded, setIgnitionDecoded] = useState<XmlDefinitionSet | null>(null);
  const [repoFragment, setRepoFragment] = useState<XmlDefinitionSet | null>(null);
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [openLeads, setOpenLeads] = useState<OpenLeadRow[]>([]);

  const [selectedTableId, setSelectedTableId] = useState<string>('');
  const [query, setQuery] = useState('');
  const [specFilter, setSpecFilter] = useState<SpecFilter>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [showRaw3d, setShowRaw3d] = useState(false);

  const [rawXmlSourceKey, setRawXmlSourceKey] = useState<'merged' | 'ignition' | 'fragment'>('merged');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetch('/api/calibrations')
      .then((r) => r.json())
      .then((d: CalibrationsResponse) => {
        if (!active) return;
        setCandidates(d.candidates || []);
        setOpenLeads(d.openLeads || []);
        setMergedV3(d.mergedV3 || null);
        setIgnitionDecoded(d.ignitionDecoded || null);
        setRepoFragment(d.repoFragment || null);
        if (d.mergedV3?.tables?.length) {
          setSelectedTableId(d.mergedV3.tables[0].id);
        } else if (d.repoFragment?.tables?.length) {
          setSelectedTableId(d.repoFragment.tables[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message || 'Failed to load calibration datasets');
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const activeXmlDef: XmlDefinitionSet | null = useMemo(() => {
    if (tab === 'merged') return mergedV3;
    if (tab === 'ignition') return ignitionDecoded;
    if (tab === 'fragment') return repoFragment;
    return null;
  }, [tab, mergedV3, ignitionDecoded, repoFragment]);

  useEffect(() => {
    setCategoryFilter('ALL');
    setSpecFilter('ALL');
    if (activeXmlDef?.tables?.length) {
      setSelectedTableId(activeXmlDef.tables[0].id);
    }
  }, [tab, activeXmlDef]);

  const categories = useMemo(() => {
    if (!activeXmlDef) return [];
    const set = new Set<string>();
    activeXmlDef.tables.forEach((t) => set.add(t.category.replace(/^SPEC\/\//, '')));
    return Array.from(set);
  }, [activeXmlDef]);

  const filteredXmlTables = useMemo(() => {
    if (!activeXmlDef) return [];
    const q = query.trim().toLowerCase();
    return activeXmlDef.tables.filter((t) => {
      if (specFilter === 'VERIFIED' && t.isSpeculative) return false;
      if (specFilter === 'SPECULATIVE' && !t.isSpeculative) return false;
      if (
        categoryFilter !== 'ALL' &&
        t.category.replace(/^SPEC\/\//, '') !== categoryFilter
      ) {
        return false;
      }
      if (!q) return true;
      return (
        t.name.toLowerCase().includes(q) ||
        t.storageaddress.toLowerCase().includes(q) ||
        t.category.toLowerCase().includes(q) ||
        t.scalingName.toLowerCase().includes(q) ||
        (t.commentNote || '').toLowerCase().includes(q)
      );
    });
  }, [activeXmlDef, query, specFilter, categoryFilter]);

  const selectedTable = useMemo(() => {
    if (!filteredXmlTables.length) return null;
    return (
      filteredXmlTables.find((t) => t.id === selectedTableId) || filteredXmlTables[0]
    );
  }, [filteredXmlTables, selectedTableId]);

  const filteredCandidates = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return candidates;
    return candidates.filter(
      (c) =>
        c.address.toLowerCase().includes(q) ||
        c.candidate_name.toLowerCase().includes(q) ||
        c.axis_or_reader.toLowerCase().includes(q)
    );
  }, [candidates, query]);

  const filteredLeads = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return openLeads;
    return openLeads.filter(
      (l) =>
        l.id.toLowerCase().includes(q) ||
        l.address_or_topic.toLowerCase().includes(q) ||
        l.best_current_interpretation.toLowerCase().includes(q) ||
        l.confidence_or_note.toLowerCase().includes(q)
    );
  }, [openLeads, query]);

  const rawXmlSet: XmlDefinitionSet | null = useMemo(() => {
    if (rawXmlSourceKey === 'ignition') return ignitionDecoded;
    if (rawXmlSourceKey === 'fragment') return repoFragment;
    return mergedV3;
  }, [rawXmlSourceKey, mergedV3, ignitionDecoded, repoFragment]);

  const handleCopyXml = () => {
    if (!rawXmlSet?.rawXml) return;
    navigator.clipboard.writeText(rawXmlSet.rawXml).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };

  const handleDownloadXml = () => {
    if (!rawXmlSet?.rawXml) return;
    const blob = new Blob([rawXmlSet.rawXml], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = rawXmlSet.filename || 'el19a_definition.xml';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-12 rounded-lg border border-slate-200 bg-white" />
        <div className="h-96 rounded-lg border border-slate-200 bg-white" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
        {error}
      </div>
    );
  }

  const verifiedCount = activeXmlDef
    ? activeXmlDef.tables.filter((t) => !t.isSpeculative).length
    : 0;
  const specCount = activeXmlDef
    ? activeXmlDef.tables.filter((t) => t.isSpeculative).length
    : 0;

  return (
    <div className="space-y-5">
      {/* Workspace Toolbar */}
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setTab('merged')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'merged'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Merged Def v3 ({mergedV3?.tables.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setTab('ignition')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'ignition'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Ignition Decoded ({ignitionDecoded?.tables.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setTab('fragment')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'fragment'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Repo Fragment ({repoFragment?.tables.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setTab('candidates')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'candidates'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Candidates ({candidates.length})
          </button>
          <button
            type="button"
            onClick={() => setTab('leads')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'leads'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Open Leads ({openLeads.length})
          </button>
          <button
            type="button"
            onClick={() => setTab('raw-xml')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'raw-xml'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            XML Source
          </button>
        </div>

        {tab !== 'raw-xml' && (
          <div className="relative w-full xl:w-72">
            <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter tables by name, 0x addr, note..."
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-3 pl-9 text-xs text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>
        )}
      </div>

      {/* XML Definition Browser (Merged Def v3 / Ignition Decoded / Repo Fragment) */}
      {(tab === 'merged' || tab === 'ignition' || tab === 'fragment') && activeXmlDef && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left Panel: Filterable List of Tables */}
          <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white overflow-hidden flex flex-col">
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-700">
                  {activeXmlDef.romid?.xmlid || activeXmlDef.label}
                </span>
                <span className="font-mono text-slate-500 tabular-nums">
                  {verifiedCount} verified · {specCount} spec
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {specCount > 0 && verifiedCount > 0 && (
                  <div className="flex items-center gap-1 rounded-md bg-slate-200/70 p-0.5 text-[11px]">
                    {(['ALL', 'VERIFIED', 'SPECULATIVE'] as SpecFilter[]).map((f) => (
                      <button
                        key={f}
                        type="button"
                        onClick={() => setSpecFilter(f)}
                        className={`rounded px-2 py-0.5 font-medium transition-colors whitespace-nowrap ${
                          specFilter === f
                            ? 'bg-white text-slate-900 shadow-xs'
                            : 'text-slate-600 hover:text-slate-900'
                        }`}
                      >
                        {f === 'ALL' ? 'All' : f === 'VERIFIED' ? 'Verified' : 'Spec [S]'}
                      </button>
                    ))}
                  </div>
                )}

                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="min-w-0 flex-1 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700"
                >
                  <option value="ALL">All Categories ({activeXmlDef.tables.length})</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="max-h-[680px] overflow-y-auto divide-y divide-slate-100">
              {filteredXmlTables.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">
                  No tables match the current filter.
                </div>
              ) : (
                filteredXmlTables.map((tbl) => {
                  const active = tbl.id === selectedTable?.id;
                  return (
                    <button
                      key={tbl.id}
                      type="button"
                      onClick={() => setSelectedTableId(tbl.id)}
                      className={`flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition-colors ${
                        active ? 'bg-sky-50/80' : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="min-w-0">
                        <div className="text-sm font-semibold text-slate-900 truncate">
                          {tbl.name}
                        </div>
                        <div className="mt-0.5 text-xs text-slate-500 truncate">
                          {tbl.category.replace(/^SPEC\/\//, '')}
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs font-mono">
                          <span className="text-slate-700">{tbl.storageaddress}</span>
                          <span className="text-slate-300">·</span>
                          <span className="text-slate-500">{tbl.type}</span>
                          <span className="text-slate-300">·</span>
                          <span className="text-slate-500">
                            {tbl.scaling?.units || tbl.scalingName || 'raw'}
                          </span>
                          <span className="text-slate-300">·</span>
                          <span
                            className={
                              tbl.isSpeculative ? 'text-amber-700 font-sans' : 'text-emerald-700 font-sans'
                            }
                          >
                            {tbl.isSpeculative ? 'Speculative' : 'Verified'}
                          </span>
                        </div>
                      </div>
                      <span className="shrink-0 font-mono text-xs font-medium text-sky-700 tabular-nums">
                        {tbl.sizey}×{tbl.sizex}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Panel: Selected Table Live ROM Decode */}
          <div className="lg:col-span-7 rounded-lg border border-slate-200 bg-white p-5">
            {selectedTable ? (
              <div className="space-y-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between border-b border-slate-200 pb-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span>{selectedTable.category.replace(/^SPEC\/\//, '')}</span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono text-slate-700">
                        {selectedTable.storageaddress}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span
                        className={`font-medium ${
                          selectedTable.isSpeculative ? 'text-amber-700' : 'text-emerald-700'
                        }`}
                      >
                        {selectedTable.isSpeculative ? 'Speculative [S]' : 'Verified'}
                      </span>
                    </div>
                    <h2 className="mt-1 text-lg font-bold text-slate-900">
                      {selectedTable.name}
                    </h2>
                    {selectedTable.commentNote && (
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
                        {selectedTable.commentNote}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onJumpHex(selectedTable.storageaddress)}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap"
                    >
                      Hex Dump
                    </button>
                    <button
                      type="button"
                      onClick={() => onOpenPresetTable(buildTablePreset(selectedTable))}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-sky-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap"
                    >
                      <SlidersHorizontal className="h-3.5 w-3.5" />
                      Open in Table Lab
                    </button>
                  </div>
                </div>

                {/* Scaling Formula Metadata */}
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                  <div className="rounded-md bg-slate-50 p-2.5">
                    <div className="text-slate-500">Storage</div>
                    <div className="mt-0.5 font-mono font-semibold text-slate-900">
                      {selectedTable.scaling?.storagetype || 'uint8'} (
                      {selectedTable.scaling?.endian || 'big'})
                    </div>
                  </div>
                  <div className="rounded-md bg-slate-50 p-2.5">
                    <div className="text-slate-500">Expression</div>
                    <div className="mt-0.5 font-mono font-semibold text-slate-900">
                      {selectedTable.scaling?.expression || 'x'}
                    </div>
                  </div>
                  <div className="rounded-md bg-slate-50 p-2.5">
                    <div className="text-slate-500">Units</div>
                    <div className="mt-0.5 font-mono font-semibold text-slate-900">
                      {selectedTable.scaling?.units || 'raw'}
                    </div>
                  </div>
                  <div className="rounded-md bg-slate-50 p-2.5">
                    <div className="text-slate-500">Dimensions</div>
                    <div className="mt-0.5 font-mono font-semibold text-slate-900">
                      {selectedTable.sizey} × {selectedTable.sizex} ({selectedTable.type})
                    </div>
                  </div>
                </div>

                {/* Axis Source Readout when ROM or Static Axes are attached */}
                {(selectedTable.xAxis || selectedTable.yAxis) && (
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
                    {selectedTable.yAxis && (
                      <div className="rounded-md border border-slate-200 px-3 py-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-700">
                            Y Axis · {selectedTable.yAxis.name}
                          </span>
                          <span className="font-mono text-slate-500">
                            {selectedTable.yAxis.isStatic
                              ? 'Static'
                              : selectedTable.yAxis.storageaddress}
                          </span>
                        </div>
                        <div className="mt-0.5 font-mono text-[11px] text-slate-500">
                          {selectedTable.yAxis.scaling?.expression || 'x'} (
                          {selectedTable.yAxis.scaling?.units || 'raw'}) ·{' '}
                          {selectedTable.yAxis.values[0]} →{' '}
                          {selectedTable.yAxis.values[selectedTable.yAxis.values.length - 1]}
                        </div>
                      </div>
                    )}
                    {selectedTable.xAxis && (
                      <div className="rounded-md border border-slate-200 px-3 py-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-700">
                            X Axis · {selectedTable.xAxis.name}
                          </span>
                          <span className="font-mono text-slate-500">
                            {selectedTable.xAxis.isStatic
                              ? 'Static'
                              : selectedTable.xAxis.storageaddress}
                          </span>
                        </div>
                        <div className="mt-0.5 font-mono text-[11px] text-slate-500">
                          {selectedTable.xAxis.scaling?.expression || 'x'} (
                          {selectedTable.xAxis.scaling?.units || 'raw'}) ·{' '}
                          {selectedTable.xAxis.values[0]} →{' '}
                          {selectedTable.xAxis.values[selectedTable.xAxis.values.length - 1]}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* 3D Matrix View */}
                {selectedTable.sizex > 1 &&
                  selectedTable.sizey > 1 &&
                  selectedTable.scaledMatrix &&
                  selectedTable.rawMatrix && (
                    <Matrix3DViewer
                      table={selectedTable}
                      showRaw={showRaw3d}
                      onToggleRaw={() => setShowRaw3d((v) => !v)}
                    />
                  )}

                {/* 2D Curve + Point Table View */}
                {selectedTable.sizex === 1 && selectedTable.sizey > 1 && (
                  <>
                    <CurveSvgChart
                      values={selectedTable.scaledValues}
                      axisLabels={selectedTable.yAxis?.values || selectedTable.axisData}
                      units={selectedTable.scaling?.units || ''}
                    />

                    <div className="overflow-x-auto rounded-lg border border-slate-200">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                          <tr>
                            <th className="px-3 py-2 font-medium">Index</th>
                            <th className="px-3 py-2 font-medium">ROM Addr</th>
                            {(selectedTable.yAxis?.values?.length ||
                              selectedTable.axisData?.length) ? (
                              <th className="px-3 py-2 font-medium text-right">
                                {selectedTable.yAxis?.name || selectedTable.axisName || 'Axis'}
                              </th>
                            ) : null}
                            <th className="px-3 py-2 font-medium text-right">Raw</th>
                            <th className="px-3 py-2 font-medium text-right">
                              Scaled ({selectedTable.scaling?.units || 'val'})
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 font-mono tabular-nums">
                          {selectedTable.rawBytes.map((raw, idx) => {
                            const elemSize =
                              selectedTable.scaling?.storagetype === 'uint16' ? 2 : 1;
                            const addrHex =
                              '0x' +
                              (selectedTable.addressNum + idx * elemSize)
                                .toString(16)
                                .toUpperCase()
                                .padStart(4, '0');
                            const axisVals =
                              selectedTable.yAxis?.values || selectedTable.axisData;
                            return (
                              <tr key={idx} className="hover:bg-slate-50">
                                <td className="px-3 py-1.5 text-slate-500">{idx}</td>
                                <td className="px-3 py-1.5 text-slate-700">{addrHex}</td>
                                {axisVals && axisVals.length > 0 && (
                                  <td className="px-3 py-1.5 text-right text-slate-700">
                                    {axisVals[idx] ?? '—'}
                                  </td>
                                )}
                                <td className="px-3 py-1.5 text-right text-slate-700">
                                  0x
                                  {raw
                                    .toString(16)
                                    .toUpperCase()
                                    .padStart(elemSize * 2, '0')}{' '}
                                  ({raw})
                                </td>
                                <td className="px-3 py-1.5 text-right font-semibold text-sky-700">
                                  {selectedTable.scaledValues[idx]}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                {/* 1D Scalar Readout */}
                {selectedTable.sizex === 1 && selectedTable.sizey === 1 && (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                      <div>
                        <div className="text-xs text-slate-500">ROM Offset</div>
                        <div className="mt-1 font-mono text-xl font-bold text-slate-900">
                          {selectedTable.storageaddress}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Live ROM Value (Raw)</div>
                        <div className="mt-1 font-mono text-xl font-bold text-slate-800 tabular-nums">
                          0x
                          {(selectedTable.rawBytes[0] ?? 0)
                            .toString(16)
                            .toUpperCase()
                            .padStart(
                              selectedTable.scaling?.storagetype === 'uint16' ? 4 : 2,
                              '0'
                            )}{' '}
                          <span className="text-sm font-normal text-slate-500">
                            ({selectedTable.rawBytes[0] ?? 0})
                          </span>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Decoded Value</div>
                        <div className="mt-1 font-mono text-xl font-bold text-sky-700 tabular-nums">
                          {selectedTable.scaledValues[0] ?? 0}{' '}
                          <span className="text-sm font-medium text-slate-600">
                            {selectedTable.scaling?.units || ''}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-slate-500">
                Select a table to inspect live ROM bytes.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Candidate Register */}
      {tab === 'candidates' && (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
            Historical seed register from{' '}
            <code className="font-mono">CALIBRATIONS/candidate_register.csv</code> enriched with live
            first-16 ROM bytes from <code className="font-mono">VERSA f501.bin</code>.
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-2.5 font-semibold">Address</th>
                  <th className="px-4 py-2.5 font-semibold">Candidate Name</th>
                  <th className="px-4 py-2.5 font-semibold">Dims</th>
                  <th className="px-4 py-2.5 font-semibold">Axis / Reader</th>
                  <th className="px-4 py-2.5 font-semibold">Conversion</th>
                  <th className="px-4 py-2.5 font-semibold">Live ROM Bytes (16B)</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredCandidates.map((c) => {
                  const dimMatch = c.dimensions.match(/^(\d+)x(\d+)$/);
                  const rows = dimMatch
                    ? parseInt(dimMatch[1], 10)
                    : parseInt(c.dimensions, 10) || 16;
                  const cols = dimMatch ? parseInt(dimMatch[2], 10) : 1;
                  return (
                    <tr key={c.address} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-mono font-semibold text-sky-700 whitespace-nowrap">
                        0x{c.address}
                      </td>
                      <td className="px-4 py-2.5 font-medium text-slate-900">
                        {c.candidate_name}
                        <span className="ml-2 text-slate-400">· {c.status}</span>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-slate-600 whitespace-nowrap">
                        {c.dimensions} ({c.storage})
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">{c.axis_or_reader}</td>
                      <td className="px-4 py-2.5 font-mono text-slate-600">{c.conversion}</td>
                      <td className="px-4 py-2.5 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {c.liveHex}
                      </td>
                      <td className="px-4 py-2.5 text-right whitespace-nowrap">
                        <button
                          type="button"
                          onClick={() =>
                            onOpenPresetTable({
                              label: `${c.address} — ${c.candidate_name}`,
                              address: `0x${c.address}`,
                              rows,
                              cols,
                              storage: 'uint8',
                              endian: 'big',
                              mult: 1,
                              offset: 0,
                            })
                          }
                          className="mr-2 rounded border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Table Lab
                        </button>
                        <button
                          type="button"
                          onClick={() => onJumpHex(`0x${c.address}`)}
                          className="rounded bg-slate-100 px-2 py-1 font-mono text-xs text-sky-700 hover:bg-sky-50"
                        >
                          Hex
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Open Leads */}
      {tab === 'leads' && (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-2.5 font-semibold">ID</th>
                  <th className="px-4 py-2.5 font-semibold">Address / Topic</th>
                  <th className="px-4 py-2.5 font-semibold">Interpretation</th>
                  <th className="px-4 py-2.5 font-semibold">Status</th>
                  <th className="px-4 py-2.5 font-semibold">Evidence Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLeads.map((l) => {
                  const isRomAddr = /^[0-9A-F]{4,6}$/i.test(l.address_or_topic);
                  return (
                    <tr key={l.id} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-mono font-semibold text-slate-700 whitespace-nowrap">
                        {l.id}
                      </td>
                      <td className="px-4 py-2.5 font-mono whitespace-nowrap">
                        {isRomAddr ? (
                          <button
                            type="button"
                            onClick={() => onJumpHex(`0x${l.address_or_topic}`)}
                            className="text-sky-700 underline decoration-sky-300 underline-offset-2 hover:text-sky-900"
                          >
                            0x{l.address_or_topic}
                          </button>
                        ) : (
                          <span className="text-slate-900">{l.address_or_topic}</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 font-medium text-slate-900">
                        {l.best_current_interpretation}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-slate-600 whitespace-nowrap">
                        {l.status}
                      </td>
                      <td className="px-4 py-2.5 text-slate-600 max-w-md">
                        {l.confidence_or_note}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Raw XML Source */}
      {tab === 'raw-xml' && rawXmlSet && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  {rawXmlSet.romid?.xmlid || rawXmlSet.filename}
                </h3>
                <p className="text-xs text-slate-500">
                  {rawXmlSet.scalings.length} scalings · {rawXmlSet.tables.length} tables
                  {rawXmlSet.romid?.internalidstring
                    ? ` · FID ${rawXmlSet.romid.internalidstring} @ ${rawXmlSet.romid.internalidaddress}`
                    : ''}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-1 rounded-md bg-slate-100 p-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => setRawXmlSourceKey('merged')}
                    className={`rounded px-2.5 py-1 font-medium whitespace-nowrap ${
                      rawXmlSourceKey === 'merged'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600'
                    }`}
                  >
                    Merged Def v3
                  </button>
                  <button
                    type="button"
                    onClick={() => setRawXmlSourceKey('ignition')}
                    className={`rounded px-2.5 py-1 font-medium whitespace-nowrap ${
                      rawXmlSourceKey === 'ignition'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600'
                    }`}
                  >
                    Ignition Decoded
                  </button>
                  <button
                    type="button"
                    onClick={() => setRawXmlSourceKey('fragment')}
                    className={`rounded px-2.5 py-1 font-medium whitespace-nowrap ${
                      rawXmlSourceKey === 'fragment'
                        ? 'bg-white text-slate-900 shadow-xs'
                        : 'text-slate-600'
                    }`}
                  >
                    Repo Fragment
                  </button>
                </div>
                <button
                  type="button"
                  onClick={handleCopyXml}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap"
                >
                  {copied ? 'Copied XML' : 'Copy XML'}
                </button>
                <button
                  type="button"
                  onClick={handleDownloadXml}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-sky-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download .xml
                </button>
              </div>
            </div>

            {Object.keys(rawXmlSet.romid || {}).length > 0 && (
              <div className="grid grid-cols-2 gap-2 rounded-md border border-slate-200 bg-slate-50 p-3 text-xs sm:grid-cols-4 lg:grid-cols-6">
                {Object.entries(rawXmlSet.romid).map(([k, v]) => (
                  <div key={k}>
                    <div className="text-[11px] text-slate-500">{k}</div>
                    <div className="font-mono font-semibold text-slate-800 truncate">{v}</div>
                  </div>
                ))}
              </div>
            )}

            <pre className="max-h-[540px] overflow-auto rounded-lg bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-100">
              {rawXmlSet.rawXml}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

const Matrix3DViewer: React.FC<{
  table: XmlTable;
  showRaw: boolean;
  onToggleRaw: () => void;
}> = ({ table, showRaw, onToggleRaw }) => {
  const scaledMatrix = table.scaledMatrix || [];
  const rawMatrix = table.rawMatrix || [];
  const allVals = table.scaledValues;
  const minVal = allVals.length ? Math.min(...allVals) : 0;
  const maxVal = allVals.length ? Math.max(...allVals) : 0;
  const xLabels = table.xAxis?.values;
  const yLabels = table.yAxis?.values;
  const elemSize = table.scaling?.storagetype === 'uint16' ? 2 : 1;

  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="text-slate-600">
          3D Matrix ({table.sizey}Y × {table.sizex}X) · Range{' '}
          <span className="font-mono font-semibold text-slate-900 tabular-nums">
            {minVal} to {maxVal} {table.scaling?.units || ''}
          </span>
        </div>
        <button
          type="button"
          onClick={onToggleRaw}
          className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap"
        >
          {showRaw ? 'Show Scaled Values' : 'Show Raw Hex'}
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full border-collapse font-mono text-[11px] tabular-nums">
          <thead>
            <tr>
              <th className="border border-slate-200 bg-slate-100 px-2 py-1.5 text-left text-slate-500 whitespace-nowrap">
                RPM \ Load
              </th>
              {Array.from({ length: table.sizex }).map((_, c) => (
                <th
                  key={c}
                  className="border border-slate-200 bg-slate-100 px-2 py-1.5 text-right font-semibold text-slate-700 whitespace-nowrap"
                >
                  {xLabels && xLabels[c] !== undefined ? xLabels[c] : `X${c}`}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {scaledMatrix.map((rowVals, r) => (
              <tr key={r}>
                <th className="border border-slate-200 bg-slate-100 px-2 py-1 text-right font-semibold text-slate-700 whitespace-nowrap">
                  {yLabels && yLabels[r] !== undefined ? yLabels[r] : `Y${r}`}
                </th>
                {rowVals.map((val, c) => {
                  const raw = rawMatrix[r]?.[c] ?? 0;
                  return (
                    <td
                      key={c}
                      title={`Raw: ${raw} (0x${raw
                        .toString(16)
                        .toUpperCase()
                        .padStart(elemSize * 2, '0')}) | Scaled: ${val}`}
                      className={`border border-slate-200 px-1.5 py-1 text-right whitespace-nowrap ${heatCellClass(
                        val,
                        minVal,
                        maxVal
                      )}`}
                    >
                      {showRaw
                        ? `0x${raw
                            .toString(16)
                            .toUpperCase()
                            .padStart(elemSize * 2, '0')}`
                        : val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const CurveSvgChart: React.FC<{
  values: number[];
  axisLabels?: number[];
  units: string;
}> = ({ values, axisLabels, units }) => {
  const width = 620;
  const height = 170;
  const padL = 42;
  const padR = 16;
  const padT = 16;
  const padB = 26;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  const points = values.map((v, i) => {
    const x =
      padL +
      (values.length === 1
        ? (width - padL - padR) / 2
        : (i / (values.length - 1)) * (width - padL - padR));
    const y = padT + (1 - (v - min) / span) * (height - padT - padB);
    return { x, y, v, label: axisLabels?.[i] ?? i };
  });

  const polyline = points.map((p) => `${p.x},${p.y}`).join(' ');

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
        <span>Live ROM Curve Profile</span>
        <span className="font-mono tabular-nums">
          Min {min} {units} · Max {max} {units}
        </span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-40">
        <line x1={padL} y1={padT} x2={padL} y2={height - padB} stroke="#cbd5e1" strokeWidth="1" />
        <line
          x1={padL}
          y1={height - padB}
          x2={width - padR}
          y2={height - padB}
          stroke="#cbd5e1"
          strokeWidth="1"
        />
        <text x={4} y={padT + 8} fontSize="10" fill="#64748b" fontFamily="monospace">
          {max}
        </text>
        <text x={4} y={height - padB} fontSize="10" fill="#64748b" fontFamily="monospace">
          {min}
        </text>
        <polyline fill="none" stroke="#0369a1" strokeWidth="2" points={polyline} />
        {points.map((p, idx) => (
          <g key={idx}>
            <circle cx={p.x} cy={p.y} r="3.5" fill="#0369a1" stroke="#ffffff" strokeWidth="1.5" />
            {(values.length <= 16 || idx % 2 === 0) && (
              <text
                x={p.x}
                y={height - 8}
                textAnchor="middle"
                fontSize="9"
                fill="#64748b"
                fontFamily="monospace"
              >
                {p.label}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
};
