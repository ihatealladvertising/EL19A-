#!/usr/bin/env pwsh
# Extract 1D CURVE and VALUE declarations from A2L/XML files
# Analyze declaration order vs address order

param(
    [string]$V6Path = "C:\EL19A-repo\EVIDENCE\64811000p2_m.a2l",
    [string]$JukePath = "C:\EL19A-repo\EVIDENCE\RFCC_2XHK19BDF1.a2l",
    [string]$CF48DPath = "C:\EL19A-repo\EVIDENCE\CF48D.xml"
)

function Parse-A2L {
    param([string]$Path, [string]$SourceName)
    
    $content = Get-Content $Path -Raw
    $lines = $content -split "`r?`n"
    
    $results = @()
    $inCharacteristic = $false
    $currentChar = $null
    $ordinal = 0
    $lineNumber = 0
    $expectingTypeLine = $false
    
    foreach ($line in $lines) {
        $lineNumber++
        
        # Start of CHARACTERISTIC: "/begin CHARACTERISTIC    mSYMBOL"
        if ($line -match '^\s*/begin\s+CHARACTERISTIC\s+(\S+)') {
            $inCharacteristic = $true
            $expectingTypeLine = $true
            $ordinal++
            $symbol = $matches[1]
            $currentChar = @{
                Source = $SourceName
                Symbol = $symbol
                Type = $null
                Address = $null
                RecordLayout = $null
                PointCount = $null
                CompuMethod = $null
                AxisType = $null
                AxisMax = $null
                AxisConversion = $null
                AxisRef = $null
                FixAxisParDist = $null
                FunctionList = $null
                DeclarationOrdinal = $ordinal
                DeclarationLine = $lineNumber
            }
        }
        # End of CHARACTERISTIC
        elseif ($line -match '^\s*/end\s+CHARACTERISTIC') {
            if ($inCharacteristic -and $currentChar) {
                # Only keep CURVE and VALUE (1D)
                if ($currentChar.Type -in @('CURVE', 'VALUE')) {
                    $results += [pscustomobject]$currentChar
                }
            }
            $inCharacteristic = $false
            $currentChar = $null
            $expectingTypeLine = $false
        }
        # Inside CHARACTERISTIC - type/address line (comes after description line)
        elseif ($inCharacteristic -and $currentChar) {
            # Type and address line: "CURVE 0x0000C9A0 REC_UBYTE_C 0 COMP_0068 0 255"
            if ($line -match '^\s+(CURVE|VALUE)\s+(0x[0-9A-F]+)\s+(\S+)\s+(\d+)\s+(\S+)') {
                $currentChar.Type = $matches[1]
                $currentChar.Address = $matches[2]
                $currentChar.RecordLayout = $matches[3]
                # $matches[4] is usually 0 (reserved)
                $currentChar.CompuMethod = $matches[5]
                # Point count is after compu method for CURVE
                if ($matches[1] -eq 'CURVE' -and $line -match '^\s+CURVE\s+0x[0-9A-F]+\s+\S+\s+\d+\s+\S+\s+(\d+)\s+(\S+)') {
                    $currentChar.PointCount = [int]$matches[1]
                }
                $expectingTypeLine = $false
            }
            # AXIS_DESCR FIX_AXIS
            elseif ($line -match '/begin\s+AXIS_DESCR\s+FIX_AXIS') {
                $currentChar.AxisType = 'FIX_AXIS'
            }
            # AXIS_DESCR COM_AXIS
            elseif ($line -match '/begin\s+AXIS_DESCR\s+COM_AXIS') {
                $currentChar.AxisType = 'COM_AXIS'
            }
            # NO_INPUT_QUANTITY COMP_0205_S 3 0 2
            elseif ($line -match 'NO_INPUT_QUANTITY\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)') {
                $currentChar.AxisConversion = $matches[1]
                $currentChar.AxisMax = [int]$matches[2]
            }
            # AXIS_PTS_REF
            elseif ($line -match 'AXIS_PTS_REF\s+(\S+)') {
                $currentChar.AxisRef = $matches[1]
            }
            # FIX_AXIS_PAR_DIST 0 1 3
            elseif ($line -match 'FIX_AXIS_PAR_DIST\s+(\S+)\s+(\S+)\s+(\S+)') {
                $currentChar.FixAxisParDist = "$($matches[1]) $($matches[2]) $($matches[3])"
            }
            # FUNCTION_LIST
            elseif ($line -match '/begin\s+FUNCTION_LIST') {
                $currentChar.FunctionList = ''
            }
            elseif ($line -match '/end\s+FUNCTION_LIST') {
                # keep whatever was captured
            }
            elseif ($currentChar.FunctionList -ne $null -and $line -match '^\s+(\S.*)') {
                $currentChar.FunctionList += $matches[1].Trim() + '; '
            }
        }
    }
    return $results
}

