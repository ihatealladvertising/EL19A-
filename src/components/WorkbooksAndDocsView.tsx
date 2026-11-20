import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { MarkdownView } from './MarkdownView';

interface WorkbooksAndDocsViewProps {
  onJumpHex: (addr: string) => void;
}

interface WorkbookFile {
  id: string;
  dir: string;
  name: string;
  size: number;
}

interface DocFile {
  path: string;
  name: string;
  size: number;
}

export const WorkbooksAndDocsView: React.FC<WorkbooksAndDocsViewProps> = ({ onJumpHex }) => {
  const [subTab, setSubTab] = useState<'workbooks' | 'docs'>('workbooks');

  // Workbooks state
  const [workbooks, setWorkbooks] = useState<WorkbookFile[]>([]);
  const [selectedWb, setSelectedWb] = useState<string>('');
  const [sheets, setSheets] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [sheetFilter, setSheetFilter] = useState('');
  const [rowQuery, setRowQuery] = useState('');
  const [rowOffset, setRowOffset] = useState(0);
  const [rows, setRows] = useState<any[][]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [wbLoading, setWbLoading] = useState(false);

  // Docs state
  const [docs, setDocs] = useState<DocFile[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<string>('README.md');
  const [docContent, setDocContent] = useState<string>('');

  useEffect(() => {
    fetch('/api/workbooks')
      .then((r) => r.json())
      .then((d) => {
        const list: WorkbookFile[] = d.workbooks || [];
        setWorkbooks(list);
        if (list.length > 0) setSelectedWb(list[0].id);
      });

    fetch('/api/docs')
      .then((r) => r.json())
      .then((d) => {
        const list: DocFile[] = d.docs || [];
        setDocs(list);
      });
  }, []);

  useEffect(() => {
    if (!selectedWb) return;
    setWbLoading(true);
    fetch(`/api/workbooks/sheets?id=${encodeURIComponent(selectedWb)}`)
      .then((r) => r.json())
      .then((d) => {
        const sList: string[] = d.sheets || [];
        setSheets(sList);
        setSelectedSheet(sList[0] || '');
        setRowOffset(0);
        setWbLoading(false);
      })
      .catch(() => setWbLoading(false));
  }, [selectedWb]);

  useEffect(() => {
    if (!selectedWb || !selectedSheet) return;
    setWbLoading(true);
    const params = new URLSearchParams({
      id: selectedWb,
      sheet: selectedSheet,
      limit: '100',
      offset: String(rowOffset),
    });
    if (rowQuery.trim()) params.set('q', rowQuery.trim());
    fetch(`/api/workbooks/sheet-data?${params.toString()}`)
      .then((r) => r.json())
      .then((d) => {
        setRows(d.rows || []);
        setTotalRows(d.totalRows || 0);
        setWbLoading(false);
      })
      .catch(() => setWbLoading(false));
  }, [selectedWb, selectedSheet, rowOffset, rowQuery]);

  useEffect(() => {
    if (subTab !== 'docs' || !selectedDoc) return;
    fetch(`/api/docs/content?path=${encodeURIComponent(selectedDoc)}`)
      .then((r) => r.json())
      .then((d) => setDocContent(d.content || ''));
  }, [subTab, selectedDoc]);

  const filteredSheets = sheets.filter((s) =>
    s.toLowerCase().includes(sheetFilter.trim().toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setSubTab('workbooks')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              subTab === 'workbooks'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Master Workbooks (.xlsx)
          </button>
          <button
            type="button"
            onClick={() => setSubTab('docs')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
              subTab === 'docs'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Protocol & Playbooks
          </button>
        </div>

        {subTab === 'workbooks' && (
          <select
            value={selectedWb}
            onChange={(e) => setSelectedWb(e.target.value)}
            className="max-w-md rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800"
          >
            {workbooks.map((wb) => (
              <option key={wb.id} value={wb.id}>
                {wb.name} ({(wb.size / 1024).toFixed(0)} KB)
              </option>
            ))}
          </select>
        )}
      </div>

      {subTab === 'workbooks' ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-3 rounded-lg border border-slate-200 bg-white overflow-hidden">
            <div className="border-b border-slate-200 p-3">
              <input
                type="text"
                value={sheetFilter}
                onChange={(e) => setSheetFilter(e.target.value)}
                placeholder={`Filter ${sheets.length} sheets...`}
                className="w-full rounded border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs focus:border-sky-500 focus:bg-white focus:outline-none"
              />
            </div>
            <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-100">
              {filteredSheets.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    setSelectedSheet(s);
                    setRowOffset(0);
                  }}
                  className={`block w-full px-3 py-2 text-left text-xs transition-colors truncate ${
                    s === selectedSheet
                      ? 'bg-sky-50 font-semibold text-sky-800'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  title={s}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-9 rounded-lg border border-slate-200 bg-white overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50 px-4 py-2.5">
              <div>
                <span className="text-xs font-semibold text-slate-900">{selectedSheet}</span>
                <span className="ml-2 text-xs text-slate-500 tabular-nums">
                  ({totalRows.toLocaleString()} rows)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute top-2 left-2.5 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    value={rowQuery}
                    onChange={(e) => {
                      setRowQuery(e.target.value);
                      setRowOffset(0);
                    }}
                    placeholder="Filter rows..."
                    className="w-44 rounded border border-slate-200 bg-white py-1 pr-2 pl-7 text-xs"
                  />
                </div>
                <button
                  type="button"
                  disabled={rowOffset === 0}
                  onClick={() => setRowOffset((o) => Math.max(0, o - 100))}
                  className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  disabled={rowOffset + 100 >= totalRows}
                  onClick={() => setRowOffset((o) => o + 100)}
                  className="rounded border border-slate-200 bg-white p-1 disabled:opacity-40"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="max-h-[600px] overflow-auto">
              {wbLoading ? (
                <div className="p-8 text-center text-xs text-slate-500">Parsing sheet...</div>
              ) : rows.length > 0 ? (
                <table className="w-full text-left text-xs">
                  <tbody className="divide-y divide-slate-100">
                    {rows.map((r, rIdx) => {
                      const isHeader = rowOffset === 0 && rIdx === 0;
                      return (
                        <tr
                          key={rIdx}
                          className={
                            isHeader
                              ? 'bg-slate-100 font-semibold text-slate-800'
                              : 'hover:bg-slate-50'
                          }
                        >
                          {r.slice(0, 18).map((cell, cIdx) => (
                            <td
                              key={cIdx}
                              className="max-w-xs truncate border-r border-slate-100 px-3 py-1.5 font-mono text-[11px]"
                              title={String(cell ?? '')}
                            >
                              {String(cell ?? '')}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">No rows in this sheet.</div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4 rounded-lg border border-slate-200 bg-white divide-y divide-slate-100">
            <div className="px-4 py-2.5 text-xs font-semibold text-slate-500">
              Repository Documentation
            </div>
            {docs.map((d) => (
              <button
                key={d.path}
                type="button"
                onClick={() => setSelectedDoc(d.path)}
                className={`flex w-full items-center justify-between gap-2 px-4 py-2.5 text-left text-xs transition-colors ${
                  selectedDoc === d.path
                    ? 'bg-sky-50 font-semibold text-sky-800'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span className="truncate">{d.path}</span>
                <span className="shrink-0 font-mono text-[11px] text-slate-400 tabular-nums">
                  {(d.size / 1024).toFixed(1)} KB
                </span>
              </button>
            ))}
          </div>
          <div className="lg:col-span-8 rounded-lg border border-slate-200 bg-white p-6">
            <MarkdownView content={docContent} onSelectAddress={onJumpHex} />
          </div>
        </div>
      )}
    </div>
  );
};
