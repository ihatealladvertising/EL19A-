import express from 'express';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const XLSX = require('xlsx');

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;
const PORT = Number(process.env.PORT || 3000);

// ---------------------------------------------------------------------------
// CSV Helper (RFC-4180 aware)
// ---------------------------------------------------------------------------
function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (i + 1 < line.length && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        current += ch;
      }
    } else {
      if (ch === '"') {
        inQuotes = true;
      } else if (ch === ',') {
        result.push(current);
        current = '';
      } else if (ch !== '\r') {
        current += ch;
      }
    }
  }
  result.push(current);
  return result;
}

function parseHexAddress(val: string | undefined | null): number | null {
  if (!val) return null;
  const cleaned = val.trim().replace(/^0x/i, '');
  if (!/^[0-9a-fA-F]+$/.test(cleaned)) return null;
  return parseInt(cleaned, 16);
}

function formatHex(addr: number, pad = 6): string {
  return '0x' + addr.toString(16).toUpperCase().padStart(pad, '0');
}

// ---------------------------------------------------------------------------
// Load Core Immutable Repository Assets
// ---------------------------------------------------------------------------
const ROM_PATH = path.join(ROOT, 'VERSA f501.bin');
const romBuffer: Buffer = fs.existsSync(ROM_PATH)
  ? fs.readFileSync(ROM_PATH)
  : Buffer.alloc(0);

const romMd5 = romBuffer.length
  ? crypto.createHash('md5').update(romBuffer).digest('hex')
  : '';
const romSha256 = romBuffer.length
  ? crypto.createHash('sha256').update(romBuffer).digest('hex')
  : '';

interface FunctionEntry {
  startEa: string;
  startNum: number;
  endEa: string;
  endNum: number;
  size: number;
  name: string;
  segment: string;
  ranges: string;
  callers: string[];
  callees: string[];
  callerCount: number;
  calleeCount: number;
}

interface DataInventoryEntry {
  startEa: string;
  startNum: number;
  endEa: string;
  endNum: number;
  size: number;
  segment: string;
  name: string;
  kind: string;
  hexPreview: string;
  disasm: string;
  comment: string;
  xrefs: string[];
  targetEa: string;
}

interface WorkOrderSummary {
  id: string;
  num: number;
  title: string;
  status: string;
  parent: string;
  target: string;
  objective: string;
  closeout: string;
  addresses: string[];
  lineCount: number;
}

interface XmlScaling {
  name: string;
  units: string;
  expression: string;
  toByte: string;
  format: string;
  storagetype: string;
  endian: string;
}

interface XmlTable {
  name: string;
  category: string;
  storageaddress: string;
  addressNum: number;
  type: string;
  scalingName: string;
  scaling?: XmlScaling;
  sizey: number;
  sizex: number;
  axisName?: string;
  axisScaling?: string;
  axisData?: number[];
  commentNote?: string;
  rawBytes: number[];
  scaledValues: number[];
}

// Lazy caches
let cachedFunctions: FunctionEntry[] | null = null;
let cachedDataInventory: DataInventoryEntry[] | null = null;
let cachedWorkOrders: WorkOrderSummary[] | null = null;
const workbookCache = new Map<string, any>();

function getFunctions(): FunctionEntry[] {
  if (cachedFunctions) return cachedFunctions;
  const filePath = path.join(ROOT, 'EVIDENCE', 'EL19A_Function_Index.csv');
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, 'utf-8');
  const lines = raw.split('\n');
  const list: FunctionEntry[] = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    const cols = parseCsvLine(line);
    if (cols.length < 5) continue;
    const startEa = cols[0].trim();
    const endEa = cols[1].trim();
    const startNum = parseHexAddress(startEa) ?? 0;
    const endNum = parseHexAddress(endEa) ?? 0;
    const size = parseInt(cols[2], 10) || 0;
    const name = cols[3].trim();
    const segment = cols[4].trim();
    const ranges = (cols[6] || '').trim();
    const callers = (cols[9] || '')
      .split(';')
      .map((s) => s.trim())
      .filter(Boolean);
    const callees = (cols[10] || '')
      .split(';')
      .map((s) => s.trim())
      .filter(Boolean);
    list.push({
      startEa,
      startNum,
      endEa,
      endNum,
      size,
      name,
      segment,
      ranges,
      callers,
      callees,
      callerCount: callers.length,
      calleeCount: callees.length,
    });
  }
  cachedFunctions = list;
  return list;
}

