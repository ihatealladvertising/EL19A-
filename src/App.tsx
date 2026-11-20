import React, { useEffect, useState } from 'react';
import {
  Binary,
  BookOpen,
  ClipboardList,
  Cpu,
  LayoutDashboard,
  Menu,
  Sliders,
  X,
} from 'lucide-react';
import type { ActiveSection, OverviewResponse, TablePreset } from './types';
import { OverviewView } from './components/OverviewView';
import { CalibrationsView } from './components/CalibrationsView';
import { RomExplorerView } from './components/RomExplorerView';
import { WorkOrdersView } from './components/WorkOrdersView';
import { FunctionsAndDataView } from './components/FunctionsAndDataView';
import { WorkbooksAndDocsView } from './components/WorkbooksAndDocsView';

const NAV_ITEMS: { id: ActiveSection; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'calibrations', label: 'Calibrations', icon: Sliders },
  { id: 'rom', label: 'ROM Explorer', icon: Binary },
  { id: 'work-orders', label: 'Work Orders', icon: ClipboardList },
  { id: 'functions', label: 'Functions', icon: Cpu },
  { id: 'workbooks', label: 'Workbooks', icon: BookOpen },
];

export function App() {
  const [section, setSection] = useState<ActiveSection>('overview');
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Cross-view navigation state
  const [romAddress, setRomAddress] = useState('0x00E678');
  const [romMode, setRomMode] = useState<'hex' | 'table'>('hex');
  const [tablePreset, setTablePreset] = useState<TablePreset | null>(null);
  const [selectedWoId, setSelectedWoId] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/overview')
      .then((r) => r.json())
      .then((d) => {
        setOverview(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleJumpHex = (addr: string) => {
    setRomAddress(addr);
    setRomMode('hex');
    setSection('rom');
    setMobileNavOpen(false);
  };

  const handleOpenPresetTable = (preset: TablePreset) => {
    setTablePreset(preset);
    setRomMode('table');
    setSection('rom');
    setMobileNavOpen(false);
  };

  const handleOpenWorkOrder = (woId: string) => {
    setSelectedWoId(woId);
    setSection('work-orders');
    setMobileNavOpen(false);
  };

  const handleNavigate = (next: ActiveSection) => {
    setSection(next);
    setMobileNavOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top Bar Contract: [Brand] — [5 single-line nav links] — [1 primary action] */}
      <header className="sticky top-0 z-30 flex items-center justify-between gap-8 border-b border-slate-200 bg-white px-4 py-3 lg:px-6">
        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={() => setMobileNavOpen((v) => !v)}
            className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden"
            aria-label="Toggle navigation menu"
          >
            {mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <button
            type="button"
            onClick={() => handleNavigate('overview')}
            className="text-base font-bold tracking-tight text-slate-900 whitespace-nowrap shrink-0"
          >
            EL19A Workbench
          </button>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
          {NAV_ITEMS.slice(0, 5).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleNavigate(item.id)}
              className={`transition-colors whitespace-nowrap shrink-0 py-1 border-b-2 ${
                section === item.id
                  ? 'border-sky-700 text-slate-900'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center shrink-0">
          <button
            type="button"
            onClick={() => {
              setRomMode('table');
              setSection('rom');
            }}
            className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800 transition-colors whitespace-nowrap shrink-0"
          >
            Open Table Lab
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar Navigation (Desktop) */}
        <aside className="hidden lg:flex lg:w-60 lg:shrink-0 lg:flex-col border-r border-slate-200 bg-white p-4 justify-between">
          <div className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = section === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleNavigate(item.id)}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                    active
                      ? 'bg-sky-50 text-sky-800'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <Icon className={`h-4 w-4 shrink-0 ${active ? 'text-sky-700' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {overview && (
            <div className="border-t border-slate-200 pt-4 text-xs text-slate-500 space-y-1">
              <div className="font-semibold text-slate-700">Target ROM</div>
              <div className="font-mono">{overview.project.romFile}</div>
              <div className="font-mono">SH7058 · {overview.project.fid}</div>
              <div className="font-mono tabular-nums">
                {overview.counts.workOrders} WOs · {overview.counts.functions} fns
              </div>
            </div>
          )}
        </aside>

        {/* Mobile Drawer */}
        {mobileNavOpen && (
          <div className="fixed inset-0 z-40 flex lg:hidden">
            <div
              className="fixed inset-0 bg-slate-900/30"
              onClick={() => setMobileNavOpen(false)}
            />
            <nav className="relative z-50 w-64 bg-white p-4 border-r border-slate-200 space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = section === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleNavigate(item.id)}
                    className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium ${
                      active ? 'bg-sky-50 text-sky-800' : 'text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        )}

        {/* Main Content Viewport */}
        <main className="flex-1 min-w-0 p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-[1240px]">
            {section === 'overview' && (
              <OverviewView
                data={overview}
                loading={loading}
                onNavigate={handleNavigate}
                onJumpHex={handleJumpHex}
                onOpenWorkOrder={handleOpenWorkOrder}
                onOpenPresetTable={handleOpenPresetTable}
              />
            )}
            {section === 'calibrations' && (
              <CalibrationsView
                onJumpHex={handleJumpHex}
                onOpenPresetTable={handleOpenPresetTable}
              />
            )}
            {section === 'rom' && (
              <RomExplorerView
                initialAddress={romAddress}
                initialPreset={tablePreset}
                initialMode={romMode}
              />
            )}
            {section === 'work-orders' && (
              <WorkOrdersView
                selectedWoId={selectedWoId}
                onSelectWo={setSelectedWoId}
                onJumpHex={handleJumpHex}
              />
            )}
            {section === 'functions' && <FunctionsAndDataView onJumpHex={handleJumpHex} />}
            {section === 'workbooks' && <WorkbooksAndDocsView onJumpHex={handleJumpHex} />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
