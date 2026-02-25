#!/usr/bin/env bash
# ── Screen Launcher ──

echo "Iniciando java-paper-1 en sesión screen: java-paper-1"
screen -dmS "java-paper-1" bash "../servers/java-paper-1/start.sh"
echo "  → screen -r java-paper-1  (para conectarte)"

echo "Sesiones activas:"
screen -ls