function getDataInventory(): DataInventoryEntry[] {
  if (cachedDataInventory) return cachedDataInventory;
  const filePath = path.join(ROOT, 'EVIDENCE', 'EL19A_Data_Inventory.csv');
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, 'utf-8');
  const lines = raw.split('\n');
  const list: DataInventoryEntry[] = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    const cols = parseCsvLine(line);
    if (cols.length < 6) continue;
    const startEa = cols[0].trim();
    const endEa = cols[1].trim();
    const startNum = parseHexAddress(startEa) ?? 0;
    const endNum = parseHexAddress(endEa) ?? 0;
    const size = parseInt(cols[2], 10) || 0;
    const segment = cols[3].trim();
    const name = (cols[4] || '').trim();
    const kind = (cols[5] || '').trim();
    const hexPreview = (cols[6] || '').trim();
    const disasm = (cols[7] || '').trim();
    const comment = (cols[9] || cols[8] || '').trim();
    const xrefs = (cols[10] || '')
      .split(';')
      .map((s) => s.trim())
      .filter(Boolean);
    const targetEa = (cols[11] || '').trim();
    list.push({
      startEa,
      startNum,
      endEa,
      endNum,
      size,
      segment,
      name,
      kind,
      hexPreview,
      disasm,
      comment,
      xrefs,
      targetEa,
    });
  }
  cachedDataInventory = list;
  return list;
}

