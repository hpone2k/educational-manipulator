$ErrorActionPreference='Stop'
$app=[Runtime.InteropServices.Marshal]::GetActiveObject('SolidEdge.Application')
# Close only the two explicitly named API probe documents created during this build.
foreach($name in @('AX_horn_adapter.par','AX_horn_adapter_ordered.par')){
 for($i=$app.Documents.Count;$i -ge 1;$i--){$doc=$app.Documents.Item($i);if($doc.FullName -eq (Join-Path $PSScriptRoot $name)){$doc.Close($false)}}
}
$asm=$app.Documents.Open((Join-Path $PSScriptRoot 'EDU06_R01_LAYOUT_PROTOTYPE.asm'))
$asm.Activate()
$app.ActiveWindow.View.Fit()
$app.ActiveWindow.View.SaveAsImage((Join-Path $PSScriptRoot 'native-assembly-preview.jpg'),1800,1200)
$asm.Save()
Write-Output ('Assembly occurrences: '+$asm.Occurrences.Count)
