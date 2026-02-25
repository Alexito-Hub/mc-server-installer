#!/usr/bin/env bash
if [ ! -f server.jar ]; then
  echo "No se encontró server.jar. Ejecuta 'python installer.py install' o usa el asistente primero."
  exit 1
fi
java -jar server.jar nogui
