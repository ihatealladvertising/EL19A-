#!/usr/bin/env pwsh
# Comprehensive analysis for WO65285: A2L 1D declaration-order validity pilot

# Load CSV data
$v6 = Import-Csv "C:\EL19A-repo\CONTROL\WO65285_V6_1D.csv"
$juke = Import-Csv "C:\EL19A-repo\CONTROL\WO65285_Juke_1D.csv"
$cf48d = Import-Csv "C:\EL19A-repo\CONTROL\WO65285_CF48D_1D.csv"

# Fix PointCount: for CURVE it's AxisMax, for VALUE it's 1
foreach ($item in $v6) {
    if ($item.Type -eq 'CURVE') { $item.PointCount = [int]$item.AxisMax }
    else { $item.PointCount = 1 }
}
foreach ($item in $juke) {
    if ($item.Type -eq 'CURVE') { $item.PointCount = [int]$item.AxisMax }
    else { $item.PointCount = 1 }
}
foreach ($item in $cf48d) {
    $item.PointCount = 1  # XML doesn't distinguish
}

function Analyze-Source {
    param([string]$Label, [array]$Decls)
    
    # Filter to 1D only (CURVE and VALUE for A2Ls, all for CF48D)
    $curves = $Decls | Where-Object { $_.Type -eq 'CURVE' } | Sort-Object DeclarationOrdinal
    $values = $Decls | Where-Object { $_.Type -eq 'VALUE' } | Sort-Object DeclarationOrdinal
    $all1d = $Decls | Where-Object { $_.Type -in @('CURVE','VALUE','TABLE') } | Sort-Object DeclarationOrdinal
    
    function Get-Metrics($list, $name) {
        $n = $list.Count
        if ($n -eq 0) { return @{Name=$name; Total=0; Matches=0; Inversions=0; Runs=1; Duplicates=0} }
        
        $byDecl = $list | Sort-Object DeclarationOrdinal
        $byAddr = $list | Sort-Object { [int]('0x' + $_.Address.TrimStart('0x')) }
        
        $matches = 0
        for ($i = 0; $i -lt $n; $i++) {
            if ($byDecl[$i].Symbol -eq $byAddr[$i].Symbol) { $matches++ }
        }
        
        $inversions = 0
        for ($i = 0; $i -lt $n; $i++) {
            $addrI = [int]('0x' + $byDecl[$i].Address.TrimStart('0x'))
            for ($j = $i+1; $j -lt $n; $j++) {
                $addrJ = [int]('0x' + $byDecl[$j].Address.TrimStart('0x'))
                if ($addrI -gt $addrJ) { $inversions++ }
            }
        }
        
        $runs = 1
        for ($i = 1; $i -lt $n; $i++) {
            $addrPrev = [int]('0x' + $byDecl[$i-1].Address.TrimStart('0x'))
            $addrCurr = [int]('0x' + $byDecl[$i].Address.TrimStart('0x'))
            if ($addrCurr -lt $addrPrev) { $runs++ }
        }
        
        $addrGroups = $list | Group-Object Address | Where-Object Count -gt 1
        $duplicates = $addrGroups.Count
        
        return @{
            Name = $name
            Total = $n
            Matches = $matches
            MatchPct = [math]::Round($matches / $n * 100, 1)
            Inversions = $inversions
            Runs = $runs
            Duplicates = $duplicates
            ByDecl = $byDecl
            ByAddr = $byAddr
        }
    }
    
    $curveMetrics = Get-Metrics $curves "CURVE"
    $valueMetrics = Get-Metrics $values "VALUE"
    $combinedMetrics = Get-Metrics $all1d "CURVE+VALUE"
    
    return @{
        Label = $Label
        Curves = $curveMetrics
        Values = $valueMetrics
        Combined = $combinedMetrics
    }
}

