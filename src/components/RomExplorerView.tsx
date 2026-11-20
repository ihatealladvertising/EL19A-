import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import type { RomHexResponse, RomTableResponse, TablePreset } from '../types';

interface RomExplorerViewProps {
  initialAddress: string;
  initialPreset: TablePreset | null;
  initialMode?: 'hex' | 'table';
}

const TABLE_PRESETS: TablePreset[] = [
  {
    label: 'CD56 · 16x16 UWORD BE (WO64972)',
    address: '0xCD56',
    rows: 16,
    cols: 16,
    storage: 'uint16',
    endian: 'big',
    mult: 1,
    offset: 0,
    yAxisAddr: '0xE2C9',
    yAxisStorage: 'uint8',
    yAxisMult: 16,
    xAxisAddr: '0xFEC0',
    xAxisStorage: 'uint16',
    xAxisMult: 1,
  },
  {
    label: '9C2E · 16x16 UBYTE Map (WO64968)',
    address: '0x9C2E',
    rows: 16,
    cols: 16,
    storage: 'uint8',
    endian: 'big',
    mult: 1,
    offset: 0,
    yAxisAddr: '0xE4BC',
    yAxisStorage: 'uint8',
    yAxisMult: 4,
    xAxisAddr: '0xE4AC',
    xAxisStorage: 'uint8',
    xAxisMult: 1,
  },
  {
    label: '9B19 · 4x4 UBYTE Manual Map (WO64978)',
    address: '0x9B19',
    rows: 4,
    cols: 4,
    storage: 'uint8',
    endian: 'big',
    mult: 1,
    offset: 0,
    yAxisAddr: '0xE062',
    yAxisStorage: 'uint8',
    yAxisMult: 1,
    xAxisAddr: '0xE066',
    xAxisStorage: 'uint8',
    xAxisMult: 1,
  },
  {
    label: 'A552 · 16x16 UBYTE Candidate',
    address: '0xA552',
    rows: 16,
    cols: 16,
    storage: 'uint8',
    endian: 'big',
    mult: 1,
    offset: 0,
  },
  {
    label: 'E678 · QDSPT Basic Curve (16x1)',
    address: '0xE678',
    rows: 16,
    cols: 1,
    storage: 'uint8',
    endian: 'big',
    mult: 2,
    offset: 0,
  },
  {
    label: 'F3D6 · TVO Limit Main (8x1)',
    address: '0xF3D6',
    rows: 8,
    cols: 1,
    storage: 'uint8',
    endian: 'big',
    mult: 0.3575,
    offset: 0,
    yAxisAddr: '0xF3C6',
    yAxisStorage: 'uint8',
    yAxisMult: 1,
  },
  {
    label: '10954 · 16x1 UWORD BE + F912 Axis (WO65004)',
    address: '0x10954',
    rows: 16,
    cols: 1,
    storage: 'uint16',
    endian: 'big',
    mult: 1,
    offset: -32768,
    yAxisAddr: '0xF912',
    yAxisStorage: 'uint16',
    yAxisMult: 1,
  },
];