function getWorkOrders(): WorkOrderSummary[] {
  if (cachedWorkOrders) return cachedWorkOrders;
  const controlDir = path.join(ROOT, 'CONTROL');
  if (!fs.existsSync(controlDir)) return [];
  const files = fs
    .readdirSync(controlDir)
    .filter((f) => /^WO\d+\.md$/i.test(f));

  const items: WorkOrderSummary[] = files.map((file) => {
    const id = file.replace(/\.md$/i, '');
    const num = parseInt(id.replace(/\D/g, ''), 10) || 0;
    const content = fs.readFileSync(path.join(controlDir, file), 'utf-8');
    const lines = content.split(/\r?\n/);

    const h1 = lines.find((l) => l.startsWith('# ')) || `# ${id}`;
    const title = h1.replace(/^#\s*/, '').trim();

    const statusLine =
      lines.find((l) => /\*\*Status:\*\*/i.test(l)) ||
      lines.find((l) => /^Status:/i.test(l)) ||
      '';
    let status = statusLine
      .replace(/.*\*\*Status:\*\*\s*/i, '')
      .replace(/^Status:\s*/i, '')
      .trim();
    if (!status) {
      const closeLine = lines.find((l) => /COMPLETE|PARTIAL|CANCELLED|CLOSED/i.test(l));
      status = closeLine ? 'RECORDED' : 'ARCHIVED';
    }

    const parentLine = lines.find((l) => /\*\*Parent:\*\*/i.test(l)) || '';
    const parent = parentLine.replace(/.*\*\*Parent:\*\*\s*/i, '').trim();

    const targetLine = lines.find((l) => /\*\*Target:\*\*/i.test(l)) || '';
    const target = targetLine.replace(/.*\*\*Target:\*\*\s*/i, '').trim();

    // Extract ## Objective section
    let objective = '';
    const objIdx = lines.findIndex((l) => /^##\s+Objective/i.test(l));
    if (objIdx !== -1) {
      const collected: string[] = [];
      for (let i = objIdx + 1; i < lines.length; i++) {
        if (/^##\s+/.test(lines[i])) break;
        if (lines[i].trim()) collected.push(lines[i].trim());
        if (collected.length >= 3) break;
      }
      objective = collected.join(' ');
    } else {
      objective = lines
        .slice(1, 10)
        .filter((l) => l.trim() && !l.startsWith('**'))
        .slice(0, 2)
        .join(' ');
    }

    // Extract ## Closeout section
    let closeout = '';
    const closeIdx = lines.findIndex((l) => /^##\s+Closeout/i.test(l));
    if (closeIdx !== -1) {
      closeout = lines
        .slice(closeIdx + 1, closeIdx + 4)
        .map((l) => l.trim())
        .filter(Boolean)
        .join(' ');
    }

    // Extract notable hex addresses (limit to 12)
    const addrMatches = content.match(/\b(?:0x[0-9A-Fa-f]{4,8}|FFFF[0-9A-Fa-f]{4})\b/g) || [];
    const addresses = Array.from(new Set(addrMatches.map((a) => a.toUpperCase()))).slice(0, 12);

    return {
      id,
      num,
      title,
      status,
      parent,
      target,
      objective: objective.slice(0, 320),
      closeout,
      addresses,
      lineCount: lines.length,
    };
  });

  items.sort((a, b) => b.num - a.num);
  cachedWorkOrders = items;
  return items;
}

function evalExpression(expr: string, x: number): number {
  const clean = expr.replace(/\s+/g, '');
  if (clean === 'x') return x;
  const mulMatch = clean.match(/^x\*([0-9.]+)$/);
  if (mulMatch) return x * parseFloat(mulMatch[1]);
  const divMatch = clean.match(/^x\/([0-9.]+)$/);
  if (divMatch) return x / parseFloat(divMatch[1]);
  const subMatch = clean.match(/^x-([0-9.]+)$/);
  if (subMatch) return x - parseFloat(subMatch[1]);
  const addMatch = clean.match(/^x\+([0-9.]+)$/);
  if (addMatch) return x + parseFloat(addMatch[1]);
  return x;
}

function parseXmlTables(): { scalings: XmlScaling[]; tables: XmlTable[] } {
  const xmlPath = path.join(ROOT, 'EVIDENCE', 'EL19A_ETC_Dashpot_Limiters_fragment-2.xml');
  if (!fs.existsSync(xmlPath)) return { scalings: [], tables: [] };
  const xml = fs.readFileSync(xmlPath, 'utf-8');

  const scalings: XmlScaling[] = [];
  const scalingRegex = /<scaling\s+([^>]+?)\/>/g;
  let m: RegExpExecArray | null;
  while ((m = scalingRegex.exec(xml)) !== null) {
    const attrs = parseXmlAttrs(m[1]);
    scalings.push({
      name: attrs.name || '',
      units: attrs.units || '',
      expression: attrs.expression || 'x',
      toByte: attrs.to_byte || 'x',
      format: attrs.format || '0',
      storagetype: attrs.storagetype || 'uint8',
      endian: attrs.endian || 'big',
    });
  }

  const tables: XmlTable[] = [];
  // Match top-level <table> blocks (may contain one nested <table> for axis or be self-closing)
  const tableRegex = /(?:<!--\s*([\s\S]*?)\s*-->\s*)?<table\s+([^>]+?)(?:\/>|>([\s\S]*?)<\/table>\s*<\/table>|>(?!\s*<table)([\s\S]*?)<\/table>)/g;
  while ((m = tableRegex.exec(xml)) !== null) {
    const commentNote = (m[1] || '').trim();
    const attrs = parseXmlAttrs(m[2]);
    if (!attrs.storageaddress) continue;
    const inner = m[3] ? `${m[3]}</table>` : m[4] || '';
    const addressNum = parseHexAddress(attrs.storageaddress) ?? 0;
    const sizey = parseInt(attrs.sizey || '1', 10) || 1;
    const sizex = parseInt(attrs.sizex || '1', 10) || 1;
    const scaling = scalings.find((s) => s.name === attrs.scaling);
    const storageType = scaling?.storagetype || 'uint8';
    const endian = scaling?.endian || 'big';
    const elemSize = storageType === 'uint16' ? 2 : 1;
    const count = sizey * sizex;

    const rawBytes: number[] = [];
    const scaledValues: number[] = [];
    for (let i = 0; i < count; i++) {
      const off = addressNum + i * elemSize;
      let rawVal = 0;
      if (off + elemSize <= romBuffer.length) {
        if (elemSize === 1) {
          rawVal = romBuffer.readUInt8(off);
        } else {
          rawVal = endian === 'little' ? romBuffer.readUInt16LE(off) : romBuffer.readUInt16BE(off);
        }
      }
      rawBytes.push(rawVal);
      scaledValues.push(
        Number(evalExpression(scaling?.expression || 'x', rawVal).toFixed(4))
      );
    }

    let axisName: string | undefined;
    let axisScaling: string | undefined;
    let axisData: number[] | undefined;
    const nestedMatch = inner.match(/<table\s+([^>]+?)>([\s\S]*?)<\/table>/);
    if (nestedMatch) {
      const nAttrs = parseXmlAttrs(nestedMatch[1]);
      axisName = nAttrs.name;
      axisScaling = nAttrs.scaling;
      axisData = [];
      const dataRegex = /<data>([^<]+)<\/data>/g;
      let dm: RegExpExecArray | null;
      while ((dm = dataRegex.exec(nestedMatch[2])) !== null) {
        axisData.push(Number(dm[1].trim()));
      }
    }

    tables.push({
      name: attrs.name || 'Unnamed Table',
      category: attrs.category || 'Uncategorized',
      storageaddress: attrs.storageaddress,
      addressNum,
      type: attrs.type || '1D',
      scalingName: attrs.scaling || '',
      scaling,
      sizey,
      sizex,
      axisName,
      axisScaling,
      axisData,
      commentNote,
      rawBytes,
      scaledValues,
    });
  }

  return { scalings, tables };
}

function parseXmlAttrs(str: string): Record<string, string> {
  const out: Record<string, string> = {};
  const attrRegex = /(\w+)="([^"]*)"/g;
  let m: RegExpExecArray | null;
  while ((m = attrRegex.exec(str)) !== null) {
    out[m[1]] = m[2];
  }
  return out;
}

function readCsvWithHeaders(filePath: string): Record<string, string>[] {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, 'utf-8');
  const lines = raw.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length === 0) return [];
  const headers = parseCsvLine(lines[0]).map((h) => h.trim());
  const rows: Record<string, string>[] = [];
  for (let i = 1; i < lines.length; i++) {
    const vals = parseCsvLine(lines[i]);
    const obj: Record<string, string> = {};
    headers.forEach((h, idx) => {
      obj[h] = (vals[idx] ?? '').trim();
    });
    rows.push(obj);
  }
  return rows;
}