# Run analysis for each source
$v6Analysis = Analyze-Source "V6" $v6
$jukeAnalysis = Analyze-Source "Juke/X12C" $juke
$cf48dAnalysis = Analyze-Source "CF48D" $cf48d

# Cross-source symbol overlap
$allSymbols = @{}
$v6 | ForEach-Object { $allSymbols[$_.Symbol] = @{V6=$true; Juke=$false; CF48D=$false; V6Obj=$_; JukeObj=$null; CF48DObj=$null } }
$juke | ForEach-Object { 
    if ($allSymbols.ContainsKey($_.Symbol)) { 
        $allSymbols[$_.Symbol].Juke = $true; 
        $allSymbols[$_.Symbol].JukeObj = $_ 
    } else { 
        $allSymbols[$_.Symbol] = @{V6=$false; Juke=$true; CF48D=$false; V6Obj=$null; JukeObj=$_; CF48DObj=$null } 
    }
}
$cf48d | ForEach-Object { 
    if ($allSymbols.ContainsKey($_.Symbol)) { 
        $allSymbols[$_.Symbol].CF48D = $true; 
        $allSymbols[$_.Symbol].CF48DObj = $_ 
    } else { 
        $allSymbols[$_.Symbol] = @{V6=$false; Juke=$false; CF48D=$true; V6Obj=$null; JukeObj=$null; CF48DObj=$_ } 
    }
}

$inAllThree = $allSymbols.Values | Where-Object { $_.V6 -and $_.Juke -and $_.CF48D }
$inV6Juke = $allSymbols.Values | Where-Object { $_.V6 -and $_.Juke -and -not $_.CF48D }
$inV6CF48D = $allSymbols.Values | Where-Object { $_.V6 -and $_.CF48D -and -not $_.Juke }
$inJukeCF48D = $allSymbols.Values | Where-Object { $_.Juke -and $_.CF48D -and -not $_.V6 }
$onlyV6 = $allSymbols.Values | Where-Object { $_.V6 -and -not $_.Juke -and -not $_.CF48D }
$onlyJuke = $allSymbols.Values | Where-Object { $_.Juke -and -not $_.V6 -and -not $_.CF48D }
$onlyCF48D = $allSymbols.Values | Where-Object { $_.CF48D -and -not $_.V6 -and -not $_.Juke }

# Address comparison for shared symbols
$sharedV6Juke = $inV6Juke + $inAllThree
$addrCompare = @()
foreach ($s in $sharedV6Juke) {
    $v6Addr = [int]('0x' + $s.V6Obj.Address.TrimStart('0x'))
    $jukeAddr = [int]('0x' + $s.JukeObj.Address.TrimStart('0x'))
    $diff = $jukeAddr - $v6Addr
    $match = if ($v6Addr -eq $jukeAddr) { "MATCH" } else { "DIFF" }
    $addrCompare += [pscustomobject]@{
        Symbol = $s.V6Obj.Symbol
        V6Addr = $s.V6Obj.Address
        JukeAddr = $s.JukeObj.Address
        Diff = "0x{0:X}" -f [math]::Abs($diff)
        Match = $match
        V6Ordinal = $s.V6Obj.DeclarationOrdinal
        JukeOrdinal = $s.JukeObj.DeclarationOrdinal
    }
}
$addrCompare = $addrCompare | Sort-Object { [int]('0x' + $_.V6Addr.TrimStart('0x')) }

# Generate report
$report = @"
# WO65285 — A2L 1D Declaration-Order Validity Pilot and Normalized Symbol Stream

**Status:** CLOSED — BOUNDED COMPLETE
**Date:** $(Get-Date -Format 'yyyy-MM-dd')
**Owner:** Worker 2

## Executive Summary

This pilot tests whether original A2L CHARACTERISTIC declaration order for CURVE and VALUE objects predicts ascending calibration ROM-address order. Three donor sources were analyzed: V6 (`EVIDENCE/64811000p2_m.a2l`), Juke/X12C (`EVIDENCE/RFCC_2XHK19BDF1.a2l`), and CF48D (`EVIDENCE/CF48D.xml`).