function Parse-CF48D {
    param([string]$Path)
    
    $xml = [xml](Get-Content $Path -Raw)
    $results = @()
    $ordinal = 0
    
    foreach ($table in $xml.rom.table) {
        $ordinal++
        $name = $table.name
        $addr = $table.storageaddress
        
        $results += [pscustomobject]@{
            Source = 'CF48D'
            Symbol = $name
            Type = 'TABLE'
            Address = $addr
            RecordLayout = ''
            PointCount = $null
            CompuMethod = ''
            AxisType = ''
            AxisMax = $null
            AxisConversion = ''
            AxisRef = ''
            FixAxisParDist = ''
            FunctionList = ''
            DeclarationOrdinal = $ordinal
            DeclarationLine = $ordinal
        }
    }
    return $results
}

# Parse all three sources
Write-Host "Parsing V6 A2L..."
$v6Decls = Parse-A2L $V6Path "V6"
Write-Host "  Found $($v6Decls.Count) 1D CURVE/VALUE declarations"

Write-Host "Parsing Juke/X12C A2L..."
$jukeDecls = Parse-A2L $JukePath "Juke"
Write-Host "  Found $($jukeDecls.Count) 1D CURVE/VALUE declarations"

Write-Host "Parsing CF48D XML..."
$cf48dDecls = Parse-CF48D $CF48DPath
Write-Host "  Found $($cf48dDecls.Count) table declarations"

# Analyze each source: declaration order vs address order
function Analyze-Order {
    param([string]$Label, [array]$Decls)
    
    # Sort by declaration ordinal (already in order)
    $byDecl = $Decls | Sort-Object DeclarationOrdinal
    
    # Sort by address
    $byAddr = $Decls | Sort-Object { [int]('0x' + $_.Address.TrimStart('0x')) }
    
    # Compare
    $n = $byDecl.Count
    $inversions = 0
    $matches = 0
    
    for ($i = 0; $i -lt $n; $i++) {
        $declSym = $byDecl[$i].Symbol
        $addrSym = $byAddr[$i].Symbol
        if ($declSym -eq $addrSym) { $matches++ }
    }
    
    # Count inversions: pairs (i,j) where i<j but addr(i) > addr(j)
    for ($i = 0; $i -lt $n; $i++) {
        $addrI = [int]('0x' + $byDecl[$i].Address.TrimStart('0x'))
        for ($j = $i+1; $j -lt $n; $j++) {
            $addrJ = [int]('0x' + $byDecl[$j].Address.TrimStart('0x'))
            if ($addrI -gt $addrJ) { $inversions++ }
        }
    }
    
    # Monotonic runs
    $runs = 1
    for ($i = 1; $i -lt $n; $i++) {
        $addrPrev = [int]('0x' + $byDecl[$i-1].Address.TrimStart('0x'))
        $addrCurr = [int]('0x' + $byDecl[$i].Address.TrimStart('0x'))
        if ($addrCurr -lt $addrPrev) { $runs++ }
    }
    
    # Duplicate/shared addresses
    $addrGroups = $Decls | Group-Object Address | Where-Object Count -gt 1
    $duplicates = $addrGroups.Count
    $dupEntries = $addrGroups | Select-Object -ExpandProperty Group
    
    # Output
    Write-Host "`n=== $Label ==="
    Write-Host "Total 1D declarations: $n"
    Write-Host "Exact position matches (decl order = addr order): $matches / $n"
    Write-Host "Inversions: $inversions"
    Write-Host "Monotonic runs: $runs"
    Write-Host "Duplicate/shared addresses: $duplicates groups"
    if ($duplicates -gt 0) {
        $dupEntries | Group-Object Address | ForEach-Object {
            Write-Host "  Address $($_.Name): $($_.Group.Symbol -join ', ')"
        }
    }
    
    # Show first 20 in declaration order with addresses
    Write-Host "`nFirst 20 in declaration order:"
    $byDecl | Select-Object -First 20 | ForEach-Object {
        $addr = [int]('0x' + $_.Address.TrimStart('0x'))
        Write-Host "  Ordinal $($_.DeclarationOrdinal): $($_.Symbol) @ 0x$($_.Address) ($($_.Type) $($_.RecordLayout) pts=$($_.PointCount) axis=$($_.AxisType)/$($_.AxisMax) compu=$($_.CompuMethod))"
    }
    
    # Show first 20 in address order
    Write-Host "`nFirst 20 in address order:"
    $byAddr | Select-Object -First 20 | ForEach-Object {
        $addr = [int]('0x' + $_.Address.TrimStart('0x'))
        Write-Host "  $($_.Symbol) @ 0x$($_.Address) (decl ordinal $($_.DeclarationOrdinal))"
    }
    
    return @{
        Label = $Label
        Total = $n
        Matches = $matches
        Inversions = $inversions
        Runs = $runs
        Duplicates = $duplicates
        ByDecl = $byDecl
        ByAddr = $byAddr
    }
}