export const RomExplorerView: React.FC<RomExplorerViewProps> = ({
  initialAddress,
  initialPreset,
  initialMode = 'hex',
}) => {
  const [mode, setMode] = useState<'hex' | 'table'>(initialMode);

  // Hex state
  const [offsetInput, setOffsetInput] = useState(initialAddress || '0x00E678');
  const [activeOffset, setActiveOffset] = useState(initialAddress || '0x00E678');
  const [hexLength, setHexLength] = useState(256);
  const [hexData, setHexData] = useState<RomHexResponse | null>(null);
  const [hexLoading, setHexLoading] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'ascii' | 'hex'>('ascii');
  const [searchResults, setSearchResults] = useState<
    { offset: number; address: string; preview: string }[]
  >([]);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Table Lab state
  const [tblAddr, setTblAddr] = useState(initialPreset?.address || '0xCD56');
  const [tblRows, setTblRows] = useState(initialPreset?.rows || 16);
  const [tblCols, setTblCols] = useState(initialPreset?.cols || 16);
  const [tblStorage, setTblStorage] = useState<'uint8' | 'uint16'>(
    initialPreset?.storage || 'uint16'
  );
  const [tblEndian, setTblEndian] = useState<'big' | 'little'>(
    initialPreset?.endian || 'big'
  );
  const [tblMult, setTblMult] = useState(String(initialPreset?.mult ?? 1));
  const [tblOffset, setTblOffset] = useState(String(initialPreset?.offset ?? 0));
  const [yAxisAddr, setYAxisAddr] = useState(initialPreset?.yAxisAddr || '0xE2C9');
  const [yAxisStorage, setYAxisStorage] = useState<'uint8' | 'uint16'>(
    initialPreset?.yAxisStorage || 'uint8'
  );
  const [yAxisMult, setYAxisMult] = useState(String(initialPreset?.yAxisMult ?? 16));
  const [xAxisAddr, setXAxisAddr] = useState(initialPreset?.xAxisAddr || '0xFEC0');
  const [xAxisStorage, setXAxisStorage] = useState<'uint8' | 'uint16'>(
    initialPreset?.xAxisStorage || 'uint16'
  );
  const [xAxisMult, setXAxisMult] = useState(String(initialPreset?.xAxisMult ?? 1));
  const [tableData, setTableData] = useState<RomTableResponse | null>(null);
  const [tableError, setTableError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [xmlCopied, setXmlCopied] = useState(false);

  useEffect(() => {
    setOffsetInput(initialAddress);
    setActiveOffset(initialAddress);
  }, [initialAddress]);

  useEffect(() => {
    if (initialPreset) {
      setMode('table');
      applyPreset(initialPreset);
    }
  }, [initialPreset]);

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  useEffect(() => {
    let active = true;
    setHexLoading(true);
    fetch(`/api/rom/hex?offset=${encodeURIComponent(activeOffset)}&length=${hexLength}`)
      .then((r) => r.json())
      .then((d) => {
        if (!active) return;
        setHexData(d);
        setHexLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setHexLoading(false);
      });
    return () => {
      active = false;
    };
  }, [activeOffset, hexLength]);

  const loadTable = () => {
    setTableError(null);
    const params = new URLSearchParams({
      address: tblAddr,
      rows: String(tblRows),
      cols: String(tblCols),
      storage: tblStorage,
      endian: tblEndian,
      mult: tblMult || '1',
      offset: tblOffset || '0',
    });
    if (yAxisAddr.trim()) {
      params.set('yAxisAddr', yAxisAddr.trim());
      params.set('yAxisStorage', yAxisStorage);
      params.set('yAxisMult', yAxisMult || '1');
    }
    if (xAxisAddr.trim()) {
      params.set('xAxisAddr', xAxisAddr.trim());
      params.set('xAxisStorage', xAxisStorage);
      params.set('xAxisMult', xAxisMult || '1');
    }
    fetch(`/api/rom/table?${params.toString()}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          setTableError(d.error);
          setTableData(null);
        } else {
          setTableData(d);
        }
      })
      .catch((e) => setTableError(e.message || 'Table read failed'));
  };

  useEffect(() => {
    if (mode === 'table') {
      loadTable();
    }
  }, [mode, tblAddr, tblRows, tblCols, tblStorage, tblEndian]);

  const applyPreset = (p: TablePreset) => {
    setTblAddr(p.address);
    setTblRows(p.rows);
    setTblCols(p.cols);
    setTblStorage(p.storage);
    setTblEndian(p.endian);
    setTblMult(String(p.mult));
    setTblOffset(String(p.offset));
    setYAxisAddr(p.yAxisAddr || '');
    setYAxisStorage(p.yAxisStorage || p.storage);
    setYAxisMult(String(p.yAxisMult ?? 1));
    setXAxisAddr(p.xAxisAddr || '');
    setXAxisStorage(p.xAxisStorage || p.storage);
    setXAxisMult(String(p.xAxisMult ?? 1));
  };

  const handleHexJump = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveOffset(offsetInput.trim() || '0x000000');
  };

  const stepHex = (delta: number) => {
    const cur = hexData?.offset ?? 0;
    const next = Math.max(0, Math.min((hexData?.romSize || 1048576) - hexLength, cur + delta));
    const hex = '0x' + next.toString(16).toUpperCase().padStart(6, '0');
    setOffsetInput(hex);
    setActiveOffset(hex);
  };

  const handleRomSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchError(null);
    if (!searchQuery.trim()) return;
    fetch(`/api/rom/search?q=${encodeURIComponent(searchQuery)}&mode=${searchMode}`)
      .then((r) => r.json())
      .then((d) => {
        if (d.error) {
          setSearchError(d.error);
          setSearchResults([]);
        } else {
          setSearchResults(d.matches || []);
        }
      })
      .catch((err) => setSearchError(err.message));
  };

  const cellHeatBg = (val: number, min: number, max: number) => {
    const span = max - min;
    if (span <= 0) return 'bg-slate-50 text-slate-900';
    const ratio = (val - min) / span;
    if (ratio >= 0.85) return 'bg-amber-200/80 text-slate-950 font-semibold';
    if (ratio >= 0.65) return 'bg-amber-100/80 text-slate-900';
    if (ratio >= 0.4) return 'bg-sky-100/80 text-slate-900';
    if (ratio >= 0.15) return 'bg-sky-50 text-slate-800';
    return 'bg-white text-slate-700';
  };

  const generatedXmlSnippet = tableData
    ? `<table name="EL19A_Table_${tableData.address}" category="Experimental" storageaddress="${tableData.address}" type="${tableData.cols > 1 ? '3D' : '2D'}" scaling="Custom_${tableData.storage}" sizey="${tableData.rows}"${tableData.cols > 1 ? ` sizex="${tableData.cols}"` : ''}>\n${
        yAxisAddr
          ? `  <table name="Y Axis" type="Y Axis" storageaddress="${yAxisAddr}" sizey="${tableData.rows}"/>\n`
          : ''
      }${
        xAxisAddr && tableData.cols > 1
          ? `  <table name="X Axis" type="X Axis" storageaddress="${xAxisAddr}" sizex="${tableData.cols}"/>\n`
          : ''
      }</table>`
    : '';

  return (
    <div className="space-y-5">
      {/* Mode Switcher */}
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setMode('hex')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              mode === 'hex' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            ROM Hex & Cross-Ref Inspector
          </button>
          <button
            type="button"
            onClick={() => setMode('table')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              mode === 'table'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            1D / 2D Table & Curve Lab
          </button>
        </div>

        <div className="font-mono text-xs text-slate-500">
          VERSA f501.bin · 1,048,576 B (0x000000–0x0FFFFF)
        </div>
      </div>

      {/* Mode 1: Hex Inspector */}
      {mode === 'hex' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-8 space-y-4">
            {/* Address Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3">
              <form onSubmit={handleHexJump} className="flex items-center gap-2">
                <label className="text-xs font-medium text-slate-600">Offset:</label>
                <input
                  type="text"
                  value={offsetInput}
                  onChange={(e) => setOffsetInput(e.target.value)}
                  className="w-32 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1.5 font-mono text-xs text-slate-900 focus:border-sky-500 focus:bg-white focus:outline-none"
                  placeholder="0x00E678"
                />
                <button
                  type="submit"
                  className="rounded-md bg-sky-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap"
                >
                  Jump
                </button>
              </form>

              <div className="flex items-center gap-2">
                <select
                  value={hexLength}
                  onChange={(e) => setHexLength(Number(e.target.value))}
                  className="rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700"
                >
                  <option value={128}>128 bytes</option>
                  <option value={256}>256 bytes</option>
                  <option value={512}>512 bytes</option>
                  <option value={1024}>1024 bytes</option>
                </select>
                <button
                  type="button"
                  onClick={() => stepHex(-hexLength)}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Prev
                </button>
                <button
                  type="button"
                  onClick={() => stepHex(hexLength)}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs text-slate-700 hover:bg-slate-50"
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            {/* Hex Table */}
            <div className="rounded-lg border border-slate-200 bg-slate-950 p-4 text-slate-100 overflow-x-auto">
              {hexLoading ? (
                <div className="py-12 text-center font-mono text-xs text-slate-400">
                  Reading ROM slice...
                </div>
              ) : (
                <table className="w-full font-mono text-xs tabular-nums">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="pb-2 pr-4 text-left font-medium">Address</th>
                      <th className="pb-2 pr-4 text-left font-medium">
                        00 01 02 03 04 05 06 07 &nbsp;08 09 0A 0B 0C 0D 0E 0F
                      </th>
                      <th className="pb-2 text-left font-medium">ASCII</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-900">
                    {hexData?.rows.map((r) => (
                      <tr key={r.address} className="hover:bg-slate-900/80">
                        <td className="py-1 pr-4 text-sky-400 whitespace-nowrap">{r.address}</td>
                        <td className="py-1 pr-4 whitespace-nowrap">
                          {r.bytes.map((b, idx) => (
                            <span
                              key={idx}
                              className={`${idx === 8 ? 'ml-2' : ''} mr-1.5 ${
                                b === 0 ? 'text-slate-600' : b === 0xff ? 'text-amber-400' : 'text-slate-100'
                              }`}
                            >
                              {b.toString(16).toUpperCase().padStart(2, '0')}
                            </span>
                          ))}
                        </td>
                        <td className="py-1 text-emerald-300/90 whitespace-nowrap">{r.ascii}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Right Sidebar: Binary Search & Region Cross-References */}
          <div className="lg:col-span-4 space-y-4">
            <section className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
              <h3 className="text-sm font-semibold text-slate-900">Search ROM Binary</h3>
              <form onSubmit={handleRomSearch} className="space-y-2">
                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => setSearchMode('ascii')}
                    className={`rounded px-2.5 py-1 text-xs font-medium ${
                      searchMode === 'ascii'
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    ASCII
                  </button>
                  <button
                    type="button"
                    onClick={() => setSearchMode('hex')}
                    className={`rounded px-2.5 py-1 text-xs font-medium ${
                      searchMode === 'hex'
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    Hex Bytes
                  </button>
                </div>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="pointer-events-none absolute top-2.5 left-2.5 h-3.5 w-3.5 text-slate-400" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder={searchMode === 'ascii' ? 'e.g. 8CMCKRN5' : 'e.g. 40 40 40 4D'}
                      className="w-full rounded-md border border-slate-200 bg-slate-50 py-1.5 pr-2.5 pl-8 font-mono text-xs focus:border-sky-500 focus:bg-white focus:outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Find
                  </button>
                </div>
                {searchError && <p className="text-xs text-rose-600">{searchError}</p>}
              </form>

              {searchResults.length > 0 && (
                <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 border-t border-slate-100 pt-2">
                  {searchResults.map((m, idx) => (
                    <button
                      key={`${m.address}-${idx}`}
                      type="button"
                      onClick={() => {
                        setOffsetInput(m.address);
                        setActiveOffset(m.address);
                      }}
                      className="flex w-full items-center justify-between gap-2 py-1.5 text-left hover:bg-slate-50 px-1 rounded"
                    >
                      <span className="font-mono text-xs font-semibold text-sky-700">
                        {m.address}
                      </span>
                      <span className="truncate font-mono text-[11px] text-slate-500">
                        {m.preview}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
              <h3 className="text-sm font-semibold text-slate-900">
                Overlapping IDA Functions & Data
              </h3>
              {hexData?.overlappingFunctions.length ? (
                <div className="space-y-1.5">
                  <div className="text-xs font-medium text-slate-500">Functions in range</div>
                  {hexData.overlappingFunctions.map((f) => (
                    <div
                      key={f.startEa}
                      className="flex items-center justify-between rounded bg-slate-50 px-2.5 py-1.5 text-xs"
                    >
                      <span className="font-mono font-medium text-slate-900 truncate">{f.name}</span>
                      <span className="font-mono text-slate-500 shrink-0 ml-2">
                        {f.startEa} ({f.size}B)
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500">No functions overlap this byte window.</p>
              )}

              {hexData?.dataItems.length ? (
                <div className="space-y-1.5 pt-2 border-t border-slate-100">
                  <div className="text-xs font-medium text-slate-500">
                    Data inventory entries ({hexData.dataItems.length})
                  </div>
                  <div className="max-h-56 overflow-y-auto divide-y divide-slate-100">
                    {hexData.dataItems.map((d) => (
                      <div key={d.startEa} className="py-1.5 text-xs">
                        <div className="flex items-center justify-between font-mono">
                          <span className="text-sky-700">{d.startEa}</span>
                          <span className="text-slate-500">
                            {d.name || d.kind} ({d.size}B)
                          </span>
                        </div>
                        {d.disasm && (
                          <div className="truncate font-mono text-[11px] text-slate-600">
                            {d.disasm}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </section>
          </div>
        </div>
      )}

      {/* Mode 2: Interactive 1D/2D Table & Curve Lab */}
      {mode === 'table' && (
        <div className="space-y-5">
          {/* Presets & Config */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 mr-1">Verified Presets:</span>
              {TABLE_PRESETS.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className="rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-sky-50 hover:border-sky-300 hover:text-sky-800 whitespace-nowrap"
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7 pt-2 border-t border-slate-100">
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Data Addr</label>
                <input
                  type="text"
                  value={tblAddr}
                  onChange={(e) => setTblAddr(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Rows (Y)</label>
                <input
                  type="number"
                  min={1}
                  max={32}
                  value={tblRows}
                  onChange={(e) => setTblRows(Number(e.target.value))}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Cols (X)</label>
                <input
                  type="number"
                  min={1}
                  max={32}
                  value={tblCols}
                  onChange={(e) => setTblCols(Number(e.target.value))}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Storage</label>
                <select
                  value={tblStorage}
                  onChange={(e) => setTblStorage(e.target.value as 'uint8' | 'uint16')}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs bg-white"
                >
                  <option value="uint8">UBYTE (uint8)</option>
                  <option value="uint16">UWORD (uint16)</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Endian</label>
                <select
                  value={tblEndian}
                  onChange={(e) => setTblEndian(e.target.value as 'big' | 'little')}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs bg-white"
                >
                  <option value="big">Big-Endian</option>
                  <option value="little">Little-Endian</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Scale Mult</label>
                <input
                  type="text"
                  value={tblMult}
                  onChange={(e) => setTblMult(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Offset</label>
                <input
                  type="text"
                  value={tblOffset}
                  onChange={(e) => setTblOffset(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-7 items-end">
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Y-Axis Addr</label>
                <input
                  type="text"
                  value={yAxisAddr}
                  onChange={(e) => setYAxisAddr(e.target.value)}
                  placeholder="Optional"
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">Y Type / Mult</label>
                <div className="mt-1 flex gap-1">
                  <select
                    value={yAxisStorage}
                    onChange={(e) => setYAxisStorage(e.target.value as 'uint8' | 'uint16')}
                    className="w-1/2 rounded border border-slate-200 px-1 py-1.5 text-xs bg-white"
                  >
                    <option value="uint8">u8</option>
                    <option value="uint16">u16</option>
                  </select>
                  <input
                    type="text"
                    value={yAxisMult}
                    onChange={(e) => setYAxisMult(e.target.value)}
                    className="w-1/2 rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">X-Axis Addr</label>
                <input
                  type="text"
                  value={xAxisAddr}
                  onChange={(e) => setXAxisAddr(e.target.value)}
                  placeholder="Optional"
                  className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-500">X Type / Mult</label>
                <div className="mt-1 flex gap-1">
                  <select
                    value={xAxisStorage}
                    onChange={(e) => setXAxisStorage(e.target.value as 'uint8' | 'uint16')}
                    className="w-1/2 rounded border border-slate-200 px-1 py-1.5 text-xs bg-white"
                  >
                    <option value="uint8">u8</option>
                    <option value="uint16">u16</option>
                  </select>
                  <input
                    type="text"
                    value={xAxisMult}
                    onChange={(e) => setXAxisMult(e.target.value)}
                    className="w-1/2 rounded border border-slate-200 px-2 py-1.5 font-mono text-xs"
                  />
                </div>
              </div>
              <div className="lg:col-span-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowRaw((v) => !v)}
                  className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap"
                >
                  {showRaw ? 'Show Scaled Values' : 'Show Raw Hex'}
                </button>
                <button
                  type="button"
                  onClick={loadTable}
                  className="rounded-md bg-sky-700 px-4 py-1.5 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap"
                >
                  Decode ROM Table
                </button>
              </div>
            </div>
          </div>

          {tableError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
              {tableError}
            </div>
          )}

          {tableData && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="lg:col-span-9 rounded-lg border border-slate-200 bg-white p-4 overflow-x-auto">
                <div className="mb-3 flex items-center justify-between text-xs text-slate-500">
                  <span>
                    Base <span className="font-mono font-semibold text-slate-900">{tableData.address}</span> ·{' '}
                    {tableData.rows}×{tableData.cols} {tableData.storage} ({tableData.endian})
                  </span>
                  <span className="font-mono tabular-nums">
                    Range: {tableData.minVal} to {tableData.maxVal}
                  </span>
                </div>

                <table className="border-collapse font-mono text-[11px] tabular-nums">
                  <thead>
                    <tr>
                      <th className="border border-slate-200 bg-slate-100 px-2 py-1.5 text-slate-500">
                        Y \ X
                      </th>
                      {Array.from({ length: tableData.cols }).map((_, c) => (
                        <th
                          key={c}
                          className="border border-slate-200 bg-slate-100 px-2 py-1.5 text-right font-semibold text-slate-700"
                        >
                          {tableData.xAxis ? tableData.xAxis[c] : `X${c}`}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.scaledMatrix.map((rowVals, r) => (
                      <tr key={r}>
                        <th className="border border-slate-200 bg-slate-100 px-2 py-1 text-right font-semibold text-slate-700">
                          {tableData.yAxis ? tableData.yAxis[r] : `Y${r}`}
                        </th>
                        {rowVals.map((val, c) => {
                          const raw = tableData.rawMatrix[r][c];
                          return (
                            <td
                              key={c}
                              title={`Raw: ${raw} (0x${raw.toString(16).toUpperCase()}) | Scaled: ${val}`}
                              className={`border border-slate-200 px-2 py-1 text-right ${cellHeatBg(
                                val,
                                tableData.minVal,
                                tableData.maxVal
                              )}`}
                            >
                              {showRaw
                                ? `0x${raw.toString(16).toUpperCase().padStart(tableData.storage === 'uint16' ? 4 : 2, '0')}`
                                : val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="lg:col-span-3 space-y-4">
                <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-semibold text-slate-900">RomRaider XML Draft</h3>
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(generatedXmlSnippet).then(() => {
                          setXmlCopied(true);
                          setTimeout(() => setXmlCopied(false), 1800);
                        });
                      }}
                      className="text-xs font-medium text-sky-700 hover:text-sky-800"
                    >
                      {xmlCopied ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <pre className="overflow-x-auto rounded bg-slate-900 p-3 font-mono text-[11px] leading-relaxed text-slate-100">
                    {generatedXmlSnippet}
                  </pre>
                  <button
                    type="button"
                    onClick={() => {
                      setOffsetInput(tableData.address);
                      setActiveOffset(tableData.address);
                      setMode('hex');
                    }}
                    className="w-full rounded-md border border-slate-200 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Inspect Raw Hex Bytes
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
