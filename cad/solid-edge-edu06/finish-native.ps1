param([switch]$AssemblyOnly)
$ErrorActionPreference='Stop'
$app=[Runtime.InteropServices.Marshal]::GetActiveObject('SolidEdge.Application')
$root=$PSScriptRoot
$data=Get-Content (Join-Path $root 'design.json') -Raw | ConvertFrom-Json
if(-not $AssemblyOnly){foreach($part in $data.parts){
 $doc=$app.Documents.Open((Join-Path $root ('parts/'+$part.name+'.par')))
 $body=$doc.Models.Item(1).Body
 $style=$doc.FaceStyles.Add('EDU06 R01 material', $body.Style.Name)
 if($part.category -match 'motor'){$style.SetDiffuse([single]0.13,[single]0.16,[single]0.18)}
 elseif($part.category -match 'purchased'){$style.SetDiffuse([single]0.65,[single]0.69,[single]0.73)}
 elseif($part.name -match 'gear|pinion|rack'){$style.SetDiffuse([single]0.67,[single]0.79,[single]0.65)}
 else{$style.SetDiffuse([single]0.12,[single]0.37,[single]0.31)}
 $body.Style=$style
 $doc.Save()
 $doc.Close($false)
}}
$asm=$app.Documents.Open((Join-Path $root 'EDU06_R01_LAYOUT_PROTOTYPE.asm'))
$index=0
foreach($item in $data.placements){
 $index++
 if($index -le $asm.Occurrences.Count){$occ=$asm.Occurrences.Item($index);$occ.Replace((Join-Path $root ('parts/'+$item.part+'.par')),$false)}
 else{$occ=$asm.Occurrences.AddByFilename((Join-Path $root ('parts/'+$item.part+'.par')))}
 $occ.PutTransform($item.position[0]/1000,$item.position[1]/1000,$item.position[2]/1000,$item.rotation[0]*[Math]::PI/180,$item.rotation[1]*[Math]::PI/180,$item.rotation[2]*[Math]::PI/180)
 $occ.Name=('{0:D2} {1}' -f $index,$item.label)
}
$view=$app.ActiveWindow.View
$view.Fit()
$asm.Save()
$asm.SaveAs((Join-Path $root 'EDU06_R01_LAYOUT_PROTOTYPE.stp'))
Write-Output "Styled native parts; positioned $index occurrences; saved assembly."