# Run analysis
$v6Analysis = Analyze-Order "V6" $v6Decls
$jukeAnalysis = Analyze-Order "Juke/X12C" $jukeDecls
$cf48dAnalysis = Analyze-Order "CF48D" $cf48dDecls

# Cross-source comparison: symbols that appear in multiple sources
Write-Host "`n=== Cross-source symbol overlap ==="
$allSymbols = @{}
$v6Decls | ForEach-Object { $allSymbols[$_.Symbol] = @{V6=$true; Juke=$false; CF48D=$false; V6Obj=$_; JukeObj=$null; CF48DObj=$null } }
$jukeDecls | ForEach-Object { 
    if ($allSymbols.ContainsKey($_.Symbol)) { 
        $allSymbols[$_.Symbol].Juke = $true; 
        $allSymbols[$_.Symbol].JukeObj = $_ 
    } else { 
        $allSymbols[$_.Symbol] = @{V6=$false; Juke=$true; CF48D=$false; V6Obj=$null; JukeObj=$_; CF48DObj=$null } 
    }
}
$cf48dDecls | ForEach-Object { 
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

Write-Host "In all three sources: $($inAllThree.Count)"
Write-Host "In V6+Juke only: $($inV6Juke.Count)"
Write-Host "In V6+CF48D only: $($inV6CF48D.Count)"
Write-Host "In Juke+CF48D only: $($inJukeCF48D.Count)"
Write-Host "Only V6: $($onlyV6.Count)"
Write-Host "Only Juke: $($onlyJuke.Count)"
Write-Host "Only CF48D: $($onlyCF48D.Count)"

# For shared symbols, compare addresses
Write-Host "`n=== Address comparison for shared symbols (V6 vs Juke) ==="
$sharedV6Juke = $inV6Juke + $inAllThree
if ($sharedV6Juke.Count -gt 0) {
    $sharedV6Juke | ForEach-Object {
        $v6Addr = [int]('0x' + $_.V6Obj.Address.TrimStart('0x'))
        $jukeAddr = [int]('0x' + $_.JukeObj.Address.TrimStart('0x'))
        $diff = $jukeAddr - $v6Addr
        if ($v6Addr -eq $jukeAddr) { $match = "MATCH" } else { $match = "DIFF" }
        Write-Host "  $($_.V6Obj.Symbol): V6=0x$($_.V6Obj.Address) Juke=0x$($_.JukeObj.Address) diff=0x{0:X} ($match)" -f $diff
    }
}

# Export detailed data for report
$v6Decls | Export-Csv "C:\EL19A-repo\CONTROL\WO65285_V6_1D.csv" -NoTypeInformation
$jukeDecls | Export-Csv "C:\EL19A-repo\CONTROL\WO65285_Juke_1D.csv" -NoTypeInformation
$cf48dDecls | Export-Csv "C:\EL19A-repo\CONTROL\WO65285_CF48D_1D.csv" -NoTypeInformation

Write-Host "`nExported CSV files to CONTROL/"