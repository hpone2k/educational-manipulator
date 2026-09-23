param([switch]$All)
$ErrorActionPreference='Stop'
$lib='C:\Program Files\Siemens\Solid Edge 2021\Program'
$refs=@('interop.SolidEdgeFrameworkLib.dll','interop.SolidEdgeAssemblyLib.dll') | ForEach-Object {Join-Path $lib $_}
foreach($ref in $refs){$null=[Reflection.Assembly]::LoadFrom($ref)}
Add-Type -Path (Join-Path $PSScriptRoot 'CheckMotion.cs') -ReferencedAssemblies ($refs+@('System.Web.Extensions','System.Core'))
try{[CheckMotion]::Run($PSScriptRoot,[bool]$All)}catch{Write-Output $_.Exception.ToString();exit 1}
