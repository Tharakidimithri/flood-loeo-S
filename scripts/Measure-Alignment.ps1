param([switch]$Sample)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
function Read-GeoHeader([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    $reader = [IO.BinaryReader]::new($stream)
    try {
        if ($reader.ReadUInt16() -ne 18761 -or $reader.ReadUInt16() -ne 42) { throw "Unsupported TIFF byte order or BigTIFF: $path" }
        $stream.Position = $reader.ReadUInt32()
        $count = $reader.ReadUInt16()
        $tags = @{}
        for ($i=0; $i -lt $count; $i++) {
            $id=[int]$reader.ReadUInt16(); $type=$reader.ReadUInt16(); $n=$reader.ReadUInt32(); $raw=$reader.ReadBytes(4)
            $next=$stream.Position
            if ($id -in @(256,257,33550,33922,34264,34735,34736,34737)) {
                $width = switch ($type) { 2 {1} 3 {2} 4 {4} 12 {8} default {throw "Unsupported tag type $type"} }
                if ($n*$width -gt 4) { $stream.Position=[BitConverter]::ToUInt32($raw,0); $raw=$reader.ReadBytes($n*$width) }
                if ($type -eq 2) { $tags[$id]=[Text.Encoding]::ASCII.GetString($raw,0,$n) }
                else {
                    $vals = for ($k=0; $k -lt $n; $k++) {
                        switch ($type) { 3 {[BitConverter]::ToUInt16($raw,2*$k)} 4 {[BitConverter]::ToUInt32($raw,4*$k)} 12 {[BitConverter]::ToDouble($raw,8*$k)} }
                    }
                    $tags[$id]=@($vals)
                }
            }
            $stream.Position=$next
        }
        if ($tags.ContainsKey(34264)) {
            $m=$tags[34264]; $affine=@($m[0],$m[1],$m[3],$m[4],$m[5],$m[7])
        } else {
            $s=$tags[33550]; $t=$tags[33922]
            if (!$s -or !$t -or $t.Count -ne 6) { throw "Missing or unsupported transform: $path" }
            $affine=@($s[0],0,($t[3]-$t[0]*$s[0]),0,(-$s[1]),($t[4]+$t[1]*$s[1]))
        }
        $keys=@{}; $g=$tags[34735]
        if (!$g) {throw "Missing GeoKeys: $path"}
        for ($k=4; $k -lt $g.Count; $k+=4) {
            $id=[int]$g[$k]; $loc=[int]$g[$k+1]; $n=[int]$g[$k+2]; $off=[int]$g[$k+3]
            if ($loc -eq 0) {$value=$off}
            elseif ($loc -eq 34737) {$value=$tags[34737].Substring($off,$n)}
            else {$value=@($tags[$loc][$off..($off+$n-1)])}
            $keys[[string]$id]=$value
        }
        return @{width=$tags[256][0];height=$tags[257][0];affine=$affine;keys=$keys}
    } finally {$reader.Dispose(); $stream.Dispose()}
}
$base=Join-Path $root 'data/sen1floods11/v1.1/data/flood_events/HandLabeled'
$files=Get-ChildItem (Join-Path $base 'S1Hand') -Filter '*_S1Hand.tif'
if ($Sample) {$files=@($files | Select-Object -First 1)}
$rows = foreach ($file in $files) {
    $chip=$file.BaseName -replace '_S1Hand$',''
    $a=Read-GeoHeader $file.FullName
    $b=Read-GeoHeader (Join-Path $base "LabelHand/${chip}_LabelHand.tif")
    $ta=$a.affine; $tb=$b.affine
    $det=$ta[0]*$ta[4]-$ta[1]*$ta[3]
    if ($det -eq 0) {throw "Singular transform: $chip"}
    $max=0.0
    foreach ($x in @(0,[double]$a.width)) { foreach ($y in @(0,[double]$a.height)) {
        $dx=($tb[0]-$ta[0])*$x+($tb[1]-$ta[1])*$y+($tb[2]-$ta[2])
        $dy=($tb[3]-$ta[3])*$x+($tb[4]-$ta[4])*$y+($tb[5]-$ta[5])
        $px=($ta[4]*$dx-$ta[1]*$dy)/$det
        $py=(-$ta[3]*$dx+$ta[0]*$dy)/$det
        $max=[Math]::Max($max,[Math]::Sqrt($px*$px+$py*$py))
    }}
    # Compare all numerical CRS/raster keys; descriptive citation text does not define the grid.
    $ids=@(@($a.keys.Keys)+@($b.keys.Keys) | Sort-Object -Unique)
    $different=@($ids | Where-Object { $_ -notin @(1026,2049,3073,4097) -and (ConvertTo-Json -Compress $a.keys[$_]) -ne (ConvertTo-Json -Compress $b.keys[$_]) })
    [pscustomobject]@{chip=$chip;max_corner_displacement_pixels=$max;dimensions_match=($a.width -eq $b.width -and $a.height -eq $b.height);numeric_geokeys_match=($different.Count -eq 0);different_keys=($different -join ',');image_transform=$ta;label_transform=$tb;image_geokeys=$a.keys;label_geokeys=$b.keys}
}
$rows | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $root 'reports/alignment_measurements.json')
$rows | Select-Object chip,max_corner_displacement_pixels,dimensions_match,numeric_geokeys_match,different_keys | Export-Csv (Join-Path $root 'reports/alignment_measurements.csv') -NoTypeInformation
$summary=[pscustomobject]@{pairs=@($rows).Count;maximum_pixel_displacement=($rows | Measure-Object max_corner_displacement_pixels -Maximum).Maximum;dimension_mismatches=@($rows | Where-Object {!$_.dimensions_match}).Count;geokey_mismatches=@($rows | Where-Object {!$_.numeric_geokeys_match}).Count;over_one_millionth_pixel=@($rows | Where-Object {$_.max_corner_displacement_pixels -gt 0.000001}).Count}
$summary | ConvertTo-Json | Set-Content (Join-Path $root 'reports/alignment_summary.json')
$summary | Format-List
if ($Sample) {$rows | ConvertTo-Json -Depth 8}


