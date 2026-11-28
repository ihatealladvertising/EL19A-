import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const inputPath = 'C:/Users/Vivian/Downloads/uprev ecus.txt';
const outputDir = 'C:/Users/Vivian/Documents/Codex/2026-11-27/co/outputs';
const outputPath = `${outputDir}/nissan_rom_model_year_index.xlsx`;
const sourceText = await fs.readFile(inputPath, 'utf8');
const lines = sourceText.replace(/^\uFEFF/, '').split(/\r?\n/);
const headers = lines[0].split('\t').map(x => x.trim());
const expectedHeaders = ['Model', 'Make', 'Vehicle Year', 'Engine Code', 'Transmission', 'Master ROM', 'ROMs Updated'];
if (JSON.stringify(headers) !== JSON.stringify(expectedHeaders)) {
  throw new Error(`Unexpected source headers: ${JSON.stringify(headers)}`);
}

// The source explicitly reports 2,161 rows; following lines contain a separate inventory.
const countLineIndex = lines.findIndex(x => /^Showing 1 to 2,161 of 2,161 entries\s*$/.test(x));
if (countLineIndex !== 2162) throw new Error(`Catalog boundary changed: expected line 2163, found ${countLineIndex + 1}`);
const sourceRows = [];
const romRows = [];
for (let i = 1; i < countLineIndex; i++) {
  const cells = lines[i].split('\t');
  if (cells.length !== 7) throw new Error(`Catalog row ${i + 1} has ${cells.length} columns`);
  const [model, make, yearText, engine, transmission, masterRom, updatedText] = cells.map(x => x.trim());
  const year = Number(yearText.replaceAll(',', ''));
  if (!Number.isInteger(year) || !model || !make || !updatedText) throw new Error(`Invalid catalog data on line ${i + 1}`);
  sourceRows.push([i + 1, model, make, year, engine, transmission, masterRom, updatedText]);
  const listedCodes = updatedText.split(',').map(x => x.trim()).filter(Boolean);
  if (!listedCodes.length) throw new Error(`No ROM codes on line ${i + 1}`);
  for (const listedCode of listedCodes) {
    romRows.push([listedCode.toUpperCase(), listedCode, model, make, year, engine, transmission, masterRom, i + 1]);
  }
}

romRows.sort((a, b) => a[0].localeCompare(b[0]) || a[4] - b[4] || a[2].localeCompare(b[2]));
const distinctCodes = new Set(romRows.map(row => row[0]));
const yearValues = sourceRows.map(row => row[3]);
const modelNames = new Set(sourceRows.map(row => row[1]));
const makeNames = new Set(sourceRows.map(row => row[2]));
const dupCounts = new Map();
for (const row of romRows) dupCounts.set(row[0], (dupCounts.get(row[0]) ?? 0) + 1);
const multiVehicleCodes = [...dupCounts.values()].filter(n => n > 1).length;

const workbook = Workbook.create();
const indexSheet = workbook.worksheets.add('ROM to Model Year');
const sourceSheet = workbook.worksheets.add('Source Catalog');
for (const sheet of [indexSheet, sourceSheet]) sheet.showGridLines = false;