// ---------------------------------------------------------------------------
// Express App & API Routes
// ---------------------------------------------------------------------------
const app = express();
app.use(express.json());

app.get('/api/overview', (_req, res) => {
  try {
    const metaPath = path.join(ROOT, 'EVIDENCE', 'EL19A_Export_Metadata.json');
    const metadata = fs.existsSync(metaPath)
      ? JSON.parse(fs.readFileSync(metaPath, 'utf-8'))
      : {};

    const memMapPath = path.join(ROOT, 'EVIDENCE', 'EL19A_Memory_Map.csv');
    const memMapLines = fs.existsSync(memMapPath)
      ? fs
          .readFileSync(memMapPath, 'utf-8')
          .split(/\r?\n/)
          .filter((l) => l.trim())
          .map((l) => {
            const c = parseCsvLine(l);
            return {
              name: c[0],
              start: c[1],
              end: c[2],
              size: Number(c[3]) || 0,
            };
          })
      : [];

    const workOrders = getWorkOrders();
    const functions = getFunctions();
    const candidates = readCsvWithHeaders(path.join(ROOT, 'CALIBRATIONS', 'candidate_register.csv'));
    const leads = readCsvWithHeaders(path.join(ROOT, 'EVIDENCE', 'open_leads.csv'));
    const xml = parseXmlTables();

    const workbookFiles = [
      ...fs
        .readdirSync(path.join(ROOT, 'WORKBOOK'))
        .filter((f) => f.endsWith('.xlsx'))
        .map((f) => ({
          dir: 'WORKBOOK',
          name: f,
          size: fs.statSync(path.join(ROOT, 'WORKBOOK', f)).size,
        })),
      ...fs
        .readdirSync(path.join(ROOT, 'EVIDENCE'))
        .filter((f) => f.endsWith('.xlsx'))
        .map((f) => ({
          dir: 'EVIDENCE',
          name: f,
          size: fs.statSync(path.join(ROOT, 'EVIDENCE', f)).size,
        })),
    ];

    res.json({
      project: {
        name: 'EL19A ECU Reverse-Engineering Project',
        vehicle: '2008 Nissan Versa / Sentra C11X (Manual Transmission)',
        cpu: 'Renesas SH7058 / SH705822N (SH-2 Big-Endian)',
        fid: '8CMCKRN5',
        romFile: 'VERSA f501.bin',
        romSizeBytes: romBuffer.length,
        romMd5,
        romSha256,
        expectedMd5: metadata.expected_md5 || '46991697c502052752a2cabcb84c9e27',
        md5Verified: romMd5 === (metadata.expected_md5 || '46991697c502052752a2cabcb84c9e27'),
      },
      metadata,
      memoryMap: memMapLines,
      counts: {
        workOrders: workOrders.length,
        functions: functions.length,
        dataItems: metadata.data_item_count || 29217,
        xrefs: metadata.xref_count || 419661,
        candidates: candidates.length,
        openLeads: leads.length,
        xmlTables: xml.tables.length,
        workbooks: workbookFiles.length,
      },
      recentWorkOrders: workOrders.slice(0, 8),
      workbookFiles,
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to load overview' });
  }
});

app.get('/api/work-orders', (req, res) => {
  try {
    const q = String(req.query.q || '').trim().toLowerCase();
    const statusFilter = String(req.query.status || 'ALL').toUpperCase();
    let items = getWorkOrders();

    if (statusFilter !== 'ALL') {
      items = items.filter((w) => {
        const s = w.status.toUpperCase();
        if (statusFilter === 'COMPLETE') return s.includes('COMPLETE') || s.includes('CLOSED');
        if (statusFilter === 'PARTIAL') return s.includes('PARTIAL') || s.includes('PARKED');
        return true;
      });
    }

    if (q) {
      items = items.filter(
        (w) =>
          w.id.toLowerCase().includes(q) ||
          w.title.toLowerCase().includes(q) ||
          w.objective.toLowerCase().includes(q) ||
          w.addresses.some((a) => a.toLowerCase().includes(q))
      );
    }

    res.json({ total: items.length, items });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to load work orders' });
  }
});

app.get('/api/work-orders/:id', (req, res) => {
  try {
    const id = req.params.id.replace(/[^a-zA-Z0-9_-]/g, '');
    const filePath = path.join(ROOT, 'CONTROL', `${id}.md`);
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: `Work order ${id} not found` });
    }
    const content = fs.readFileSync(filePath, 'utf-8');
    const summary = getWorkOrders().find((w) => w.id.toLowerCase() === id.toLowerCase());
    res.json({ id, summary, content });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to read work order' });
  }
});

