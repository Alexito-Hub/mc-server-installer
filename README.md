Minecraft — Proyecto inicial

Este proyecto automatiza la descarga y la configuración inicial de un servidor Minecraft profesional.

Características:
- Selección entre `paper` (PaperMC) y `vanilla` (Mojang)
- Selección de versión y descarga automática del jar correspondiente
- Genera `eula.txt`, `server.properties` y scripts de arranque multiplataforma
- Buenas prácticas y ejemplos de despliegue profesional en `docs/professional.md`


Requisitos:
- `python3` (>=3.8) para ejecutar `installer.py` (sin dependencias externas)
- `java` para ejecutar el servidor (configurable en `start.sh` / `start.ps1`)

Uso rápido (Python):
1. Ejecuta desde la carpeta `minecraft`:

```bash
python -m pip --version || true
python installer.py       # interactivo
# o modo no interactivo:
python installer.py -e paper -v latest --staging
```

2. Usa `./start.sh` (Linux/macOS) o `start.ps1` (Windows) para iniciar.

Funciones avanzadas añadidas:

- Verificación de integridad (SHA) automática cuando la API proporciona el checksum.
 - Modo `staging`: añade `staging/` y genera `start-staging.sh` para pruebas. Habilítalo con `"staging": true` en la configuración o `python installer.py --staging`.
- Scripts de backup: `backup.sh` y `backup.ps1` guardan comprimidos en `backups/`.
- Dockerfile incluido para ejecutar el servidor en contenedor. Construcción:

```bash
docker build -t minecraft-server .
docker run -v $(pwd)/world:/opt/minecraft/world -p 25565:25565 minecraft-server
```

Ejemplo de archivo de configuración:

Para usar el sistema como único ejecutador, usa `installer.py` (ubicado en la raíz del proyecto).

Ejemplos:

```bash
# Validar todos los archivos y su sintaxis
python installer.py validate

# Ejecutar instalador integrado
python installer.py install -e paper -v latest --staging

# Iniciar servidor (usa el script en `bin/` si lo prefieres)
python installer.py start

# Crear backup (o ejecutar directamente `bin/backup.sh`)
python installer.py backup

# Ejecutar tests unitarios
python installer.py test
```

Tests unitarios:

Para ejecutar los tests (usa Python >=3.8):

```bash
python -m unittest discover -s tests
```

Validaciones añadidas:
- `installer.py` ahora valida versiones simples, comprueba disponibilidad de `java` y ofrece mensajes claros para Spigot/Forge/Fabric cuando la descarga automática no es factible.