indexSheet.getRange('A2').values = [['Nissan / Infiniti ROM to model-year index']];
indexSheet.getRange('A3').values = [[`${romRows.length.toLocaleString('en-US')} ROM-to-vehicle links · ${distinctCodes.size.toLocaleString('en-US')} distinct ROM IDs · ${sourceRows.length.toLocaleString('en-US')} catalog rows · ${Math.min(...yearValues)}–${Math.max(...yearValues)} · ${modelNames.size} model names`]];
indexSheet.getRange('A4').values = [['ROM IDs are catalog codes, not binary hashes. Each row comes from “ROMs Updated”; source spelling, Master ROM, and catalog line are retained. The differently structured inventory after line 2,163 is not merged.']];
const indexHeaders = ['ROM ID', 'ROM ID as listed', 'Model', 'Make', 'Vehicle Year', 'Engine Code', 'Transmission', 'Master ROM', 'Source line'];
indexSheet.getRange('A6:I6').values = [indexHeaders];
indexSheet.getRange(`A7:I${6 + romRows.length}`).values = romRows;
const romTable = indexSheet.tables.add(`A6:I${6 + romRows.length}`, true, 'RomVehicleIndex');
romTable.style = 'TableStyleMedium2';
romTable.showFilterButton = true;
indexSheet.getRange('A2:I4').format.font = { name: 'Arial', size: 10, color: '#242424' };
indexSheet.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true, color: '#1F1F1F' };
indexSheet.getRange('A3:A4').format.wrapText = false;
indexSheet.getRange('A6:I6').format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
indexSheet.getRange('A:A').format.columnWidth = 17;
indexSheet.getRange('B:B').format.columnWidth = 18;
indexSheet.getRange('C:C').format.columnWidth = 25;
indexSheet.getRange('D:D').format.columnWidth = 14;
indexSheet.getRange('E:E').format.columnWidth = 13;
indexSheet.getRange('F:F').format.columnWidth = 18;
indexSheet.getRange('G:G').format.columnWidth = 16;
indexSheet.getRange('H:H').format.columnWidth = 17;
indexSheet.getRange('I:I').format.columnWidth = 13;
indexSheet.getRange(`E7:E${6 + romRows.length}`).format.numberFormat = '0';
indexSheet.getRange(`I7:I${6 + romRows.length}`).format.numberFormat = '0';
indexSheet.freezePanes.freezeRows(6);

sourceSheet.getRange('A2').values = [['Source catalog rows']];
sourceSheet.getRange('A3').values = [['Verbatim catalog fields from the first structured table in uprev ecus.txt. Source line is the line number in the supplied text file.']];
const sourceHeaders = ['Source line', 'Model', 'Make', 'Vehicle Year', 'Engine Code', 'Transmission', 'Master ROM', 'ROMs Updated'];
sourceSheet.getRange('A5:H5').values = [sourceHeaders];
sourceSheet.getRange(`A6:H${5 + sourceRows.length}`).values = sourceRows;
const sourceTable = sourceSheet.tables.add(`A5:H${5 + sourceRows.length}`, true, 'SourceCatalogRows');
sourceTable.style = 'TableStyleMedium2';
sourceTable.showFilterButton = true;
sourceSheet.getRange('A2:H3').format.font = { name: 'Arial', size: 10, color: '#242424' };
sourceSheet.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true, color: '#1F1F1F' };
sourceSheet.getRange('A5:H5').format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
sourceSheet.getRange('A:A').format.columnWidth = 13;
sourceSheet.getRange('B:B').format.columnWidth = 24;
sourceSheet.getRange('C:C').format.columnWidth = 14;
sourceSheet.getRange('D:D').format.columnWidth = 14;
sourceSheet.getRange('E:E').format.columnWidth = 18;
sourceSheet.getRange('F:F').format.columnWidth = 16;
sourceSheet.getRange('G:G').format.columnWidth = 17;
sourceSheet.getRange('H:H').format.columnWidth = 55;
sourceSheet.getRange(`A6:A${5 + sourceRows.length}`).format.numberFormat = '0';
sourceSheet.getRange(`D6:D${5 + sourceRows.length}`).format.numberFormat = '0';
sourceSheet.freezePanes.freezeRows(5);

await fs.mkdir(outputDir, { recursive: true });
workbook.recalculate();
const preview = await workbook.render({ sheetName: 'ROM to Model Year', range: 'A1:I18', format: 'png', scale: 1 });
await fs.writeFile(`${outputDir}/rom_model_year_preview.png`, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

const inspect = await workbook.inspect({ kind: 'workbook,sheet,table', maxChars: 1600, tableMaxRows: 4, tableMaxCols: 9 });
console.log(JSON.stringify({
  outputPath,
  sourceRows: sourceRows.length,
  expandedMappings: romRows.length,
  distinctCodes: distinctCodes.size,
  modelNames: modelNames.size,
  makes: [...makeNames].sort(),
  yearRange: [Math.min(...yearValues), Math.max(...yearValues)],
  codeAppearsInMultipleCatalogRows: multiVehicleCodes,
  masterCodeCaseOnlyMismatchCount: sourceRows.filter(row => !row[6].toUpperCase().split(',').some(code => code.trim() === row[7].toUpperCase())).length,
  inspect: inspect.ndjson,
}, null, 2));
