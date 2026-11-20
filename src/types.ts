export type ActiveSection =
  | 'overview'
  | 'calibrations'
  | 'rom'
  | 'work-orders'
  | 'functions'
  | 'workbooks';

export interface OverviewResponse {
  project: {
    name: string;
    vehicle: string;
    cpu: string;
    fid: string;
    romFile: string;
    romSizeBytes: number;
    romMd5: string;
    romSha256: string;
    expectedMd5: string;
    md5Verified: boolean;
  };
  metadata: Record<string, any>;
  memoryMap: {
    name: string;
    start: string;
    end: string;
    size: number;
  }[];
  counts: {
    workOrders: number;
    functions: number;
    dataItems: number;
    xrefs: number;
    candidates: number;
    openLeads: number;
    xmlTables: number;
    workbooks: number;
  };
  recentWorkOrders: WorkOrderSummary[];
  workbookFiles: { dir: string; name: string; size: number }[];
}

export interface WorkOrderSummary {
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

export interface XmlScaling {
  name: string;
  units: string;
  expression: string;
  toByte: string;
  format: string;
  storagetype: string;
  endian: string;
}

export interface XmlAxis {
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

export interface XmlTable {
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

export interface XmlDefinitionSet {
  id: string;
  filename: string;
  label: string;
  romid: Record<string, string>;
  scalings: XmlScaling[];
  tables: XmlTable[];
  rawXml: string;
}

export interface CalibrationsResponse {
  candidates: CandidateRow[];
  openLeads: OpenLeadRow[];
  mergedV3: XmlDefinitionSet;
  ignitionDecoded: XmlDefinitionSet;
  repoFragment: XmlDefinitionSet;
  xmlScalings: XmlScaling[];
  xmlTables: XmlTable[];
  rawXml: string;
}

export interface CandidateRow {
  address: string;
  candidate_name: string;
  dimensions: string;
  storage: string;
  axis_or_reader: string;
  conversion: string;
  status: string;
  liveHex: string;
}

export interface OpenLeadRow {
  id: string;
  address_or_topic: string;
  best_current_interpretation: string;
  status: string;
  confidence_or_note: string;
  source_context: string;
}

export interface FunctionEntry {
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

export interface DataInventoryEntry {
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

export interface HexRow {
  address: string;
  addressNum: number;
  bytes: number[];
  ascii: string;
  u16be: number[];
}

export interface RomHexResponse {
  offset: number;
  offsetHex: string;
  length: number;
  romSize: number;
  rows: HexRow[];
  overlappingFunctions: FunctionEntry[];
  dataItems: DataInventoryEntry[];
}

export interface RomTableResponse {
  address: string;
  rows: number;
  cols: number;
  storage: 'uint8' | 'uint16';
  endian: 'big' | 'little';
  mult: number;
  offset: number;
  expr?: string;
  minVal: number;
  maxVal: number;
  rawMatrix: number[][];
  scaledMatrix: number[][];
  yAxis: number[] | null;
  xAxis: number[] | null;
}

export interface TablePreset {
  label: string;
  address: string;
  rows: number;
  cols: number;
  storage: 'uint8' | 'uint16';
  endian: 'big' | 'little';
  mult: number;
  offset: number;
  expr?: string;
  yAxisAddr?: string;
  yAxisStorage?: 'uint8' | 'uint16';
  yAxisMult?: number;
  yAxisExpr?: string;
  xAxisAddr?: string;
  xAxisStorage?: 'uint8' | 'uint16';
  xAxisMult?: number;
  xAxisExpr?: string;
}
