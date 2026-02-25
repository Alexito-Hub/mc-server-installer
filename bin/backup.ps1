$outdir = "backups"
if (-not (Test-Path $outdir)) { New-Item -ItemType Directory -Path $outdir | Out-Null }
$ts = Get-Date -Format yyyyMMdd-HHmmss
$zip = "$outdir/backup-$ts.zip"
$items = @('world','world_nether','world_the_end','plugins','server.properties','eula.txt')
Compress-Archive -Path $items -DestinationPath $zip -Force
Write-Output "Backup creado: $zip"