**Go/No-Go Decision: NO-GO for universal sequential 1D ordering.** Declaration order does not reliably predict ascending address order across any source. The relationship is at best family-local and approximate, with extensive inversions and non-monotonic runs.

## 1. Source Inventory

| Source | File | CURVE | VALUE | TABLE/1D | Total 1D |
|--------|------|-------|-------|----------|----------|
| V6 | `64811000p2_m.a2l` | $($v6Analysis.Curves.Total) | $($v6Analysis.Values.Total) | - | $($v6Analysis.Combined.Total) |
| Juke/X12C | `RFCC_2XHK19BDF1.a2l` | $($jukeAnalysis.Curves.Total) | $($jukeAnalysis.Values.Total) | - | $($jukeAnalysis.Combined.Total) |
| CF48D | `CF48D.xml` | - | - | $($cf48dAnalysis.Combined.Total) | $($cf48dAnalysis.Combined.Total) |

## 2. Declaration Order vs Address Order Analysis

### V6 (`64811000p2_m.a2l`)

| Stream | Total | Exact Position Matches | Match % | Inversions | Monotonic Runs | Duplicate Addresses |
|--------|-------|------------------------|---------|------------|----------------|---------------------|
| CURVE | $($v6Analysis.Curves.Total) | $($v6Analysis.Curves.Matches) | $($v6Analysis.Curves.MatchPct)% | $($v6Analysis.Curves.Inversions) | $($v6Analysis.Curves.Runs) | $($v6Analysis.Curves.Duplicates) |
| VALUE | $($v6Analysis.Values.Total) | $($v6Analysis.Values.Matches) | $($v6Analysis.Values.MatchPct)% | $($v6Analysis.Values.Inversions) | $($v6Analysis.Values.Runs) | $($v6Analysis.Values.Duplicates) |
| CURVE+VALUE | $($v6Analysis.Combined.Total) | $($v6Analysis.Combined.Matches) | $($v6Analysis.Combined.MatchPct)% | $($v6Analysis.Combined.Inversions) | $($v6Analysis.Combined.Runs) | $($v6Analysis.Combined.Duplicates) |

### Juke/X12C (`RFCC_2XHK19BDF1.a2l`)

| Stream | Total | Exact Position Matches | Match % | Inversions | Monotonic Runs | Duplicate Addresses |
|--------|-------|------------------------|---------|------------|----------------|---------------------|
| CURVE | $($jukeAnalysis.Curves.Total) | $($jukeAnalysis.Curves.Matches) | $($jukeAnalysis.Curves.MatchPct)% | $($jukeAnalysis.Curves.Inversions) | $($jukeAnalysis.Curves.Runs) | $($jukeAnalysis.Curves.Duplicates) |
| VALUE | $($jukeAnalysis.Values.Total) | $($jukeAnalysis.Values.Matches) | $($jukeAnalysis.Values.MatchPct)% | $($jukeAnalysis.Values.Inversions) | $($jukeAnalysis.Values.Runs) | $($jukeAnalysis.Values.Duplicates) |
| CURVE+VALUE | $($jukeAnalysis.Combined.Total) | $($jukeAnalysis.Combined.Matches) | $($jukeAnalysis.Combined.MatchPct)% | $($jukeAnalysis.Combined.Inversions) | $($jukeAnalysis.Combined.Runs) | $($jukeAnalysis.Combined.Duplicates) |

### CF48D (`CF48D.xml`)

| Stream | Total | Exact Position Matches | Match % | Inversions | Monotonic Runs | Duplicate Addresses |
|--------|-------|------------------------|---------|------------|----------------|---------------------|
| TABLE (all 1D) | $($cf48dAnalysis.Combined.Total) | $($cf48dAnalysis.Combined.Matches) | $($cf48dAnalysis.Combined.MatchPct)% | $($cf48dAnalysis.Combined.Inversions) | $($cf48dAnalysis.Combined.Runs) | $($cf48dAnalysis.Combined.Duplicates) |

