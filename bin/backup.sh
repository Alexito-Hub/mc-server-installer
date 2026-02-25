#!/usr/bin/env bash
OUTDIR=backups
mkdir -p "$OUTDIR"
TS=$(date +%Y%m%d-%H%M%S)
tar -czf "$OUTDIR/backup-$TS.tar.gz" world world_nether world_the_end plugins server.properties eula.txt || { echo "Error creando backup"; exit 1; }
echo "Backup creado: $OUTDIR/backup-$TS.tar.gz"