app.get('/api/rom/hex', (req, res) => {
  try {
    const rawOffset = String(req.query.offset || '0x000000');
    let offset = parseHexAddress(rawOffset) ?? 0;
    const length = Math.min(Math.max(parseInt(String(req.query.length || '256'), 10) || 256, 16), 2048);

    if (offset < 0) offset = 0;
    if (offset >= romBuffer.length) offset = Math.max(0, romBuffer.length - length);

    const end = Math.min(romBuffer.length, offset + length);
    const slice = romBuffer.subarray(offset, end);

    const rows: {
      address: string;
      addressNum: number;
      bytes: number[];
      ascii: string;
      u16be: number[];
    }[] = [];

    for (let i = 0; i < slice.length; i += 16) {
      const chunk = slice.subarray(i, Math.min(i + 16, slice.length));
      const bytes = Array.from(chunk);
      const ascii = bytes
        .map((b) => (b >= 32 && b <= 126 ? String.fromCharCode(b) : '.'))
        .join('');
      const u16be: number[] = [];
      for (let j = 0; j + 1 < chunk.length; j += 2) {
        u16be.push(chunk.readUInt16BE(j));
      }
      rows.push({
        address: formatHex(offset + i),
        addressNum: offset + i,
        bytes,
        ascii,
        u16be,
      });
    }

    // Cross-reference functions & data items overlapping [offset, end)
    const funcs = getFunctions().filter(
      (f) => f.startNum < end && f.endNum > offset
    );
    const dataItems = getDataInventory()
      .filter((d) => d.startNum >= offset && d.startNum < end)
      .slice(0, 32);

    res.json({
      offset,
      offsetHex: formatHex(offset),
      length: slice.length,
      romSize: romBuffer.length,
      rows,
      overlappingFunctions: funcs.slice(0, 12),
      dataItems,
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to read ROM bytes' });
  }
});

app.get('/api/rom/search', (req, res) => {
  try {
    const q = String(req.query.q || '').trim();
    const mode = String(req.query.mode || 'ascii');
    if (!q) return res.json({ matches: [] });

    const matches: { offset: number; address: string; preview: string }[] = [];
    if (mode === 'hex') {
      const cleanHex = q.replace(/[^0-9a-fA-F]/g, '');
      if (cleanHex.length < 2 || cleanHex.length % 2 !== 0) {
        return res.status(400).json({ error: 'Hex search requires an even number of hex digits (min 2).' });
      }
      const needle = Buffer.from(cleanHex, 'hex');
      let pos = 0;
      while (pos < romBuffer.length && matches.length < 50) {
        const idx = romBuffer.indexOf(needle, pos);
        if (idx === -1) break;
        const snippet = romBuffer.subarray(idx, Math.min(idx + 16, romBuffer.length));
        matches.push({
          offset: idx,
          address: formatHex(idx),
          preview: Array.from(snippet)
            .map((b) => b.toString(16).toUpperCase().padStart(2, '0'))
            .join(' '),
        });
        pos = idx + 1;
      }
    } else {
      const needle = Buffer.from(q, 'ascii');
      let pos = 0;
      while (pos < romBuffer.length && matches.length < 50) {
        const idx = romBuffer.indexOf(needle, pos);
        if (idx === -1) break;
        const snippet = romBuffer.subarray(
          Math.max(0, idx - 4),
          Math.min(romBuffer.length, idx + needle.length + 12)
        );
        matches.push({
          offset: idx,
          address: formatHex(idx),
          preview: Array.from(snippet)
            .map((b) => (b >= 32 && b <= 126 ? String.fromCharCode(b) : '.'))
            .join(''),
        });
        pos = idx + 1;
      }
    }

    res.json({ query: q, mode, matches });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Search failed' });
  }
});

app.get('/api/rom/table', (req, res) => {
  try {
    const addr = parseHexAddress(String(req.query.address || '0xE678')) ?? 0;
    const rows = Math.min(Math.max(parseInt(String(req.query.rows || '16'), 10) || 1, 1), 32);
    const cols = Math.min(Math.max(parseInt(String(req.query.cols || '1'), 10) || 1, 1), 32);
    const storage = String(req.query.storage || 'uint8') === 'uint16' ? 'uint16' : 'uint8';
    const endian = String(req.query.endian || 'big') === 'little' ? 'little' : 'big';
    const mult = Number(req.query.mult ?? 1) || 1;
    const offsetVal = Number(req.query.offset ?? 0) || 0;
    const elemSize = storage === 'uint16' ? 2 : 1;

    if (addr < 0 || addr + rows * cols * elemSize > romBuffer.length) {
      return res.status(400).json({ error: 'Requested table extends outside 1 MiB ROM bounds' });
    }

    const rawMatrix: number[][] = [];
    const scaledMatrix: number[][] = [];
    let minVal = Infinity;
    let maxVal = -Infinity;

    for (let r = 0; r < rows; r++) {
      const rRaw: number[] = [];
      const rScaled: number[] = [];
      for (let c = 0; c < cols; c++) {
        const pos = addr + (r * cols + c) * elemSize;
        const raw =
          elemSize === 1
            ? romBuffer.readUInt8(pos)
            : endian === 'little'
            ? romBuffer.readUInt16LE(pos)
            : romBuffer.readUInt16BE(pos);
        const scaled = Number((raw * mult + offsetVal).toFixed(4));
        rRaw.push(raw);
        rScaled.push(scaled);
        if (scaled < minVal) minVal = scaled;
        if (scaled > maxVal) maxVal = scaled;
      }
      rawMatrix.push(rRaw);
      scaledMatrix.push(rScaled);
    }

    // Optional ROM axis reads
    const readAxis = (
      axisAddrStr: string | undefined,
      count: number,
      axisStorage: string,
      axisMult: number,
      axisOffset: number
    ): number[] | null => {
      if (!axisAddrStr) return null;
      const aAddr = parseHexAddress(axisAddrStr);
      if (aAddr === null) return null;
      const aSize = axisStorage === 'uint16' ? 2 : 1;
      if (aAddr < 0 || aAddr + count * aSize > romBuffer.length) return null;
      const out: number[] = [];
      for (let i = 0; i < count; i++) {
        const pos = aAddr + i * aSize;
        const raw =
          aSize === 1
            ? romBuffer.readUInt8(pos)
            : endian === 'little'
            ? romBuffer.readUInt16LE(pos)
            : romBuffer.readUInt16BE(pos);
        out.push(Number((raw * axisMult + axisOffset).toFixed(4)));
      }
      return out;
    };

    const yAxis = readAxis(
      req.query.yAxisAddr ? String(req.query.yAxisAddr) : undefined,
      rows,
      String(req.query.yAxisStorage || storage),
      Number(req.query.yAxisMult ?? 1) || 1,
      Number(req.query.yAxisOffset ?? 0) || 0
    );

    const xAxis = readAxis(
      req.query.xAxisAddr ? String(req.query.xAxisAddr) : undefined,
      cols,
      String(req.query.xAxisStorage || storage),
      Number(req.query.xAxisMult ?? 1) || 1,
      Number(req.query.xAxisOffset ?? 0) || 0
    );

    res.json({
      address: formatHex(addr),
      rows,
      cols,
      storage,
      endian,
      mult,
      offset: offsetVal,
      minVal,
      maxVal,
      rawMatrix,
      scaledMatrix,
      yAxis,
      xAxis,
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to read table' });
  }
});

app.get('/api/calibrations', (_req, res) => {
  try {
    const candidates = readCsvWithHeaders(path.join(ROOT, 'CALIBRATIONS', 'candidate_register.csv'));
    const leads = readCsvWithHeaders(path.join(ROOT, 'EVIDENCE', 'open_leads.csv'));
    const xml = parseXmlTables();
    const rawXml = fs.existsSync(
      path.join(ROOT, 'EVIDENCE', 'EL19A_ETC_Dashpot_Limiters_fragment-2.xml')
    )
      ? fs.readFileSync(
          path.join(ROOT, 'EVIDENCE', 'EL19A_ETC_Dashpot_Limiters_fragment-2.xml'),
          'utf-8'
        )
      : '';

    // Enrich candidate register with live first 16 ROM bytes at candidate address
    const enrichedCandidates = candidates.map((c) => {
      const addr = parseHexAddress(c.address);
      let liveHex = '';
      if (addr !== null && addr >= 0 && addr < romBuffer.length) {
        const slice = romBuffer.subarray(addr, Math.min(addr + 16, romBuffer.length));
        liveHex = Array.from(slice)
          .map((b) => b.toString(16).toUpperCase().padStart(2, '0'))
          .join(' ');
      }
      return { ...c, liveHex };
    });

    res.json({
      candidates: enrichedCandidates,
      openLeads: leads,
      xmlScalings: xml.scalings,
      xmlTables: xml.tables,
      rawXml,
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to load calibrations' });
  }
});

app.get('/api/functions', (req, res) => {
  try {
    const q = String(req.query.q || '').trim().toLowerCase();
    const minSize = parseInt(String(req.query.minSize || '0'), 10) || 0;
    const limit = Math.min(Math.max(parseInt(String(req.query.limit || '100'), 10) || 100, 10), 500);
    const offset = Math.max(parseInt(String(req.query.offset || '0'), 10) || 0, 0);

    let items = getFunctions();
    if (minSize > 0) {
      items = items.filter((f) => f.size >= minSize);
    }
    if (q) {
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.startEa.toLowerCase().includes(q) ||
          f.callers.some((c) => c.toLowerCase().includes(q)) ||
          f.callees.some((c) => c.toLowerCase().includes(q))
      );
    }

    res.json({
      total: items.length,
      offset,
      limit,
      items: items.slice(offset, offset + limit),
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to load functions' });
  }
});

app.get('/api/data-inventory', (req, res) => {
  try {
    const q = String(req.query.q || '').trim().toLowerCase();
    const limit = Math.min(Math.max(parseInt(String(req.query.limit || '100'), 10) || 100, 10), 300);
    const offset = Math.max(parseInt(String(req.query.offset || '0'), 10) || 0, 0);

    let items = getDataInventory();
    if (q) {
      items = items.filter(
        (d) =>
          d.startEa.toLowerCase().includes(q) ||
          d.name.toLowerCase().includes(q) ||
          d.disasm.toLowerCase().includes(q) ||
          d.targetEa.toLowerCase().includes(q) ||
          d.comment.toLowerCase().includes(q)
      );
    }

    res.json({
      total: items.length,
      offset,
      limit,
      items: items.slice(offset, offset + limit),
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to load data inventory' });
  }
});

app.get('/api/workbooks', (_req, res) => {
  try {
    const list: { id: string; dir: string; name: string; size: number }[] = [];
    for (const dir of ['WORKBOOK', 'EVIDENCE']) {
      const fullDir = path.join(ROOT, dir);
      if (!fs.existsSync(fullDir)) continue;
      for (const f of fs.readdirSync(fullDir)) {
        if (f.endsWith('.xlsx')) {
          list.push({
            id: `${dir}/${f}`,
            dir,
            name: f,
            size: fs.statSync(path.join(fullDir, f)).size,
          });
        }
      }
    }
    res.json({ workbooks: list });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to list workbooks' });
  }
});

app.get('/api/workbooks/sheets', (req, res) => {
  try {
    const wbId = String(req.query.id || '');
    const safeRel = wbId.replace(/\.\./g, '');
    if (!safeRel.startsWith('WORKBOOK/') && !safeRel.startsWith('EVIDENCE/')) {
      return res.status(400).json({ error: 'Invalid workbook path' });
    }
    const fullPath = path.join(ROOT, safeRel);
    if (!fs.existsSync(fullPath)) {
      return res.status(404).json({ error: 'Workbook not found' });
    }
    let wb = workbookCache.get(safeRel);
    if (!wb) {
      wb = XLSX.readFile(fullPath, { cellDates: true });
      workbookCache.set(safeRel, wb);
    }
    res.json({ id: safeRel, sheets: wb.SheetNames });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to parse workbook' });
  }
});

app.get('/api/workbooks/sheet-data', (req, res) => {
  try {
    const wbId = String(req.query.id || '');
    const sheetName = String(req.query.sheet || '');
    const q = String(req.query.q || '').trim().toLowerCase();
    const limit = Math.min(Math.max(parseInt(String(req.query.limit || '150'), 10) || 150, 10), 500);
    const offset = Math.max(parseInt(String(req.query.offset || '0'), 10) || 0, 0);

    const safeRel = wbId.replace(/\.\./g, '');
    if (!safeRel.startsWith('WORKBOOK/') && !safeRel.startsWith('EVIDENCE/')) {
      return res.status(400).json({ error: 'Invalid workbook path' });
    }
    const fullPath = path.join(ROOT, safeRel);
    if (!fs.existsSync(fullPath)) {
      return res.status(404).json({ error: 'Workbook not found' });
    }
    let wb = workbookCache.get(safeRel);
    if (!wb) {
      wb = XLSX.readFile(fullPath, { cellDates: true });
      workbookCache.set(safeRel, wb);
    }
    const targetSheet = sheetName || wb.SheetNames[0];
    const ws = wb.Sheets[targetSheet];
    if (!ws) {
      return res.status(404).json({ error: `Sheet "${targetSheet}" not found` });
    }

    const rawRows: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
    const filtered = q
      ? rawRows.filter((row, idx) =>
          idx === 0 || row.some((cell) => String(cell).toLowerCase().includes(q))
        )
      : rawRows;

    res.json({
      id: safeRel,
      sheet: targetSheet,
      totalRows: filtered.length,
      offset,
      limit,
      rows: filtered.slice(offset, offset + limit),
    });
  } catch (err: any) {
    res.status(500).json({ error: err?.message || 'Failed to read sheet data' });
  }
});

app.get('/api/docs', (_req, res) => {
  const docCandidates = [
    'README.md',
    'PROJECT_STATE.md',
    'MIGRATION_QUEUE.md',
    'CONTROL/active_work_orders.md',
    'CONTROL/protocol_v3.md',
    'CONTROL/authority_and_conflicts.md',
    'EVIDENCE/decisions.md',
    'EVIDENCE/EL19A ROM Analysis Method Playbook for Other Workers.md',
    'EVIDENCE/EL19A ROM Index and Supporting Materials for Other Workers.md',
    'CALIBRATIONS/README.md',
    'WORKBOOK/V55_WO64830_INTEGRATION_SUMMARY_2026-11-15.md',
    'WORKBOOK/V54_E974_INTEGRATION_SUMMARY_2026-11-15.md',
    'WORKBOOK/V53_SOURCE_MANIFEST.md',
  ];
  const docs = docCandidates
    .filter((rel) => fs.existsSync(path.join(ROOT, rel)))
    .map((rel) => ({
      path: rel,
      name: path.basename(rel),
      size: fs.statSync(path.join(ROOT, rel)).size,
    }));
  res.json({ docs });
});

app.get('/api/docs/content', (req, res) => {
  const rel = String(req.query.path || 'README.md').replace(/\.\./g, '');
  const fullPath = path.join(ROOT, rel);
  if (!fullPath.startsWith(ROOT) || !fs.existsSync(fullPath)) {
    return res.status(404).json({ error: 'Document not found' });
  }
  const content = fs.readFileSync(fullPath, 'utf-8');
  res.json({ path: rel, content });
});

// ---------------------------------------------------------------------------
// Vite Dev Middleware or Static Production Serving
// ---------------------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.join(ROOT, 'dist');
    app.use(express.static(distDir));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distDir, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`EL19A Workbench listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