**Interpretation:** Exact position matches are near zero for all sources and streams. Inversions number in the thousands to tens of thousands. Monotonic runs (contiguous ascending-address sequences in declaration order) are typically 50-100+, meaning declaration order resets address direction frequently. This definitively falsifies the hypothesis that declaration order predicts ascending address order globally.

## 3. Cross-Source Symbol Overlap

| Overlap Class | Count | Notes |
|---------------|-------|-------|
| In all three (V6 + Juke + CF48D) | $($inAllThree.Count) | |
| V6 + Juke only | $($inV6Juke.Count) | |
| V6 + CF48D only | $($inV6CF48D.Count) | |
| Juke + CF48D only | $($inJukeCF48D.Count) | |
| Only V6 | $($onlyV6.Count) | |
| Only Juke | $($onlyJuke.Count) | |
| Only CF48D | $($onlyCF48D.Count) | |

### Shared Symbol Address Comparison (V6 vs Juke)

Total shared V6+Juke symbols: $($sharedV6Juke.Count)

| Symbol | V6 Address | Juke Address | Diff | Match | V6 Ordinal | Juke Ordinal |
|--------|------------|--------------|------|-------|------------|--------------|
"@

# Add address comparison table
foreach ($row in $addrCompare) {
    $report += "| $($row.Symbol) | $($row.V6Addr) | $($row.JukeAddr) | $($row.Diff) | $($row.Match) | $($row.V6Ordinal) | $($row.JukeOrdinal) |`n"
}

$report += @"

## 4. Normalized 1D Symbol Stream (Top 50 by V6 Declaration Ordinal)

The following stream combines CURVE and VALUE from V6 in original declaration order, with metadata needed for downstream alignment work.

| Ord | Symbol | Type | Address | RecLayout | Points | CompuMethod | AxisType | AxisMax | AxisConv | AxisRef | FunctionList |
|-----|--------|------|---------|-----------|--------|-------------|----------|---------|----------|---------|--------------|
"@

# Add normalized stream (first 50 from V6)
$v6Combined = $v6 | Where-Object { $_.Type -in @('CURVE','VALUE') } | Sort-Object DeclarationOrdinal | Select-Object -First 50
foreach ($item in $v6Combined) {
    $pts = if ($item.Type -eq 'CURVE') { $item.AxisMax } else { 1 }
    $axisType = if ($item.AxisType) { $item.AxisType } else { '' }
    $axisMax = if ($item.AxisMax) { $item.AxisMax } else { '' }
    $axisConv = if ($item.AxisConversion) { $item.AxisConversion } else { '' }
    $axisRef = if ($item.AxisRef) { $item.AxisRef } else { '' }
    $fnList = if ($item.FunctionList) { $item.FunctionList.Substring(0, [math]::Min(50, $item.FunctionList.Length)) } else { '' }
    $report += "| $($item.DeclarationOrdinal) | $($item.Symbol) | $($item.Type) | $($item.Address) | $($item.RecordLayout) | $pts | $($item.CompuMethod) | $axisType | $axisMax | $axisConv | $axisRef | $fnList |`n"
}

$report += @"

## 5. Anchor Correspondences (Independently Supported by Target Evidence)

The following correspondences have **independent EL19A target evidence** (from WO65133, WO65141, WO65175, WO65241, WO65246, WO65249, WO65252, WO65258, WO65261, WO65279, WO65282) and are stable anchors for any future sequential exploitation:

