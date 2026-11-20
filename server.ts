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

interface XmlAxis {
  name: string;
  type: string;
  isStatic: boolean;
  storageaddress?: string;
  addressNum?: number;
  scalingName: string;
  scaling?: XmlScaling;
  storagetype: string;
  endian: string;
  size: number;
  rawValues: number[];
  values: number[];
}

interface XmlTable {
  id: string;
  name: string;
  category: string;
  isSpeculative: boolean;
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
  xAxis?: XmlAxis;
  yAxis?: XmlAxis;
  commentNote?: string;
  rawBytes: number[];
  scaledValues: number[];
  rawMatrix?: number[][];
  scaledMatrix?: number[][];
}

interface XmlDefinitionSet {
  id: string;
  filename: string;
  label: string;
  romid: Record<string, string>;
  scalings: XmlScaling[];
  tables: XmlTable[];
  rawXml: string;
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
  const src = (expr || 'x').trim();
  if (src === 'x') return x;

  let pos = 0;
  const skipWs = () => {
    while (pos < src.length && /\s/.test(src[pos])) pos++;
  };

  const parseExpr = (): number => {
    let left = parseTerm();
    while (true) {
      skipWs();
      const ch = src[pos];
      if (ch === '+') {
        pos++;
        left += parseTerm();
      } else if (ch === '-') {
        pos++;
        left -= parseTerm();
      } else {
        break;
      }
    }
    return left;
  };

  const parseTerm = (): number => {
    let left = parseUnary();
    while (true) {
      skipWs();
      const ch = src[pos];
      if (ch === '*') {
        pos++;
        left *= parseUnary();
      } else if (ch === '/') {
        pos++;
        const d = parseUnary();
        left = d === 0 ? 0 : left / d;
      } else if (ch === '%') {
        pos++;
        const d = parseUnary();
        left = d === 0 ? 0 : left % d;
      } else {
        break;
      }
    }
    return left;
  };

  const parseUnary = (): number => {
    skipWs();
    const ch = src[pos];
    if (ch === '+') {
      pos++;
      return parseUnary();
    }
    if (ch === '-') {
      pos++;
      return -parseUnary();
    }
    return parsePrimary();
  };

  const parsePrimary = (): number => {
    skipWs();
    if (src[pos] === '(') {
      pos++;
      const val = parseExpr();
      skipWs();
      if (src[pos] === ')') pos++;
      return val;
    }
    const numMatch = src.slice(pos).match(/^(?:\d+\.\d*|\d*\.\d+|\d+)/);
    if (numMatch) {
      pos += numMatch[0].length;
      return parseFloat(numMatch[0]);
    }
    const idMatch = src.slice(pos).match(/^[a-zA-Z_][a-zA-Z0-9_]*/);
    if (idMatch) {
      const ident = idMatch[0].toLowerCase();
      pos += idMatch[0].length;
      if (ident === 'x') return x;
      skipWs();
      if (src[pos] === '(') {
        pos++;
        const arg = parseExpr();
        skipWs();
        if (src[pos] === ')') pos++;
        if (ident === 'floor') return Math.floor(arg);
        if (ident === 'ceil') return Math.ceil(arg);
        if (ident === 'round') return Math.round(arg);
        if (ident === 'abs') return Math.abs(arg);
        return arg;
      }
      return x;
    }
    throw new Error(`Unexpected token at ${pos} in expression "${src}"`);
  };

  try {
    const val = parseExpr();
    return Number.isFinite(val) ? val : x;
  } catch {
    return x;
  }
}

function readRomElements(
  addressNum: number,
  count: number,
  storagetype: string,
  endian: string
): number[] {
  const elemSize = storagetype === 'uint16' ? 2 : 1;
  const out: number[] = [];
  for (let i = 0; i < count; i++) {
    const off = addressNum + i * elemSize;
    let rawVal = 0;
    if (off >= 0 && off + elemSize <= romBuffer.length) {
      if (elemSize === 1) {
        rawVal = romBuffer.readUInt8(off);
      } else {
        rawVal = endian === 'little' ? romBuffer.readUInt16LE(off) : romBuffer.readUInt16BE(off);
      }
    }
    out.push(rawVal);
  }
  return out;
}

interface ParsedSubTable {
  attrs: Record<string, string>;
  inlineScalings: XmlScaling[];
  staticData: number[];
}

interface ParsedTopTable {
  attrs: Record<string, string>;
  commentNote: string;
  inlineScalings: XmlScaling[];
  staticData: number[];
  subTables: ParsedSubTable[];
}

