$ErrorActionPreference='Stop'
$lib='C:\Program Files\Siemens\Solid Edge 2021\Program'
$refs=@('interop.SolidEdgeFrameworkLib.dll','interop.SolidEdgePartLib.dll','interop.SolidEdgeFrameworkSupportLib.dll','interop.SolidEdgeGeometryLib.dll','interop.SolidEdgeAssemblyLib.dll') | ForEach-Object {Join-Path $lib $_}
foreach($ref in $refs){$null=[Reflection.Assembly]::LoadFrom($ref)}
Add-Type -Path (Join-Path $PSScriptRoot 'NativeCad.cs') -ReferencedAssemblies ($refs + @('System.Web.Extensions','System.Core'))
try{[NativeCad]::Build($PSScriptRoot)}catch{Write-Output $_.Exception.ToString();if($_.Exception.InnerException){Write-Output $_.Exception.InnerException.ToString()};exit 1}
