import React, { useEffect, useMemo, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import type { CandidateRow, OpenLeadRow, TablePreset, XmlScaling, XmlTable } from '../types';

interface CalibrationsViewProps {
  onJumpHex: (addr: string) => void;
  onOpenPresetTable: (preset: TablePreset) => void;
}

type CalTab = 'xml' | 'candidates' | 'leads' | 'raw-xml';

export const CalibrationsView: React.FC<CalibrationsViewProps> = ({
  onJumpHex,
  onOpenPresetTable,
}) => {
  const [tab, setTab] = useState<CalTab>('xml');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [openLeads, setOpenLeads] = useState<OpenLeadRow[]>([]);
  const [xmlTables, setXmlTables] = useState<XmlTable[]>([]);
  const [xmlScalings, setXmlScalings] = useState<XmlScaling[]>([]);
  const [rawXml, setRawXml] = useState('');
  const [selectedTableAddr, setSelectedTableAddr] = useState<string>('');
  const [query, setQuery] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetch('/api/calibrations')
      .then((r) => r.json())
      .then((d) => {
        if (!active) return;
        setCandidates(d.candidates || []);
        setOpenLeads(d.openLeads || []);
        setXmlTables(d.xmlTables || []);
        setXmlScalings(d.xmlScalings || []);
        setRawXml(d.rawXml || '');
        if (d.xmlTables?.length) {
          setSelectedTableAddr(d.xmlTables[0].storageaddress);
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

  const selectedTable = useMemo(
    () => xmlTables.find((t) => t.storageaddress === selectedTableAddr) || xmlTables[0] || null,
    [xmlTables, selectedTableAddr]
  );

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

  const handleCopyXml = () => {
    if (!rawXml) return;
    navigator.clipboard.writeText(rawXml).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
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

  return (
    <div className="space-y-5">
      {/* Workspace Toolbar */}
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setTab('xml')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              tab === 'xml'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            RomRaider XML Tables ({xmlTables.length})
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
            Candidate Register ({candidates.length})
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
            XML Fragment Source
          </button>
        </div>

        {(tab === 'candidates' || tab === 'leads') && (
          <div className="relative w-full sm:w-72">
            <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Filter by address or name..."
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pr-3 pl-9 text-xs text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:bg-white focus:outline-none"
            />
          </div>
        )}
      </div>

      {/* Tab 1: Live RomRaider XML Tables */}
      {tab === 'xml' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-5 rounded-lg border border-slate-200 bg-white divide-y divide-slate-100">
            <div className="px-4 py-3 text-xs font-semibold text-slate-500">
              Defined Tables in Fragment XML
            </div>
            {xmlTables.map((tbl) => {
              const active = tbl.storageaddress === selectedTable?.storageaddress;
              return (
                <button
                  key={tbl.storageaddress}
                  type="button"
                  onClick={() => setSelectedTableAddr(tbl.storageaddress)}
                  className={`flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition-colors ${
                    active ? 'bg-sky-50/70' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-slate-900">{tbl.name}</div>
                    <div className="mt-0.5 text-xs text-slate-500">{tbl.category}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 font-mono">
                      <span>{tbl.storageaddress}</span>
                      <span>·</span>
                      <span>{tbl.type}</span>
                      <span>·</span>
                      <span>{tbl.scaling?.units || tbl.scalingName}</span>
                    </div>
                  </div>
                  <span className="shrink-0 font-mono text-xs font-medium text-sky-700 tabular-nums">
                    {tbl.sizey}×{tbl.sizex}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="lg:col-span-7 rounded-lg border border-slate-200 bg-white p-5">
            {selectedTable ? (
              <div className="space-y-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between border-b border-slate-200 pb-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>{selectedTable.category}</span>
                      <span>·</span>
                      <span className="font-mono">{selectedTable.storageaddress}</span>
                    </div>
                    <h2 className="mt-1 text-lg font-bold text-slate-900">{selectedTable.name}</h2>
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
                      onClick={() =>
                        onOpenPresetTable({
                          label: selectedTable.name,
                          address: selectedTable.storageaddress,
                          rows: selectedTable.sizey,
                          cols: selectedTable.sizex,
                          storage:
                            selectedTable.scaling?.storagetype === 'uint16' ? 'uint16' : 'uint8',
                          endian: selectedTable.scaling?.endian === 'little' ? 'little' : 'big',
                          mult: 1,
                          offset: 0,
                        })
                      }
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
                      {selectedTable.scaling?.storagetype || 'uint8'} ({selectedTable.scaling?.endian || 'big'})
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

                {/* SVG Curve Chart for 2D curves */}
                {selectedTable.scaledValues.length > 1 && (
                  <CurveSvgChart
                    values={selectedTable.scaledValues}
                    axisLabels={selectedTable.axisData}
                    units={selectedTable.scaling?.units || ''}
                  />
                )}

                {/* Live ROM Decoded Data Table */}
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                      <tr>
                        <th className="px-3 py-2 font-medium">Index</th>
                        <th className="px-3 py-2 font-medium">ROM Addr</th>
                        {selectedTable.axisData && (
                          <th className="px-3 py-2 font-medium text-right">
                            {selectedTable.axisName || 'Axis'}
                          </th>
                        )}
                        <th className="px-3 py-2 font-medium text-right">Raw Byte</th>
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
                        return (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="px-3 py-1.5 text-slate-500">{idx}</td>
                            <td className="px-3 py-1.5 text-slate-700">{addrHex}</td>
                            {selectedTable.axisData && (
                              <td className="px-3 py-1.5 text-right text-slate-700">
                                {selectedTable.axisData[idx] ?? '—'}
                              </td>
                            )}
                            <td className="px-3 py-1.5 text-right text-slate-700">
                              0x{raw.toString(16).toUpperCase().padStart(2, '0')} ({raw})
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
              </div>
            ) : (
              <div className="text-sm text-slate-500">Select a table to inspect live ROM bytes.</div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Candidate Register */}
      {tab === 'candidates' && (
        <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
            Historical seed register from <code className="font-mono">CALIBRATIONS/candidate_register.csv</code> enriched with live first-16 ROM bytes from <code className="font-mono">VERSA f501.bin</code>.
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

      {/* Tab 3: Open Leads */}
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

      {/* Tab 4: Raw XML Fragment + Scalings */}
      {tab === 'raw-xml' && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  EL19A_ETC_Dashpot_Limiters_fragment-2.xml
                </h3>
                <p className="text-xs text-slate-500">
                  {xmlScalings.length} scaling definitions · {xmlTables.length} table definitions
                </p>
              </div>
              <button
                type="button"
                onClick={handleCopyXml}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                {copied ? 'Copied XML' : 'Copy XML'}
              </button>
            </div>
            <pre className="max-h-[540px] overflow-auto rounded-lg bg-slate-900 p-4 font-mono text-xs leading-relaxed text-slate-100">
              {rawXml}
            </pre>
          </div>
        </div>
      )}
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
      (values.length === 1 ? (width - padL - padR) / 2 : (i / (values.length - 1)) * (width - padL - padR));
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