function parseRomRaiderXml(filePath: string, id: string, label: string): XmlDefinitionSet {
  const filename = path.basename(filePath);
  if (!fs.existsSync(filePath)) {
    return {
      id,
      filename,
      label,
      romid: {},
      scalings: [],
      tables: [],
      rawXml: '',
    };
  }

  const rawXml = fs.readFileSync(filePath, 'utf-8');
  const romid: Record<string, string> = {};
  const romidMatch = rawXml.match(/<romid>([\s\S]*?)<\/romid>/);
  if (romidMatch) {
    const tagRe = /<([a-zA-Z0-9_-]+)>([^<]*)<\/\1>/g;
    let rm: RegExpExecArray | null;
    while ((rm = tagRe.exec(romidMatch[1])) !== null) {
      romid[rm[1]] = rm[2].trim();
    }
  }

  const topScalings: XmlScaling[] = [];
  const scalingByName = new Map<string, XmlScaling>();
  const topTables: ParsedTopTable[] = [];

  const tokenRegex = /<!--([\s\S]*?)-->|<(\/?)([a-zA-Z0-9_-]+)((?:[^>"']|"[^"]*"|'[^']*')*)>/g;
  let pendingComment = '';
  const tableStack: Array<
    | { kind: 'top'; node: ParsedTopTable }
    | { kind: 'sub'; node: ParsedSubTable }
  > = [];

  let m: RegExpExecArray | null;
  while ((m = tokenRegex.exec(rawXml)) !== null) {
    if (m[1] !== undefined) {
      if (tableStack.length === 0) {
        pendingComment = m[1].trim();
      }
      continue;
    }

    const isClosing = m[2] === '/';
    const tagName = (m[3] || '').toLowerCase();
    const rawTail = m[4] || '';
    const isSelfClosing = !isClosing && rawTail.trimEnd().endsWith('/');
    const attrStr = isSelfClosing ? rawTail.replace(/\/\s*$/, '') : rawTail;

    if (tagName === 'scaling' && !isClosing) {
      const attrs = parseXmlAttrs(attrStr);
      const sc: XmlScaling = {
        name: attrs.name || '',
        units: attrs.units || '',
        expression: attrs.expression || 'x',
        toByte: attrs.to_byte || 'x',
        format: attrs.format || '0',
        storagetype: attrs.storagetype || 'uint8',
        endian: (attrs.endian || 'big').toLowerCase(),
      };
      if (tableStack.length === 0) {
        topScalings.push(sc);
        if (sc.name) scalingByName.set(sc.name, sc);
        pendingComment = '';
      } else {
        const top = tableStack[tableStack.length - 1];
        top.node.inlineScalings.push(sc);
        if (sc.name && !scalingByName.has(sc.name)) {
          scalingByName.set(sc.name, sc);
        }
      }
      continue;
    }

    if (tagName === 'data' && !isClosing && !isSelfClosing && tableStack.length > 0) {
      const endDataIdx = rawXml.indexOf('</data>', tokenRegex.lastIndex);
      if (endDataIdx !== -1) {
        const numText = rawXml.slice(tokenRegex.lastIndex, endDataIdx).trim();
        const numVal = Number(numText);
        if (!Number.isNaN(numVal)) {
          tableStack[tableStack.length - 1].node.staticData.push(numVal);
        }
        tokenRegex.lastIndex = endDataIdx + 7;
      }
      continue;
    }

    if (tagName === 'table') {
      if (isClosing) {
        const popped = tableStack.pop();
        if (popped && popped.kind === 'top') {
          topTables.push(popped.node);
        } else if (popped && popped.kind === 'sub' && tableStack.length > 0) {
          const parent = tableStack[tableStack.length - 1];
          if (parent.kind === 'top') {
            parent.node.subTables.push(popped.node);
          }
        }
        continue;
      }

      const attrs = parseXmlAttrs(attrStr);
      if (tableStack.length === 0) {
        const topNode: ParsedTopTable = {
          attrs,
          commentNote: pendingComment,
          inlineScalings: [],
          staticData: [],
          subTables: [],
        };
        pendingComment = '';
        if (isSelfClosing) {
          topTables.push(topNode);
        } else {
          tableStack.push({ kind: 'top', node: topNode });
        }
      } else {
        const subNode: ParsedSubTable = {
          attrs,
          inlineScalings: [],
          staticData: [],
        };
        if (isSelfClosing) {
          const parent = tableStack[tableStack.length - 1];
          if (parent.kind === 'top') {
            parent.node.subTables.push(subNode);
          }
        } else {
          tableStack.push({ kind: 'sub', node: subNode });
        }
      }
    }
  }

  const tables: XmlTable[] = [];
  topTables.forEach((parsed, idx) => {
    const attrs = parsed.attrs;
    if (!attrs.storageaddress) return;
    const addressNum = parseHexAddress(attrs.storageaddress) ?? 0;
    const sizey = parseInt(attrs.sizey || '1', 10) || 1;
    const sizex = parseInt(attrs.sizex || '1', 10) || 1;

    const scaling =
      parsed.inlineScalings.find((s) => s.name === attrs.scaling) ||
      scalingByName.get(attrs.scaling || '') ||
      parsed.inlineScalings[0];

    const storageType = attrs.storagetype || scaling?.storagetype || 'uint8';
    const endian = (attrs.endian || scaling?.endian || 'big').toLowerCase();
    const expr = scaling?.expression || 'x';
    const count = sizey * sizex;

    const rawBytes = readRomElements(addressNum, count, storageType, endian);
    const scaledValues = rawBytes.map((raw) => Number(evalExpression(expr, raw).toFixed(4)));

    let rawMatrix: number[][] | undefined;
    let scaledMatrix: number[][] | undefined;
    if (sizex > 1 || sizey > 1) {
      rawMatrix = [];
      scaledMatrix = [];
      for (let r = 0; r < sizey; r++) {
        rawMatrix.push(rawBytes.slice(r * sizex, (r + 1) * sizex));
        scaledMatrix.push(scaledValues.slice(r * sizex, (r + 1) * sizex));
      }
    }

    const resolveAxis = (sub: ParsedSubTable, defaultSize: number): XmlAxis => {
      const aAttrs = sub.attrs;
      const aType = aAttrs.type || 'Y Axis';
      const aScaling =
        sub.inlineScalings.find((s) => s.name === aAttrs.scaling) ||
        scalingByName.get(aAttrs.scaling || '') ||
        sub.inlineScalings[0];
      const aStorage = aAttrs.storagetype || aScaling?.storagetype || 'uint8';
      const aEndian = (aAttrs.endian || aScaling?.endian || 'big').toLowerCase();
      const aSize =
        parseInt(aAttrs.sizex || aAttrs.sizey || String(defaultSize), 10) || defaultSize;
      const aExpr = aScaling?.expression || 'x';
      const aAddrNum = aAttrs.storageaddress
        ? parseHexAddress(aAttrs.storageaddress) ?? undefined
        : undefined;
      const isStatic =
        aType.toLowerCase().includes('static') ||
        (sub.staticData.length > 0 && !aAttrs.storageaddress);

      let rawAxisValues: number[] = [];
      let scaledAxisValues: number[] = [];
      if (sub.staticData.length > 0) {
        rawAxisValues = sub.staticData.slice();
        scaledAxisValues = sub.staticData.map((v) =>
          Number(evalExpression(aExpr, v).toFixed(4))
        );
      } else if (aAddrNum !== undefined) {
        rawAxisValues = readRomElements(aAddrNum, aSize, aStorage, aEndian);
        scaledAxisValues = rawAxisValues.map((v) =>
          Number(evalExpression(aExpr, v).toFixed(4))
        );
      }

      return {
        name: aAttrs.name || aType,
        type: aType,
        isStatic,
        storageaddress: aAttrs.storageaddress,
        addressNum: aAddrNum,
        scalingName: aAttrs.scaling || '',
        scaling: aScaling,
        storagetype: aStorage,
        endian: aEndian,
        size: scaledAxisValues.length || aSize,
        rawValues: rawAxisValues,
        values: scaledAxisValues,
      };
    };

    let xAxis: XmlAxis | undefined;
    let yAxis: XmlAxis | undefined;
    for (const sub of parsed.subTables) {
      const t = (sub.attrs.type || '').toLowerCase();
      if (t.includes('x axis')) {
        xAxis = resolveAxis(sub, sizex);
      } else if (t.includes('y axis')) {
        yAxis = resolveAxis(sub, sizey);
      }
    }

    const name = attrs.name || 'Unnamed Table';
    const category = attrs.category || 'Uncategorized';
    const isSpeculative = name.includes('[S') || category.startsWith('SPEC//');

    tables.push({
      id: `${id}:${attrs.storageaddress}:${idx}:${attrs.scaling || 'raw'}`,
      name,
      category,
      isSpeculative,
      storageaddress: attrs.storageaddress,
      addressNum,
      type: attrs.type || '1D',
      scalingName: attrs.scaling || '',
      scaling,
      sizey,
      sizex,
      axisName: yAxis?.name || xAxis?.name,
      axisScaling: yAxis?.scalingName || xAxis?.scalingName,
      axisData: yAxis?.values,
      xAxis,
      yAxis,
      commentNote: parsed.commentNote,
      rawBytes,
      scaledValues,
      rawMatrix,
      scaledMatrix,
    });
  });

  return {
    id,
    filename,
    label,
    romid,
    scalings: topScalings,
    tables,
    rawXml,
  };
}

function getAllXmlDefinitions(): {
  mergedV3: XmlDefinitionSet;
  ignitionDecoded: XmlDefinitionSet;
  repoFragment: XmlDefinitionSet;
} {
  return {
    mergedV3: parseRomRaiderXml(
      path.join(ROOT, 'public', 'assets', 'aistudio', 'EL19A_merged_definition_v3_08a300db.xml'),
      'merged',
      'Current Working Def v3'
    ),
    ignitionDecoded: parseRomRaiderXml(
      path.join(ROOT, 'public', 'assets', 'aistudio', 'EL19A_ignition_decoded_fragment_33ea8e67.xml'),
      'ignition',
      'Ignition Timing Decoded'
    ),
    repoFragment: parseRomRaiderXml(
      path.join(ROOT, 'EVIDENCE', 'EL19A_ETC_Dashpot_Limiters_fragment-2.xml'),
      'fragment',
      'ETC Verified Fragment'
    ),
  };
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
    const xmlDefs = getAllXmlDefinitions();

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
        xmlTables: xmlDefs.mergedV3.tables.length || xmlDefs.repoFragment.tables.length,
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
    const expr = String(req.query.expr || '').trim();
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
        const scaled = expr
          ? Number(evalExpression(expr, raw).toFixed(4))
          : Number((raw * mult + offsetVal).toFixed(4));
        rRaw.push(raw);
        rScaled.push(scaled);
        if (scaled < minVal) minVal = scaled;
        if (scaled > maxVal) maxVal = scaled;
      }
      rawMatrix.push(rRaw);
      scaledMatrix.push(rScaled);
    }

    const readAxis = (
      axisAddrStr: string | undefined,
      count: number,
      axisStorage: string,
      axisMult: number,
      axisOffset: number,
      axisExpr: string
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
        const scaled = axisExpr
          ? Number(evalExpression(axisExpr, raw).toFixed(4))
          : Number((raw * axisMult + axisOffset).toFixed(4));
        out.push(scaled);
      }
      return out;
    };

    const yAxis = readAxis(
      req.query.yAxisAddr ? String(req.query.yAxisAddr) : undefined,
      rows,
      String(req.query.yAxisStorage || storage),
      Number(req.query.yAxisMult ?? 1) || 1,
      Number(req.query.yAxisOffset ?? 0) || 0,
      String(req.query.yAxisExpr || '').trim()
    );

    const xAxis = readAxis(
      req.query.xAxisAddr ? String(req.query.xAxisAddr) : undefined,
      cols,
      String(req.query.xAxisStorage || storage),
      Number(req.query.xAxisMult ?? 1) || 1,
      Number(req.query.xAxisOffset ?? 0) || 0,
      String(req.query.xAxisExpr || '').trim()
    );

    res.json({
      address: formatHex(addr),
      rows,
      cols,
      storage,
      endian,
      mult,
      offset: offsetVal,
      expr,
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
    const xmlDefs = getAllXmlDefinitions();

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
      mergedV3: xmlDefs.mergedV3,
      ignitionDecoded: xmlDefs.ignitionDecoded,
      repoFragment: xmlDefs.repoFragment,
      xmlScalings: xmlDefs.mergedV3.scalings,
      xmlTables: xmlDefs.mergedV3.tables,
      rawXml: xmlDefs.mergedV3.rawXml,
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
    app.get('/@vite/client', (_req, res) => {
      res.type('application/javascript').send(`
const sheetsMap = new Map();
export function updateStyle(id, content) {
  let style = sheetsMap.get(id);
  if (!style) {
    style = document.createElement('style');
    style.setAttribute('type', 'text/css');
    style.setAttribute('data-vite-dev-id', id);
    style.textContent = content;
    document.head.appendChild(style);
  } else {
    style.textContent = content;
  }
  sheetsMap.set(id, style);
}
export function removeStyle(id) {
  const style = sheetsMap.get(id);
  if (style) {
    document.head.removeChild(style);
    sheetsMap.delete(id);
  }
}
export function createHotContext() {
  return {
    data: {},
    accept() {},
    acceptExports() {},
    dispose() {},
    prune() {},
    decline() {},
    invalidate() {},
    on() {},
    off() {},
    send() {},
  };
}
export function injectQuery(url) { return url; }
export class ErrorOverlay extends HTMLElement {}
`);
    });

    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true, hmr: false, ws: false },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distDir = path.join(ROOT, 'dist');
    app.use(express.static(distDir));
    app.use((_req, res) => {
      res.sendFile(path.join(distDir, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
