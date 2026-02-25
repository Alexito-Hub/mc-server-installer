#!/usr/bin/env bash
# ── Auralix Start Script ──
# Servidor: java-paper-1
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"

JAR="server.jar"
FLAGS="-Xms512M -Xmx2G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200"

if [ ! -f "$JAR" ]; then
    echo "[ERROR] No se encontró $JAR"
    exit 1
fi

echo "[Auralix] Iniciando java-paper-1..."
exec java $FLAGS -jar "$JAR" nogui
