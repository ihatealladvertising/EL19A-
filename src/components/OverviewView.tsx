import React from 'react';
import { ArrowUpRight, CheckCircle2, FileSpreadsheet, HardDrive, ShieldCheck } from 'lucide-react';
import type { ActiveSection, OverviewResponse, TablePreset } from '../types';

interface OverviewViewProps {
  data: OverviewResponse | null;
  loading: boolean;
  onNavigate: (section: ActiveSection) => void;
  onJumpHex: (addr: string) => void;
  onOpenWorkOrder: (woId: string) => void;
  onOpenPresetTable: (preset: TablePreset) => void;
}

const FEATURED_ROM_REGIONS: {
  label: string;
  address: string;
  detail: string;
  preset?: TablePreset;
}[] = [
  {
    label: 'Reset & Interrupt Vector Table',
    address: '0x000000',
    detail: 'SH7058 exception vectors & Poweron_Reset (0x0000264C)',
  },
  {
    label: 'Dashpot Scalar Pair (Drive / Neutral)',
    address: '0x00848A',
    detail: 'mDDSHPTD / mDDSHPTN UBYTE 0x43 (52.34% @ x*0.78125)',
  },
  {
    label: 'QDSPT Basic Value Curves (E678 / E688)',
    address: '0x00E678',
    detail: '16-point UBYTE airflow curves via sub_22E10',
    preset: {
      label: 'E678 QDSPT Basic Value (Drive)',
      address: '0xE678',
      rows: 16,
      cols: 1,
      storage: 'uint8',
      endian: 'big',
      mult: 2,
      offset: 0,
    },
  },
  {
    label: 'TVO Upper Limit Curves (F3D6 / F3DE)',
    address: '0x00F3D6',
    detail: '8-point UBYTE limiters with ROM axis F3C6 / F3CE',
    preset: {
      label: 'F3D6 TVO Upper Limit Main',
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
  },
  {
    label: '2D Calibration Maps (9C2E / CD56 / A552)',
    address: '0x00CD56',
    detail: '16x16 UWORD BE map with explicit axes E2C9 & FEC0',
    preset: {
      label: 'CD56 16x16 UWORD BE Map (WO64972)',
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
  },
  {
    label: 'Bulk RAM Copy & ADC Descriptors',
    address: '0x013B20',
    detail: '0x16CD0 -> FFFFB61C bulk copy & ADCR0_B/ADDR7H_B patterns',
  },
];

export const OverviewView: React.FC<OverviewViewProps> = ({
  data,
  loading,
  onNavigate,
  onJumpHex,
  onOpenWorkOrder,
  onOpenPresetTable,
}) => {
  if (loading || !data) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-36 rounded-lg border border-slate-200 bg-white" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((k) => (
            <div key={k} className="h-24 rounded-lg border border-slate-200 bg-white" />
          ))}
        </div>
      </div>
    );
  }

  const { project, counts, memoryMap, recentWorkOrders, workbookFiles } = data;

  return (
    <div className="space-y-6">
      {/* Target Identity Banner */}
      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span>{project.vehicle}</span>
              <span aria-hidden="true">·</span>
              <span className="font-mono">{project.cpu}</span>
              <span aria-hidden="true">·</span>
              <span className="font-mono">FID {project.fid}</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 text-balance">
              {project.name}
            </h1>
            <p className="max-w-3xl text-sm leading-relaxed text-slate-600">
              Live reverse-engineering workbench backed directly by the immutable 1 MiB{' '}
              <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-800">
                {project.romFile}
              </code>{' '}
              ROM binary, IDA Pro function and data exports, RomRaider XML fragment definitions,
              228 control work orders, and Master Reverse-Engineering Workbooks.
            </p>
          </div>

          <div className="flex shrink-0 flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => onNavigate('calibrations')}
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap shrink-0"
            >
              Inspect Calibrations
            </button>
            <button
              type="button"
              onClick={() => onJumpHex('0x00E678')}
              className="rounded-lg bg-sky-700 px-4 py-2 text-xs font-medium text-white hover:bg-sky-800 whitespace-nowrap shrink-0"
            >
              Open ROM Hex Explorer
            </button>
          </div>
        </div>

        {/* Cryptographic Verification Strip */}
        <div className="mt-5 grid grid-cols-1 gap-4 border-t border-slate-200 pt-4 md:grid-cols-3">
          <div className="flex items-start gap-2.5">
            <ShieldCheck
              className={`mt-0.5 h-4 w-4 shrink-0 ${
                project.md5Verified ? 'text-emerald-600' : 'text-amber-600'
              }`}
            />
            <div className="min-w-0">
              <div className="text-xs font-medium text-slate-700">
                ROM Binary Integrity ({project.md5Verified ? 'Verified Match' : 'Mismatch'})
              </div>
              <div className="truncate font-mono text-xs text-slate-500" title={project.romMd5}>
                MD5: {project.romMd5}
              </div>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <HardDrive className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
            <div className="min-w-0">
              <div className="text-xs font-medium text-slate-700">Binary Size & Base</div>
              <div className="font-mono text-xs text-slate-500">
                {project.romSizeBytes.toLocaleString()} bytes · Base 0x00000000
              </div>
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />
            <div className="min-w-0">
              <div className="text-xs font-medium text-slate-700">SHA-256 Digest</div>
              <div className="truncate font-mono text-xs text-slate-500" title={project.romSha256}>
                {project.romSha256}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Primary KPI Strip */}
      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <button
          type="button"
          onClick={() => onNavigate('functions')}
          className="rounded-lg border border-slate-200 bg-white p-4 text-left transition-colors hover:border-sky-300"
        >
          <div className="text-xs font-medium text-slate-500">Disassembled Functions</div>
          <div className="mt-1 font-mono text-2xl font-semibold text-slate-900 tabular-nums">
            {counts.functions.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500 tabular-nums">
            {counts.xrefs.toLocaleString()} cross-references
          </div>
        </button>

        <button
          type="button"
          onClick={() => onNavigate('work-orders')}
          className="rounded-lg border border-slate-200 bg-white p-4 text-left transition-colors hover:border-sky-300"
        >
          <div className="text-xs font-medium text-slate-500">Control Work Orders</div>
          <div className="mt-1 font-mono text-2xl font-semibold text-slate-900 tabular-nums">
            {counts.workOrders.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500">WO64828 through WO65055</div>
        </button>

        <button
          type="button"
          onClick={() => onNavigate('calibrations')}
          className="rounded-lg border border-slate-200 bg-white p-4 text-left transition-colors hover:border-sky-300"
        >
          <div className="text-xs font-medium text-slate-500">Calibrations & Leads</div>
          <div className="mt-1 font-mono text-2xl font-semibold text-slate-900 tabular-nums">
            {counts.xmlTables} XML / {counts.candidates} Reg
          </div>
          <div className="mt-1 text-xs text-slate-500 tabular-nums">
            {counts.openLeads} tracked open leads
          </div>
        </button>

        <button
          type="button"
          onClick={() => onNavigate('workbooks')}
          className="rounded-lg border border-slate-200 bg-white p-4 text-left transition-colors hover:border-sky-300"
        >
          <div className="text-xs font-medium text-slate-500">Data Inventory & Books</div>
          <div className="mt-1 font-mono text-2xl font-semibold text-slate-900 tabular-nums">
            {counts.dataItems.toLocaleString()}
          </div>
          <div className="mt-1 text-xs text-slate-500 tabular-nums">
            {counts.workbooks} XLSX master workbooks
          </div>
        </button>
      </section>

      {/* Two-column Memory Map & Key ROM Landmarks */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900">SH7058 Address Space</h2>
            <span className="font-mono text-xs text-slate-500">Big-Endian SH-2</span>
          </div>
          <div className="divide-y divide-slate-100">
            {memoryMap.map((seg) => (
              <div key={seg.name} className="flex items-center justify-between py-2.5 text-sm">
                <div>
                  <span className="font-semibold text-slate-900">{seg.name}</span>
                  <span className="ml-2 font-mono text-xs text-slate-500">
                    {seg.start} – {seg.end}
                  </span>
                </div>
                <span className="font-mono text-xs text-slate-700 tabular-nums">
                  {seg.size.toLocaleString()} B
                </span>
              </div>
            ))}
          </div>

          <h3 className="mt-5 mb-2 text-xs font-semibold text-slate-500">
            Quick-Jump ROM Landmarks
          </h3>
          <div className="divide-y divide-slate-100">
            {FEATURED_ROM_REGIONS.map((reg) => (
              <div
                key={reg.address}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium text-slate-900 truncate">{reg.label}</div>
                  <div className="text-xs text-slate-500 truncate">{reg.detail}</div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {reg.preset && (
                    <button
                      type="button"
                      onClick={() => onOpenPresetTable(reg.preset!)}
                      className="rounded border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 whitespace-nowrap"
                    >
                      Table Lab
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => onJumpHex(reg.address)}
                    className="rounded bg-slate-100 px-2.5 py-1 font-mono text-xs font-medium text-sky-700 hover:bg-sky-50 whitespace-nowrap"
                  >
                    {reg.address}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Recent Work Orders + Workbooks */}
        <div className="space-y-6">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">Latest Work Orders</h2>
              <button
                type="button"
                onClick={() => onNavigate('work-orders')}
                className="inline-flex items-center gap-1 text-xs font-medium text-sky-700 hover:text-sky-800"
              >
                View all {counts.workOrders}
                <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="divide-y divide-slate-100">
              {recentWorkOrders.slice(0, 6).map((wo) => (
                <button
                  key={wo.id}
                  type="button"
                  onClick={() => onOpenWorkOrder(wo.id)}
                  className="flex w-full items-start justify-between gap-3 py-2.5 text-left hover:bg-slate-50 px-1 rounded transition-colors"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-sky-700">
                        {wo.id}
                      </span>
                      <span className="truncate text-sm font-medium text-slate-900">
                        {wo.title.replace(/^WO\d+\s*[—-]\s*/i, '')}
                      </span>
                    </div>
                    <p className="mt-0.5 line-clamp-1 text-xs text-slate-500">{wo.objective}</p>
                  </div>
                  <span className="shrink-0 text-xs text-slate-500 whitespace-nowrap">
                    {wo.status.split('—')[0].trim()}
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">
                Engineering Workbooks (.xlsx)
              </h2>
              <button
                type="button"
                onClick={() => onNavigate('workbooks')}
                className="inline-flex items-center gap-1 text-xs font-medium text-sky-700 hover:text-sky-800"
              >
                Browse sheets
                <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="divide-y divide-slate-100">
              {workbookFiles.map((wb) => (
                <div
                  key={`${wb.dir}/${wb.name}`}
                  className="flex items-center justify-between gap-3 py-2 text-xs"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <FileSpreadsheet className="h-4 w-4 shrink-0 text-emerald-600" />
                    <span className="truncate font-medium text-slate-800" title={wb.name}>
                      {wb.name}
                    </span>
                  </div>
                  <span className="shrink-0 font-mono text-slate-500 tabular-nums">
                    {(wb.size / 1024).toFixed(0)} KB
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