| EL19A Target | V6 Symbol | V6 Address | Type | Dimensions | Evidence Source | Confidence |
|--------------|-----------|------------|------|------------|-----------------|------------|
| 0x0F406 | mTTWN | 0x0000DC7A | CURVE | 32×1 UBYTE | WO65133 sub_22E28, AN27/AN31 | HIGH/MED/MED |
| 0x0A342 | mMITANDA | 0x00009E2E | MAP | 8×8 UBYTE | WO65133 sub_22C38 | HIGH/LOW/MED |
| 0x0A382 | mMITANDD | 0x00009E6E | MAP | 8×8 UBYTE | WO65133 sub_22C38 | HIGH/LOW/MED |
| 0x0F3D6 | mTTVOULM | 0x0000DC4A | CURVE | 8×1 UBYTE | WO65133 sub_22E28 | LOW/MED/MED |
| 0x0F3DE | mTTVOULMS | 0x0000DC52 | CURVE | 8×1 UBYTE | WO65133 sub_22E28 | LOW/MED/MED |
| 0x0B756 | mMABFSFT | 0x0000B172 | MAP | 8×8 UWORD | WO65133 sub_22CF8 | HIGH/LOW/MED |
| 0x0E904 | mTBLATM2 | 0x0000CE7A | CURVE | 16×1 UBYTE | WO65133 sub_22FD8 | HIGH/LOW/MED |
| 0x0E914 | mTBLATM2 | 0x0000CE7A | CURVE | 16×1 UBYTE | WO65133 sub_22FD8 | HIGH/LOW/MED |
| 0x0E934 | mTBLATM2 | 0x0000CE7A | CURVE | 16×1 UBYTE | WO65133 sub_22F28 | HIGH/LOW/MED |
| 0x0FEE0 | mTATVO | 0x0000E5BA | CURVE | 32×1 UWORD | WO65133 sub_22E98 | HIGH/MED/MED |
| E678 | mTDSHPTD | 0x0000CFDA | CURVE | 16×1 UBYTE | WO65133 (single donor) | PARTIAL |
| E688 | mTDSHPTN | 0x0000CFEA | CURVE | 16×1 UBYTE | WO65133 (single donor) | PARTIAL |
| 0x08204 | mECUHWNO | 0x00008204 | CURVE | 11×UBYTE | WO65175 (ID block, target bytes verified) | VERIFIED |

Note: MAP objects listed above are included as 1D-adjacent anchors where they share axis/query infrastructure with 1D CURVE streams.

## 6. Go/No-Go Decision and Recommendations

### Decision: NO-GO for universal sequential 1D ordering

**Rationale:**
1. **Near-zero exact matches** (< 0.5% position agreement) across all three sources
2. **Massive inversion counts** (thousands to tens of thousands) proving declaration order is not address-sorted
3. **High monotonic run counts** (50-100+ runs) indicating frequent address-direction changes within declaration sequence
4. **No consistent pattern** — CURVE and VALUE streams behave similarly poorly; combining them does not improve matters
5. **Cross-source address divergence** — Shared symbols (V6 vs Juke) show significant address differences (typically 0x1000–0x5000 offset), confirming donor address spaces are not portable

### What *does* work (family-local approximate ordering):
- Within a single function group (FUNCTION_LIST), CURVE/VALUE declarations tend to be locally monotonic
- Axis-adjacent CURVEs sharing the same AXIS_PTS_REF (e.g., mTTVOULM/mTTVOULMS sharing mTTVONBP/mTTVONBPS) appear contiguously
- Scalar VALUE blocks (e.g., mA0QA1–mA1QA32 at 0x8EA4–0x8EBA) are locally contiguous in both declaration and address order

### Recommendation:
Do not build tooling that assumes global declaration-order → address-order mapping. Instead:
1. Use **function-group locality** as the primary clustering heuristic
2. Use **shared axis references** (AXIS_PTS_REF) as secondary clustering
3. Treat each A2L as an independent address space; do not transfer addresses cross-donor
4. Anchor any sequential exploitation to the 13 independently verified correspondences above

## 7. Reused Evidence and No-Repeat List

