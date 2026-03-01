# pitufialdea — Servidor Minecraft

Gestionado por **auralix.py** — instalador v3.0.

## Conexión

| Tipo    | IP              | Puerto    |
|---------|-----------------|-----------|
| Java    | 38.250.153.21   | 25565 TCP |
| Bedrock | 38.250.153.21   | 19132 UDP |

> `online-mode=false` — jugadores sin cuenta premium pueden conectarse.

## Comandos

```bash
sudo python3 auralix.py             # Asistente de instalación / reconfiguración
sudo python3 auralix.py start       # Iniciar todos los servidores
sudo python3 auralix.py stop        # Detener todos los servidores
sudo python3 auralix.py status      # Estado de los servicios
sudo python3 auralix.py backup      # Crear backup
sudo python3 auralix.py logs        # Ver logs en tiempo real
sudo python3 auralix.py validate    # Verificar instalación
sudo python3 auralix.py repair      # Reparar units systemd (permisos)
sudo python3 auralix.py delete      # Eliminar un servidor instalado
```

## Estructura

```
servers/
  <nombre>-<motor>-<n>/
    server.jar · start.sh · eula.txt · server.properties
    plugins/   · logs/
  <nombre>-bedrock-<version>-<n>/
    bedrock_server · start.sh
backups/        backups automáticos
systemd/        units de systemd locales
logs/           logs centralizados
config.json     configuración activa
```

## Motores soportados

| Motor   | Tipo    | Notas                          |
|---------|---------|--------------------------------|
| Paper   | Java    | Recomendado, alto rendimiento  |
| Purpur  | Java    | Fork de Paper con más opciones  |
| Vanilla | Java    | Oficial de Mojang              |
| Spigot  | Java    | Compatible con Bukkit          |
| Fabric  | Java    | Para mods                      |
| Bedrock | Bedrock | Compatible con móvil/consola   |

## Crossplay Java ↔ Bedrock

Instala **Geyser + Floodgate** desde el asistente para permitir
que jugadores Bedrock se conecten al servidor Java.
