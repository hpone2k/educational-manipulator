$ErrorActionPreference='Stop'
$app=[Runtime.InteropServices.Marshal]::GetActiveObject('SolidEdge.Application')
$doc=$app.Documents.Add('SolidEdge.PartDocument','C:\Program Files\Siemens\Solid Edge 2021\Template\ISO Metric\iso metric part.par')
$profile=$doc.ProfileSets.Add().Profiles.Add($doc.RefPlanes.Item(3))
$null=$profile.Circles2d.AddByCenterRadius(0,0,0.018)
$null=$profile.Circles2d.AddByCenterRadius(0,0,0.005)
foreach($i in 0..3){$t=$i*[Math]::PI/2;$null=$profile.Circles2d.AddByCenterRadius(0.008*[Math]::Cos($t),0.008*[Math]::Sin($t),0.00115)}
$status=$profile.End(1)
Write-Output "profile status $status"
$profiles=[Array]@($profile)
$m=$doc.Models.AddFiniteExtrudedProtrusion(1,[ref]$profiles,2,0.004)
$profile.Visible=$false
$path=Join-Path $PSScriptRoot 'AX_horn_adapter.par'
$doc.SaveAs($path)
$app.ActiveWindow.View.Fit()
$x1=0.0;$y1=0.0;$z1=0.0;$x2=0.0;$y2=0.0;$z2=0.0
$m.Body.GetRange([ref]$x1,[ref]$y1,[ref]$z1,[ref]$x2,[ref]$y2,[ref]$z2)
Write-Output "range $x1 $y1 $z1 / $x2 $y2 $z2"
$doc.SaveAs((Join-Path $PSScriptRoot 'AX_horn_adapter.stl'))
Write-Output 'SAVED'