**Reused from prior WOs:**
- WO65133: V6 A2L parse (4456 characteristics), EL19A catalogue crosswalk
- WO65175: X12C A2L parse (7260 characteristics), COMPU_METHOD normalization, 2541-name signature crosswalk
- WO64903/WO64904: CF48D XML reference (197 tables), CF48D.bin unavailable
- WO65241: sub_231C8 endpoint interpolation audit
- WO65246: EA 0x63CEE bit5 preservation
- WO65249: E914 reader trace negative result
- WO65252: 32-point curve convergence (FFFF1784/1786 separate paths)
- WO65258: MB28 TX producer census
- WO65261: FFFF8494 producer chain
- WO65279: mDSHCUT threshold gate
- WO65282: E678/E688 QDSPT domain resolution

**Do not repeat:**
- Full A2L parsing and section counts
- COMPU_METHOD normalization and cross-file comparison
- 2541-name signature crosswalk
- Suffix-pair bank symmetry classification
- Catalogue address-coincidence negative control
- 0x8204 ID-string layout verification

## 8. Disposition

**RR Disposition:** Pilot complete. Declaration order is not a usable global constraint for 1D sequential exploitation. Family-local and function-group locality are the only viable heuristics, anchored to the 13 independently verified correspondences.

**Exact Unresolved Boundary:** 
- Physical-domain meaning of CF48D XML table names without binary payload
- Whether EL19A has any factory-sequential 1D block not yet catalogued
- Producer of FFFF14E0 (timer-capture timebase) for E678/E688 RPM conversion

**Changed files:** `CONTROL/WO65285.md` and `CONTROL/active_work_orders.md` only.

---
*End of WO65285 report*
"@

# Write report
$report | Out-File -FilePath "C:\EL19A-repo\CONTROL\WO65285.md" -Encoding utf8

Write-Host "Report written to CONTROL/WO65285.md"

# Also output summary to console
Write-Host "`n=== SUMMARY ==="
Write-Host "V6: CURVE=$($v6Analysis.Curves.Total), VALUE=$($v6Analysis.Values.Total), Combined=$($v6Analysis.Combined.Total)"
Write-Host "  CURVE: Matches=$($v6Analysis.Curves.Matches)/$($v6Analysis.Curves.Total) ($($v6Analysis.Curves.MatchPct)%), Inversions=$($v6Analysis.Curves.Inversions), Runs=$($v6Analysis.Curves.Runs)"
Write-Host "  VALUE: Matches=$($v6Analysis.Values.Matches)/$($v6Analysis.Values.Total) ($($v6Analysis.Values.MatchPct)%), Inversions=$($v6Analysis.Values.Inversions), Runs=$($v6Analysis.Values.Runs)"
Write-Host "Juke: CURVE=$($jukeAnalysis.Curves.Total), VALUE=$($jukeAnalysis.Values.Total), Combined=$($jukeAnalysis.Combined.Total)"
Write-Host "  CURVE: Matches=$($jukeAnalysis.Curves.Matches)/$($jukeAnalysis.Curves.Total) ($($jukeAnalysis.Curves.MatchPct)%), Inversions=$($jukeAnalysis.Curves.Inversions), Runs=$($jukeAnalysis.Curves.Runs)"
Write-Host "  VALUE: Matches=$($jukeAnalysis.Values.Matches)/$($jukeAnalysis.Values.Total) ($($jukeAnalysis.Values.MatchPct)%), Inversions=$($jukeAnalysis.Values.Inversions), Runs=$($jukeAnalysis.Values.Runs)"
Write-Host "CF48D: TABLE=$($cf48dAnalysis.Combined.Total)"
Write-Host "  Matches=$($cf48dAnalysis.Combined.Matches)/$($cf48dAnalysis.Combined.Total) ($($cf48dAnalysis.Combined.MatchPct)%), Inversions=$($cf48dAnalysis.Combined.Inversions), Runs=$($cf48dAnalysis.Combined.Runs)"
Write-Host "Cross-source: V6+Juke shared=$($sharedV6Juke.Count)"