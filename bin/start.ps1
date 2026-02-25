if (-not (Test-Path .\server.jar)) {
  Write-Error "No se encontró server.jar. Ejecuta 'python installer.py install' o usa el asistente primero."
  exit 1
}
java -jar server.jar nogui
