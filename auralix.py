#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║                 A U R A L I X   v3.0                             ║
║         Minecraft Server Manager — Un solo ejecutador            ║
║    Configura, instala y deja corriendo el servidor en Linux      ║
║                    Creado por: Alexito-Hub                       ║
╚══════════════════════════════════════════════════════════════════╝

MODO DE USO:
    sudo python3 <script>          →  Asistente completo (recomendado)
    sudo python3 <script> start    →  Iniciar todos los servidores
    sudo python3 <script> stop     →  Detener todos los servidores
    sudo python3 <script> status   →  Ver estado de los servidores
    sudo python3 <script> backup   →  Crear backup
    sudo python3 <script> validate →  Verificar instalación
    sudo python3 <script> logs     →  Ver logs en tiempo real
"""
from __future__ import annotations

import argparse
try:
    import grp
except Exception:
    grp = None
import hashlib
import json
import os
try:
    import pwd
except Exception:
    pwd = None
import py_compile
import shutil
import socket
import subprocess
import sys
import textwrap
try:
    import termios
    import tty
except ImportError:
    termios = None
    tty = None
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import re

# ═══════════════════════════════════════════════════════════════════
#  COLORES Y UI
# ═══════════════════════════════════════════════════════════════════
class C:
    RESET   = "\033[0m";  BOLD    = "\033[1m";  DIM     = "\033[2m"
    GREEN   = "\033[92m"; YELLOW  = "\033[93m"; RED     = "\033[91m"
    CYAN    = "\033[96m"; BLUE    = "\033[94m"; MAGENTA = "\033[95m"
    WHITE   = "\033[97m"; BG_DARK = "\033[48;5;234m"

def _color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def ok(m):      print(f"  {C.GREEN}✔{C.RESET}  {m}" if _color() else f"  [OK]  {m}")
def warn(m):    print(f"  {C.YELLOW}⚠{C.RESET}  {m}" if _color() else f"  [!]   {m}")
def err(m):     print(f"  {C.RED}✘{C.RESET}  {m}" if _color() else f"  [ERR] {m}")
def info(m):    print(f"  {C.CYAN}→{C.RESET}  {m}" if _color() else f"  [..]  {m}")
def step(m):    print(f"\n{C.BOLD}{C.YELLOW}▸ {m}{C.RESET}" if _color() else f"\n-- {m} --")
def title(m):   print(f"\n{C.BOLD}{C.CYAN}{m}{C.RESET}\n" if _color() else f"\n=== {m} ===\n")
def sep():      print(f"  {C.DIM}{'─'*60}{C.RESET}" if _color() else "  " + "─"*60)

def banner():
    art = r"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     █████╗ ██╗   ██╗██████╗  █████╗ ██╗     ██╗██╗  ██╗  ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██║     ██║╚██╗██╔╝  ║
    ║    ███████║██║   ██║██████╔╝███████║██║     ██║ ╚███╔╝   ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══██║██║     ██║ ██╔██╗   ║
    ║    ██║  ██║╚██████╔╝██║  ██║██║  ██║███████╗██║██╔╝ ██╗  ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═╝  ║
    ║                                                          ║
    ║        Minecraft Server Setup Wizard  v3.0               ║
    ║    Configura · Instala · Corre · ¡A jugar!               ║
    ║                Creado por: Alexito-Hub                   ║
    ╚══════════════════════════════════════════════════════════╝
    """
    if _color():
        lines = art.split("\n")
        colors = [C.CYAN, C.BLUE, C.CYAN, C.MAGENTA, C.CYAN, C.BLUE, C.CYAN, C.MAGENTA, C.CYAN, C.BLUE, C.CYAN, C.CYAN]
        for i, line in enumerate(lines):
            print(f"{C.BOLD}{colors[i % len(colors)]}{line}{C.RESET}")
    else:
        print(art)

# ═══════════════════════════════════════════════════════════════════
#  RUTAS
# ═══════════════════════════════════════════════════════════════════
ROOT    = Path(__file__).resolve().parent
SERVERS = ROOT / "servers"
BACKUPS = ROOT / "backups"
LOGS    = ROOT / "logs"
DOCS    = ROOT / "docs"
SYSTEMD = ROOT / "systemd"
TESTS   = ROOT / "tests"
CONFIG  = ROOT / "config.json"
PROGRESS_FILE = ROOT / "progress.json"

def save_progress(state: dict) -> None:
    try:
        PROGRESS_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    except Exception as e:
        warn(f"No se pudo guardar el progreso: {e}")

def load_progress() -> dict | None:
    try:
        if PROGRESS_FILE.exists():
            return json.loads(PROGRESS_FILE.read_text())
    except Exception as e:
        warn(f"No se pudo leer el progreso: {e}")
    return None

def clear_progress() -> None:
    try:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            info("Progreso previo eliminado.")
    except Exception as e:
        warn(f"No se pudo eliminar el progreso: {e}")

def validate_state(state: dict) -> tuple[bool, list[str]]:
    """Validación mínima del estado guardado. Devuelve (ok, mensajes)."""
    msgs = []
    # server_name
    if state.get("server_name") is None or not str(state.get("server_name")).strip():
        msgs.append("Nombre de servidor vacío")
    # java_instances ports
    for i, inst in enumerate(state.get("java_instances", [])):
        port = inst.get("port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            msgs.append(f"Puerto inválido en java_instances[{i}]: {port}")
    for i, inst in enumerate(state.get("bedrock_instances", [])):
        port = inst.get("port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            msgs.append(f"Puerto inválido en bedrock_instances[{i}]: {port}")
    return (len(msgs) == 0, msgs)

# ═══════════════════════════════════════════════════════════════════
#  PLUGINS Y MODS CONOCIDOS
# ═══════════════════════════════════════════════════════════════════
PLUGINS = {
    "LuckPerms":    "https://github.com/LuckPerms/LuckPerms/releases/download/v5.4.102/LuckPerms-Bukkit-5.4.102.jar",
    "Vault":        "https://github.com/MilkBowl/Vault/releases/download/1.7.3/Vault.jar",
    "EssentialsX":  "https://github.com/EssentialsX/Essentials/releases/download/2.21.0/EssentialsX-2.21.0.jar",
    "EssentialsX-Chat": "https://github.com/EssentialsX/Essentials/releases/download/2.21.0/EssentialsXChat-2.21.0.jar",
    "WorldEdit":    "https://dev.bukkit.org/projects/worldedit/files/latest",
    "WorldGuard":   "https://dev.bukkit.org/projects/worldguard/files/latest",
    "ProtocolLib":  "https://github.com/dmulloy2/ProtocolLib/releases/download/5.3.0/ProtocolLib.jar",
    "ViaVersion":   "https://github.com/ViaVersion/ViaVersion/releases/download/5.0.3/ViaVersion-5.0.3.jar",
    "ViaBackwards": "https://github.com/ViaVersion/ViaBackwards/releases/download/5.0.2/ViaBackwards-5.0.2.jar",
    # Geyser + Floodgate: juego cruzado Java <-> Bedrock
    "Geyser-Spigot": "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot",
    "Floodgate":     "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot",
}

MODS = {
    "FabricAPI":   "https://github.com/FabricMC/fabric-api/releases/download/0.102.1+1.21.1/fabric-api-0.102.1+1.21.1.jar",
    "Lithium":     "https://api.modrinth.com/maven/maven/modrinth/lithium/mc1.21.1-0.13.0/lithium-mc1.21.1-0.13.0.jar",
    "FerriteCore": "https://github.com/malte0811/FerriteCore/releases/download/7.0.0/ferritecore-7.0.0-fabric.jar",
}

# ═══════════════════════════════════════════════════════════════════
#  UTILIDADES DE RED
# ═══════════════════════════════════════════════════════════════════
def get_json(url: str, timeout: int = 20) -> dict:
    req = Request(url, headers={"User-Agent": "Installer/3.0"})
    with urlopen(req, timeout=timeout) as r:
        return json.load(r)

def download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "Installer/3.0"})
    try:
        with urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            done  = 0
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total and _color():
                        pct = int(done * 38 / total)
                        bar = "█" * pct + "░" * (38 - pct)
                        mb  = done / 1048576
                        tot = total / 1048576
                        print(f"\r     [{C.CYAN}{bar}{C.RESET}] {mb:.1f}/{tot:.1f} MB ", end="", flush=True)
        if total and _color():
            print()
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"Error de descarga ({url}): {e}")


def resolve_github_latest_asset(original_url: str, name_prefix: str | None = None) -> str | None:
    try:
        p = urlparse(original_url)
        parts = p.path.split("/")
        if len(parts) < 5:
            return None
        owner = parts[1]
        repo  = parts[2]
        if not name_prefix:
            name_prefix = parts[-1].split("-")[0] if parts[-1] else repo
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        for rel in get_json(api_url):
            for a in rel.get("assets", []):
                aname = a.get("name", "")
                if aname.lower().startswith(name_prefix.lower()) and aname.lower().endswith(".jar"):
                    return a.get("browser_download_url")
        for a in get_json(f"https://api.github.com/repos/{owner}/{repo}/releases/latest").get("assets", []):
            aname = a.get("name", "")
            if aname.lower().startswith(name_prefix.lower()) and aname.lower().endswith(".jar"):
                return a.get("browser_download_url")
    except Exception:
        return None
    return None

def hash_file(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def get_public_ip() -> str:
    """Obtiene la IP pública del servidor."""
    for url in ("https://api4.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"):
        try:
            req = Request(url, headers={"User-Agent": "Installer/3.0"})
            with urlopen(req, timeout=5) as r:
                return r.read().decode().strip()
        except Exception:
            continue
    return "No detectada"

def get_local_ip() -> str:
    """Obtiene la IP local del servidor."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def resolve_domain(domain: str) -> str:
    """Resuelve un dominio a IP."""
    try:
        return socket.gethostbyname(domain)
    except Exception:
        return "No resuelto"

def check_port_available(port: int) -> bool:
    """Verifica si un puerto está libre."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0

# ═══════════════════════════════════════════════════════════════════
#  SISTEMA LINUX — USUARIOS, PERMISOS, FIREWALL
# ═══════════════════════════════════════════════════════════════════
def is_root() -> bool:
    try:
        if hasattr(os, "geteuid"):
            return os.geteuid() == 0
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return False

def user_exists(username: str) -> bool:
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def group_exists(groupname: str) -> bool:
    try:
        grp.getgrnam(groupname)
        return True
    except KeyError:
        return False

def create_system_user(username: str) -> bool:
    """Crea usuario del sistema dedicado para el servidor Minecraft."""
    if user_exists(username):
        info(f"Usuario '{username}' ya existe.")
        return True
    try:
        subprocess.check_call([
            "useradd", "--system", "--no-create-home",
            "--shell", "/usr/sbin/nologin",
            "--comment", "Minecraft Server",
            username
        ], stderr=subprocess.DEVNULL)
        ok(f"Usuario del sistema '{username}' creado.")
        return True
    except subprocess.CalledProcessError as e:
        err(f"No se pudo crear el usuario '{username}': {e}")
        return False

def set_directory_permissions(path: Path, username: str) -> None:
    """Asigna propietario y permisos correctos al directorio del servidor."""
    try:
        uid = pwd.getpwnam(username).pw_uid
        gid = pwd.getpwnam(username).pw_gid
        for root_dir, dirs, files in os.walk(path):
            os.chown(root_dir, uid, gid)
            for f in files:
                os.chown(os.path.join(root_dir, f), uid, gid)
        ok(f"Permisos asignados: {path} → {username}")
    except Exception as e:
        warn(f"No se pudieron asignar permisos a {path}: {e}")

def ensure_parents_traversable(server_dir: Path) -> None:
    """Añade o+x en cada directorio padre para que el usuario del servicio
    pueda traversar la ruta aunque el directorio raíz sea 700."""
    current = server_dir.resolve()
    fs_root = Path("/")
    while current != fs_root:
        current = current.parent
        try:
            mode = current.stat().st_mode
            if not (mode & 0o001):
                current.chmod(mode | 0o001)
                ok(f"chmod o+x {current}")
        except Exception as e:
            warn(f"No se pudo ajustar permisos en {current}: {e}")

def open_firewall_port(port: int, protocol: str = "tcp") -> None:
    if shutil.which("ufw"):
        try:
            subprocess.check_call(["ufw", "allow", f"{port}/{protocol}"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok(f"Puerto {port}/{protocol} abierto en UFW.")
            return
        except Exception:
            pass
    if shutil.which("firewall-cmd"):
        try:
            subprocess.check_call(["firewall-cmd", "--permanent", f"--add-port={port}/{protocol}"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.check_call(["firewall-cmd", "--reload"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok(f"Puerto {port}/{protocol} abierto en firewalld.")
            return
        except Exception:
            pass
    if shutil.which("iptables"):
        try:
            subprocess.check_call(["iptables", "-I", "INPUT", "-p", protocol,
                                   "--dport", str(port), "-j", "ACCEPT"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok(f"Puerto {port}/{protocol} abierto en iptables.")
            return
        except Exception:
            pass
    warn(f"No se pudo abrir el puerto {port} automáticamente. Ábrelo manualmente.")

def detect_java() -> tuple[str, str]:
    """Retorna (versión, ruta) de Java o ('', '')."""
    try:
        r = subprocess.run(["java", "-version"], capture_output=True, text=True)
        for line in (r.stdout + r.stderr).splitlines():
            if "version" in line.lower():
                path = shutil.which("java") or ""
                return line.strip(), path
    except Exception:
        pass
    return "", ""

def install_java_if_missing() -> bool:
    """Intenta instalar Java 21 usando el gestor de paquetes disponible."""
    ver, _ = detect_java()
    if ver:
        return True
    info("Intentando instalar Java 21 automáticamente...")
    pkg_managers = [
        (["apt-get", "install", "-y", "openjdk-21-jre-headless"], "apt-get"),
        (["apt",     "install", "-y", "openjdk-21-jre-headless"], "apt"),
        (["dnf",     "install", "-y", "java-21-openjdk-headless"], "dnf"),
        (["yum",     "install", "-y", "java-21-openjdk-headless"], "yum"),
        (["pacman",  "-S", "--noconfirm", "jre21-openjdk-headless"], "pacman"),
        (["zypper",  "install", "-y", "java-21-openjdk-headless"], "zypper"),
    ]
    for cmd, name in pkg_managers:
        if shutil.which(cmd[0]):
            try:
                info(f"Usando {name}...")
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok("Java 21 instalado correctamente.")
                return True
            except subprocess.CalledProcessError:
                continue
    err("No se pudo instalar Java automáticamente. Instálalo manualmente:")
    info("  Ubuntu/Debian: sudo apt install openjdk-21-jre-headless")
    info("  Fedora/RHEL:   sudo dnf install java-21-openjdk-headless")
    info("  Arch:          sudo pacman -S jre21-openjdk-headless")
    return False

# ═══════════════════════════════════════════════════════════════════
#  FETCH ENGINES
# ═══════════════════════════════════════════════════════════════════
def fetch_papermc(version: str, build: str | None, dest: Path) -> dict:
    base = "https://api.papermc.io/v2/projects/paper"
    if not version:
        err("No se ha especificado una versión para Paper.")
        raise SystemExit("Instalación de Paper abortada.")
    proj = get_json(base)
    if version == "latest":
        version = proj["versions"][-1]
    if version not in proj["versions"]:
        raise SystemExit(f"Paper: versión '{version}' no encontrada.")
    
    version_builds = get_json(f"{base}/versions/{version}")
    builds = version_builds["builds"]
    selected = int(build) if build and build.isdigit() else builds[-1]
    
    binfo    = get_json(f"{base}/versions/{version}/builds/{selected}")
    app      = binfo["downloads"]["application"]
    url      = f"{base}/versions/{version}/builds/{selected}/downloads/{app['name']}"
    jar      = dest / "server.jar"
    info(f"Descargando Paper {version} (build {selected})...")
    download(url, jar)
    return {"jar": jar, "version": f"{version}-{selected}",
            "hash": app.get("sha256"), "algo": "sha256"}

def fetch_purpur(version: str, build: str | None, dest: Path) -> dict:
    base = "https://api.purpurmc.org/v2/purpur"
    proj = get_json(base)
    if version == "latest":
        version = proj["versions"][-1]
    if version not in proj["versions"]:
        raise SystemExit(f"Purpur: versión '{version}' no encontrada.")
    builds   = get_json(f"{base}/{version}")["builds"]
    selected = build or builds["latest"]
    url      = f"{base}/{version}/{selected}/download"
    jar      = dest / "server.jar"
    info(f"Descargando Purpur {version} (build {selected})...")
    download(url, jar)
    return {"jar": jar, "version": f"{version}-{selected}",
            "hash": None, "algo": None}

def fetch_vanilla(version: str, dest: Path) -> dict:
    manifest = get_json("https://launchermeta.mojang.com/mc/game/version_manifest.json")
    if version == "latest":
        version = manifest["latest"]["release"]
    entry = next((v for v in manifest["versions"] if v["id"] == version), None)
    if not entry:
        raise SystemExit(f"Vanilla: versión '{version}' no encontrada.")
    meta   = get_json(entry["url"])
    server = meta["downloads"]["server"]
    jar    = dest / "server.jar"
    info(f"Descargando Vanilla {version}...")
    download(server["url"], jar)
    return {"jar": jar, "version": version,
            "hash": server.get("sha1"), "algo": "sha1"}

def fetch_spigot(version: str, dest: Path) -> dict:
    url = "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar"
    jar = dest / "BuildTools.jar"
    info("Descargando BuildTools (Spigot)...")
    download(url, jar)
    return {"jar": jar, "version": version, "hash": None, "algo": None,
            "note": f"Para compilar: java -jar BuildTools.jar --rev {version}"}

def fetch_fabric(version: str, dest: Path) -> dict:
    url = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/0.11.0/fabric-installer-0.11.0.jar"
    jar = dest / "fabric-installer.jar"
    info("Descargando Fabric Installer...")
    download(url, jar)
    return {"jar": jar, "version": version, "hash": None, "algo": None,
            "note": "Para instalar: java -jar fabric-installer.jar server"}

def _get_bedrock_versions_data() -> dict:
    """Obtiene el JSON de versiones de Bedrock desde BDS-Versions (Bedrock-OSS)."""
    api_url = "https://raw.githubusercontent.com/Bedrock-OSS/BDS-Versions/main/versions.json"
    return get_json(api_url)

def fetch_bedrock(version: str, dest: Path) -> dict:
    try:
        info("Consultando versiones de Bedrock...")
        data      = _get_bedrock_versions_data()
        cdn       = data["cdn_root"]
        linux_info= data["linux"]
        stable    = linux_info["stable"]
        if version in ("latest", ""):
            version = stable
        if version not in linux_info.get("versions", [stable]):
            warn(f"Versión Bedrock '{version}' no encontrada, usando {stable}.")
            version = stable
        url      = f"{cdn}/bin-linux/bedrock-server-{version}.zip"
        dest_zip = dest / f"bedrock-server-{version}.zip"
        info(f"Descargando Bedrock Server {version}...")
        download(url, dest_zip)
        if shutil.which("unzip"):
            subprocess.run(["unzip", "-o", str(dest_zip), "-d", str(dest)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok(f"Bedrock {version} descomprimido en {dest}")
        else:
            warn("'unzip' no encontrado. Descomprime manualmente el zip.")
        return {"jar": dest_zip, "version": version, "hash": None, "algo": None,
                "bedrock_exec": dest / "bedrock_server"}
    except Exception as e:
        warn(f"Error descargando Bedrock: {e}")
    return {"jar": None, "version": "latest", "hash": None, "algo": None,
            "note": (f"Descarga manual requerida:\n"
                     f"  https://www.minecraft.net/en-us/download/server/bedrock\n"
                     f"  Coloca el zip en: {dest}")}

def get_available_versions(engine: str) -> list[str]:
    try:
        if engine == "paper":
            return list(reversed(get_json("https://api.papermc.io/v2/projects/paper")["versions"]))[:12]
        if engine == "purpur":
            return list(reversed(get_json("https://api.purpurmc.org/v2/purpur")["versions"]))[:12]
        if engine in ("vanilla", "spigot"):
            data = get_json("https://launchermeta.mojang.com/mc/game/version_manifest.json")
            return [v["id"] for v in data["versions"] if v["type"] == "release"][:12]
        if engine == "fabric":
            data = get_json("https://meta.fabricmc.net/v2/versions/game")
            return [v["version"] for v in data if v.get("stable")][:12]
        if engine == "bedrock":
            bdata    = _get_bedrock_versions_data()
            stable   = bdata["linux"]["stable"]
            versions = [v for v in reversed(bdata["linux"]["versions"]) if v != stable][:9]
            return [f"latest ({stable})"] + versions
    except Exception:
        pass
    return ["latest"]

def verify_jar(result: dict) -> bool:
    if not result.get("hash") or not result.get("algo") or not result.get("jar"):
        warn("Sin checksum disponible, saltando verificación.")
        return True
    actual = hash_file(result["jar"], result["algo"])
    if actual.lower() == result["hash"].lower():
        ok(f"Hash {result['algo'].upper()} verificado ✔")
        return True
    err(f"¡Hash incorrecto! esperado={result['hash'][:16]}... obtenido={actual[:16]}...")
    return False

# ═══════════════════════════════════════════════════════════════════
#  GENERACIÓN DE ARCHIVOS
# ═══════════════════════════════════════════════════════════════════
def write_eula(dest: Path) -> None:
    dest.write_text("eula=true\n# EULA aceptado por el instalador\n", encoding="utf-8")

def write_server_properties(dest: Path, cfg: dict) -> None:
    bind_ip = cfg.get("bind_ip", "")   # "" = bind en todas las interfaces
    lines = [
        "# ── Server Properties ──",
        f"server-name={cfg.get('name', 'Servidor')}",
        f"motd={cfg.get('motd', '§bServidor §7| §aMinecraft')}",
        f"server-ip={bind_ip}",
        f"server-port={cfg.get('port', 25565)}",
        f"online-mode={str(cfg.get('online_mode', True)).lower()}",
        f"max-players={cfg.get('max_players', 40)}",
        f"level-name={cfg.get('level_name', 'world')}",
        f"level-seed={cfg.get('seed', '')}",
        f"difficulty={cfg.get('difficulty', 'normal')}",
        f"gamemode={cfg.get('gamemode', 'survival')}",
        f"pvp={str(cfg.get('pvp', True)).lower()}",
        f"enable-command-block={str(cfg.get('command_blocks', False)).lower()}",
        f"view-distance={cfg.get('view_distance', 10)}",
        f"simulation-distance={cfg.get('simulation_distance', 10)}",
        f"white-list={str(cfg.get('whitelist', False)).lower()}",
        f"enforce-whitelist={str(cfg.get('enforce_whitelist', False)).lower()}",
        f"spawn-protection={cfg.get('spawn_protection', 16)}",
        f"max-world-size={cfg.get('max_world_size', 29999984)}",
        f"allow-nether={str(cfg.get('allow_nether', True)).lower()}",
        f"allow-flight={str(cfg.get('allow_flight', False)).lower()}",
        "enable-rcon=false",
        "enable-query=false",
        "prevent-proxy-connections=false",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")

def write_start_script(dest_dir: Path, jar: str, jvm_flags: str,
                       server_name: str = "server") -> None:
    sh = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        # ── Start Script ──
        # Servidor: {server_name}
        set -euo pipefail
        cd "$(dirname "$(realpath "$0")")"

        JAR="{jar}"
        FLAGS="{jvm_flags}"

        if [ ! -f "$JAR" ]; then
            echo "[ERROR] No se encontró $JAR"
            exit 1
        fi

        echo "Iniciando {server_name}..."
        exec java $FLAGS -jar "$JAR" nogui
    """)
    script = dest_dir / "start.sh"
    script.write_text(sh, encoding="utf-8")
    script.chmod(0o755)

def write_bedrock_start(dest_dir: Path) -> None:
    sh = textwrap.dedent("""\
        #!/usr/bin/env bash
        # ── Bedrock Start ──
        set -euo pipefail
        cd "$(dirname "$(realpath "$0")")"
        if [ -f "bedrock_server" ]; then
            chmod +x bedrock_server
            LD_LIBRARY_PATH=. ./bedrock_server
        else
            echo "[ERROR] No se encontró bedrock_server. Descomprime el zip primero."
            exit 1
        fi
    """)
    script = dest_dir / "start.sh"
    script.write_text(sh, encoding="utf-8")
    script.chmod(0o755)

def write_systemd_unit(unit_path: Path, server_dir: Path,
                        start_sh: Path, username: str,
                        description: str = "Minecraft Server",
                        opts: dict | None = None) -> None:
    """Genera la unit de systemd con soporte completo de opciones Linux.
    
    opts puede contener:
      restart, restart_sec, timeout_stop, start_limit_burst,
      start_limit_interval, kill_signal, memory_max, cpu_quota,
      tasks_max, nice, io_class, io_prio, oom_score, hardening,
      env_vars (dict str->str), success_exit
    """
    o = opts or {}

    # ── Restart ──────────────────────────────────────────────────────────────────
    restart          = o.get("restart",           "on-failure")
    restart_sec      = o.get("restart_sec",        15)
    timeout_stop     = o.get("timeout_stop",       60)
    start_limit_b    = o.get("start_limit_burst",  5)
    start_limit_i    = o.get("start_limit_interval", 120)
    kill_signal      = o.get("kill_signal",        "SIGTERM")

    # ── Recursos ──────────────────────────────────────────────────────────────────
    memory_max  = o.get("memory_max",  "")    # ej: "4G", "" = sin límite
    cpu_quota   = o.get("cpu_quota",   "")    # ej: "200%" (2 núcleos)
    tasks_max   = o.get("tasks_max",   "")    # ej: "512"
    nice        = o.get("nice",        0)     # -20 (alta) a 19 (baja)
    io_class    = o.get("io_class",    "")    # best-effort / realtime / idle
    io_prio     = o.get("io_prio",     "")    # 0-7
    oom_score   = o.get("oom_score",   "")    # -1000-1000

    # ── Hardening ─────────────────────────────────────────────────────────────────
    hardening = o.get("hardening", "basic")  # none / basic / strict

    under_home   = str(server_dir.resolve()).startswith("/home")
    protect_home = "no" if under_home else "read-only"

    if hardening == "none":
        hardening_block = "# Hardening desactivado\n"
    elif hardening == "strict":
        hardening_block = textwrap.dedent(f"""\
            # Hardening estricto
            NoNewPrivileges=true
            PrivateTmp=true
            PrivateDevices=true
            ProtectSystem=strict
            ProtectHome={protect_home}
            ReadWritePaths={server_dir}
            ProtectKernelTunables=true
            ProtectKernelModules=true
            ProtectKernelLogs=true
            ProtectControlGroups=true
            ProtectClock=true
            ProtectHostname=true
            RestrictNamespaces=true
            RestrictRealtime=true
            RestrictSUIDSGID=true
            LockPersonality=true
            MemoryDenyWriteExecute=false
            SystemCallFilter=@system-service
            SystemCallErrorNumber=EPERM
            CapabilityBoundingSet=
        """)
    else:  # basic
        hardening_block = textwrap.dedent(f"""\
            # Hardening básico
            NoNewPrivileges=true
            PrivateTmp=true
            ProtectSystem=full
            ProtectHome={protect_home}
            ReadWritePaths={server_dir}
        """)

    # ── Variables de entorno ──────────────────────────────────────────────────────────
    env_vars: dict = o.get("env_vars", {})
    env_block = ""
    if env_vars:
        env_block = "\n".join(f'Environment="{k}={v}"' for k, v in env_vars.items()) + "\n"

    # ── Recursos opcionales (solo si tienen valor) ──────────────────────────────
    res_lines = []
    if memory_max:  res_lines.append(f"MemoryMax={memory_max}")
    if cpu_quota:   res_lines.append(f"CPUQuota={cpu_quota}")
    if tasks_max:   res_lines.append(f"TasksMax={tasks_max}")
    if nice != 0:   res_lines.append(f"Nice={nice}")
    if io_class:    res_lines.append(f"IOSchedulingClass={io_class}")
    if io_prio:     res_lines.append(f"IOSchedulingPriority={io_prio}")
    if oom_score:   res_lines.append(f"OOMScoreAdjust={oom_score}")
    res_block = ("# Límites de recursos\n" + "\n".join(res_lines) + "\n") if res_lines else ""

    success_exit = o.get("success_exit", "")
    success_line = f"SuccessExitStatus={success_exit}\n" if success_exit else ""

    # Asegurar que start.sh sea ejecutable antes de escribir la unit
    try:
        start_sh.chmod(0o755)
    except Exception:
        pass

    content = textwrap.dedent(f"""\
        # ── Generado por el instalador v3.0 ──
        [Unit]
        Description={description}
        After=network-online.target
        Wants=network-online.target
        StartLimitIntervalSec={start_limit_i}
        StartLimitBurst={start_limit_b}

        [Service]
        Type=simple
        User={username}
        Group={username}
        WorkingDirectory={server_dir}
        ExecStart=/bin/bash {start_sh}
        ExecReload=/bin/kill -HUP $MAINPID
        Restart={restart}
        RestartSec={restart_sec}s
        KillMode=mixed
        KillSignal={kill_signal}
        TimeoutStopSec={timeout_stop}
        {success_line}\
        {env_block}\
        {res_block}\
        {hardening_block}\
        # Logs
        StandardOutput=journal
        StandardError=journal
        SyslogIdentifier={unit_path.stem}

        [Install]
        WantedBy=multi-user.target
    """)
    # Limpiar líneas vacías duplicadas que puedan generarse
    import io
    lines = content.splitlines()
    clean: list[str] = []
    prev_blank = False
    for ln in lines:
        is_blank = ln.strip() == ""
        if is_blank and prev_blank:
            continue
        clean.append(ln)
        prev_blank = is_blank
    content = "\n".join(clean) + "\n"

    unit_path.parent.mkdir(parents=True, exist_ok=True)
    unit_path.write_text(content, encoding="utf-8")


def configure_systemd_options() -> dict:
    """Asistente interactivo para opciones avanzadas de systemd/Linux."""
    step("Opciones avanzadas de systemd")
    opts: dict = {}

    sep()
    info("RESTART")
    opts["restart"]              = ask_choice("Política de reinicio", ["on-failure", "always", "on-abnormal", "on-watchdog", "no"], "on-failure")
    opts["restart_sec"]          = ask_int("Segundos entre reinicios", 15, 1, 300)
    opts["start_limit_burst"]    = ask_int("Máx. reinicios en la ventana", 5, 1, 20)
    opts["start_limit_interval"] = ask_int("Ventana de tiempo (segundos)", 120, 10, 3600)
    opts["timeout_stop"]         = ask_int("Tiempo para parada ordenada (segundos)", 60, 5, 600)
    opts["kill_signal"]          = ask_choice("Señal de parada", ["SIGTERM", "SIGINT", "SIGHUP", "SIGKILL"], "SIGTERM")

    sep()
    info("RECURSOS")
    if ask_yn("¿Limitar RAM máxima del servicio?", False):
        opts["memory_max"] = ask("Límite de RAM (ej: 4G, 2048M)", "4G")
    if ask_yn("¿Limitar el uso de CPU?", False):
        opts["cpu_quota"] = ask("Cuota de CPU (ej: 200% = 2 núcleos)", "200%")
    if ask_yn("¿Limitar el número máximo de hilos/procesos?", False):
        opts["tasks_max"] = ask("Máximo de tareas", "512")
    opts["nice"] = ask_int("Prioridad nice (-20=alta, 0=normal, 19=baja)", 0, -20, 19)
    if ask_yn("¿Configurar prioridad de I/O?", False):
        opts["io_class"] = ask_choice("Clase de I/O", ["best-effort", "realtime", "idle"], "best-effort")
        opts["io_prio"]  = str(ask_int("Prioridad I/O (0=alta, 7=baja)", 4, 0, 7))
    if ask_yn("¿Ajustar puntuación OOM?", False):
        opts["oom_score"] = str(ask_int("OOM score (-1000=nunca matar, 1000=matar primero)", 0, -1000, 1000))

    sep()
    info("SEGURIDAD  —  none: sin restricciones  |  basic: PrivateTmp+ProtectSystem  |  strict: sandbox completo")
    opts["hardening"] = ask_choice("Nivel de hardening", ["none", "basic", "strict"], "basic")

    sep()
    info("ENTORNO")
    env_vars: dict = {}
    if ask_yn("¿Añadir variables de entorno al servicio?", False):
        info("Introduce pares CLAVE=VALOR, línea vacía para terminar.")
        while True:
            try:
                pair = input("    VAR=valor: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not pair:
                break
            if "=" in pair:
                k, v = pair.split("=", 1)
                env_vars[k.strip()] = v.strip()
            else:
                warn(f"Formato inválido '{pair}', usa CLAVE=valor")
    opts["env_vars"] = env_vars

    sep()
    info("OTROS")
    if ask_yn("¿Definir códigos de salida exitosos (SuccessExitStatus)?", False):
        opts["success_exit"] = ask("Códigos (ej: 0 143)", "0 143")

    return opts

def repair_systemd_units() -> int:
    """Regenera las units systemd generadas por este instalador corrigiendo
    problemas de permisos (ProtectHome, ReadWritePaths, chmod start.sh)."""
    if not is_root():
        err("Necesitas ejecutar como root: sudo python3 auralix.py repair")
        return 1

    sys_dir = Path("/etc/systemd/system")
    marker  = "# ── Generado por el instalador v3.0 ──"
    repaired = 0

    # Buscar en el directorio local de units y en /etc/systemd/system
    candidates: list[Path] = []
    for d in (SYSTEMD, sys_dir):
        if d.exists():
            candidates += [f for f in d.glob("*.service") if marker in f.read_text(encoding="utf-8", errors="ignore")]

    # Deduplicar por nombre
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        if c.name not in seen:
            seen.add(c.name)
            unique.append(c)

    if not unique:
        warn("No se encontraron units generadas por este instalador.")
        return 0

    step(f"Reparando {len(unique)} unit(s) systemd...")

    for unit_file in unique:
        content = unit_file.read_text(encoding="utf-8", errors="ignore")

        # Extraer campos necesarios
        exec_match = re.search(r'^ExecStart=/bin/bash (.+)$', content, re.MULTILINE)
        user_match  = re.search(r'^User=(.+)$', content, re.MULTILINE)
        desc_match  = re.search(r'^Description=(.+)$', content, re.MULTILINE)

        if not exec_match or not user_match:
            warn(f"No se pudo parsear {unit_file.name}, omitiendo.")
            continue

        start_sh   = Path(exec_match.group(1).strip())
        server_dir = start_sh.parent
        username   = user_match.group(1).strip()
        description = desc_match.group(1).strip() if desc_match else unit_file.stem

        # Asegurar permisos de ejecución en start.sh
        if start_sh.exists():
            start_sh.chmod(0o755)
            ok(f"chmod +x {start_sh}")
        else:
            warn(f"start.sh no encontrado: {start_sh}")

        # Asegurar que los directorios padre sean traversables
        ensure_parents_traversable(server_dir)

        # Ruta local del systemd dir de este proyecto
        local_unit = SYSTEMD / unit_file.name

        # Reescribir la unit con los parámetros corregidos
        write_systemd_unit(local_unit, server_dir, start_sh, username, description)

        # Copiar a /etc/systemd/system/
        target = sys_dir / unit_file.name
        try:
            shutil.copy2(str(local_unit), str(target))
            ok(f"Unit actualizada: {target}")
            repaired += 1
        except Exception as e:
            warn(f"No se pudo copiar {unit_file.name}: {e}")

    # Recargar systemd
    try:
        subprocess.check_call(["systemctl", "daemon-reload"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ok("systemctl daemon-reload ejecutado.")
    except Exception as e:
        warn(f"daemon-reload falló: {e}")

    if repaired:
        ok(f"{repaired} unit(s) reparada(s).")
        info("Reinicia los servicios con:  sudo systemctl restart <nombre>.service")
        # Preguntar si reiniciar ahora
        try:
            resp = input("  ¿Reiniciar los servicios ahora? [S/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            resp = "n"
        if resp in ("", "s", "si", "sí", "y", "yes"):
            for unit_file in unique:
                try:
                    subprocess.check_call(["systemctl", "restart", unit_file.stem],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    ok(f"Reiniciado: {unit_file.stem}")
                except Exception as e:
                    warn(f"No se pudo reiniciar {unit_file.stem}: {e}")
    return 0


def write_screen_launcher(dest: Path, servers: list[tuple[str, Path]]) -> None:
    lines = ["#!/usr/bin/env bash", "# ── Screen Launcher ──", ""]
    for name, sh in servers:
        safe = name.replace(" ", "_").lower()
        lines.append(f'echo "Iniciando {name} en sesión screen: {safe}"')
        lines.append(f'screen -dmS "{safe}" bash "{sh}"')
        lines.append(f'echo "  → screen -r {safe}  (para conectarte)"')
        lines.append("")
    lines.append('echo "Sesiones activas:"')
    lines.append("screen -ls")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dest.chmod(0o755)

def write_tmux_launcher(dest: Path, servers: list[tuple[str, Path]]) -> None:
    lines = ["#!/usr/bin/env bash", "# ── tmux Launcher ──", ""]
    for name, sh in servers:
        safe = name.replace(" ", "_").lower()
        lines.append(f'echo "Iniciando {name} en sesión tmux: {safe}"')
        lines.append(f'tmux new-session -d -s "{safe}" "bash {sh}"')
        lines.append(f'echo "  → tmux attach -t {safe}  (para conectarte)"')
        lines.append("")
    lines.append('echo "Sesiones activas:"')
    lines.append("tmux ls 2>/dev/null || echo '  (ninguna)'")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dest.chmod(0o755)

def write_docker_compose(dest: Path, services: list[dict]) -> None:
    svc_block = []
    for s in services:
        name = s["name"].replace(" ", "_").lower()
        port = s["port"]
        path = s["path"]
        proto = s.get("proto", "tcp")
        svc_block.append(textwrap.dedent(f"""\
          {name}:
            build: {path}
            container_name: mc_{name}
            ports:
              - "{port}:{port}/{proto}"
            volumes:
              - {path}/world:/srv/mc/world
              - {path}/plugins:/srv/mc/plugins
              - {path}/logs:/srv/mc/logs
            restart: unless-stopped
            stdin_open: true
            tty: true
        """))
    content = "version: \"3.9\"\nservices:\n" + "".join(
        textwrap.indent(s, "  ") for s in svc_block
    )
    dest.write_text(content, encoding="utf-8")

def write_dockerfile(dest: Path, jar: str, jvm_flags: str) -> None:
    flags_list = ", ".join(f'"{f}"' for f in jvm_flags.split())
    dest.write_text(textwrap.dedent(f"""
        FROM eclipse-temurin:21-jre-alpine
        WORKDIR /srv/mc
        COPY {jar} .
        COPY eula.txt .
        COPY server.properties .
        RUN addgroup -S minecraft && adduser -S -G minecraft minecraft \\
            && chown -R minecraft:minecraft /srv/mc
        USER minecraft
        EXPOSE 25565
        CMD ["java", {flags_list}, "-jar", "{jar}", "nogui"]
    """), encoding="utf-8")

def write_backup_script(dest: Path, server_dirs: list[Path]) -> None:
    paths_str = " \\\n  ".join(f'"{p}"' for p in server_dirs)
    sh = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        # ── Backup Script ──
        set -euo pipefail
        TS=$(date +%Y%m%d_%H%M%S)
        DEST="{BACKUPS}"
        mkdir -p "$DEST"

        echo "Iniciando backup $TS..."
        tar -czf "$DEST/backup_$TS.tar.gz" \\
          {paths_str}

        SIZE=$(du -sh "$DEST/backup_$TS.tar.gz" | cut -f1)
        echo "[OK] Backup creado: $DEST/backup_$TS.tar.gz ($SIZE)"

        # Borrar backups con más de 7 días
        find "$DEST" -name "backup_*.tar.gz" -mtime +7 -delete
        echo "[OK] Backups antiguos (>7 días) eliminados."
    """)
    dest.write_text(sh, encoding="utf-8")
    dest.chmod(0o755)

def write_gitignore(dest: Path) -> None:
    dest.write_text(textwrap.dedent("""\
        # .gitignore
        server.jar
        eula.txt
        world/
        world_nether/
        world_the_end/
        logs/
        cache/
        plugins/*.jar
        mods/*.jar
        backups/
        staging/
        *.zip
        *.tar.gz
        BuildTools.jar
        fabric-installer.jar
        bedrock_server
        bedrock-server-*.zip
        __pycache__/
        *.pyc
        .env
        .vscode/
        .idea/
    """), encoding="utf-8")

def write_readme(dest: Path, cfg: dict) -> None:
    name     = cfg.get("server_name", "Servidor")
    public   = cfg.get("public_ip", "?")
    domain   = cfg.get("domain", "")
    ip_str   = domain if domain else public
    dest.write_text(textwrap.dedent(f"""\
        # {name} — Servidor Minecraft

        Configurado y gestionado por el instalador v3.0.

        ## Conexión al servidor

        - **IP del servidor:** `{ip_str}`
        - **Puerto Java:** `{cfg.get('java_port', 25565)}`
        - **Puerto Bedrock:** `{cfg.get('bedrock_port', 19132)}` (UDP)

        ## Comandos

        ```bash
        sudo python3 <script>          # Asistente / reconfigurar
        sudo python3 <script> start    # Iniciar servidores
        sudo python3 <script> stop     # Detener servidores
        sudo python3 <script> status   # Estado
        sudo python3 <script> backup   # Backup
        sudo python3 <script> logs     # Ver logs
        sudo python3 <script> validate # Validar instalación
        ```

        ## Estructura

        ```
        servers/
          java/<motor>-<version>/
            server.jar · start.sh · eula.txt · server.properties
            plugins/   · logs/
          bedrock/<version>/
            bedrock_server · start.sh
        backups/         (backups automáticos)
        systemd/         (units de systemd)
        logs/            (logs centralizados)
        ```

        ## Modo sin cuenta premium (offline)

        Los jugadores sin cuenta premium pueden conectarse porque
        `online-mode=false` está configurado en server.properties.
    """), encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════
#  PREGUNTAS HELPER
# ═══════════════════════════════════════════════════════════════════
def ask(prompt_text: str, default: str = "") -> str:
    if _color():
        d   = f" [{C.YELLOW}{default}{C.RESET}]" if default else ""
        txt = f"  {C.CYAN}{prompt_text}{C.RESET}{d}: "
    else:
        d   = f" [{default}]" if default else ""
        txt = f"  {prompt_text}{d}: "
    try:
        val = input(txt).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit("\nAsistente cancelado.")

def check_dependencies() -> None:
    """Verifica e instala dependencias del sistema requeridas."""
    # Verificar sistema operativo
    if os.name != 'posix':
        err("Este script solo funciona en sistemas Linux/Unix.")
        sys.exit(1)
    
    required = [
        ("curl", "curl", "Para descargas HTTP"),
        ("unzip", "unzip", "Para descomprimir archivos Bedrock"),
        ("screen", "screen", "Para gestión de sesiones (opcional pero recomendado)"),
    ]
    missing = []
    for cmd, pkg, desc in required:
        if not shutil.which(cmd):
            missing.append((pkg, desc))
    
    # Verificar Java
    java_ver, _ = detect_java()
    if not java_ver:
        missing.append(("openjdk-21-jre-headless", "Java 21 (requerido para servidores)"))
    
    if missing:
        step("Instalando dependencias faltantes")
        if is_root():
            # Intentar instalar con apt, yum, pacman, etc.
            managers = [
                ("apt-get", ["apt-get", "update"], ["apt-get", "install", "-y"]),
                ("yum", [], ["yum", "install", "-y"]),
                ("dnf", [], ["dnf", "install", "-y"]),
                ("pacman", [], ["pacman", "-S", "--noconfirm"]),
                ("zypper", [], ["zypper", "install", "-y"]),
            ]
            installed = False
            for mgr, update_cmd, install_cmd in managers:
                if shutil.which(mgr):
                    try:
                        if update_cmd:
                            subprocess.check_call(update_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        packages = [pkg for pkg, _ in missing]
                        subprocess.check_call(install_cmd + packages, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        ok(f"Dependencias instaladas con {mgr}")
                        installed = True
                        break
                    except Exception as e:
                        warn(f"Falló instalación con {mgr}: {e}")
            if not installed:
                err("No se pudieron instalar dependencias automáticamente.")
                for pkg, desc in missing:
                    err(f"  Instala manualmente: {pkg} — {desc}")
                sys.exit(1)
        else:
            err("Faltan dependencias y no eres root para instalarlas:")
            for pkg, desc in missing:
                err(f"  {pkg} — {desc}")
            err("Ejecuta como root: sudo python3 <script>")
            sys.exit(1)

def get_key():
    if not termios or not tty:
        return input("Presiona una tecla: ").strip()
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def ask_choice(prompt_text: str, choices: list[str], default: str = "") -> str:
    current = choices.index(default) if default in choices else 0
    n = len(choices)

    hdr = f"  {C.CYAN}{C.BOLD}{prompt_text}{C.RESET}" if _color() else f"  {prompt_text}"
    sys.stdout.write(hdr + "\n")
    sys.stdout.flush()

    def _render(cur: int) -> None:
        for i, choice in enumerate(choices):
            if _color():
                line = (f"  {C.GREEN}>{C.RESET} {C.BOLD}{choice}{C.RESET}" if i == cur
                        else f"    {C.DIM}{choice}{C.RESET}")
            else:
                line = f"  {'>' if i == cur else ' '} {choice}"
            sys.stdout.write(line + "\033[K\n")
        sys.stdout.flush()

    _render(current)

    while True:
        key = get_key()
        prev = current
        if key == '\x1b[A':
            current = max(0, current - 1)
        elif key == '\x1b[B':
            current = min(n - 1, current + 1)
        elif key in ['\n', '\r']:
            sys.stdout.write(f"\033[{n}A")
            for _ in range(n):
                sys.stdout.write("\033[2K\n")
            sys.stdout.write(f"\033[{n}A")
            res = (f"  {C.GREEN}\u2714{C.RESET}  {C.DIM}{prompt_text}:{C.RESET} {C.BOLD}{choices[current]}{C.RESET}"
                   if _color() else f"  [\u2714]  {prompt_text}: {choices[current]}")
            sys.stdout.write(res + "\033[K\n")
            sys.stdout.flush()
            return choices[current]
        if current != prev:
            sys.stdout.write(f"\033[{n}A")
            sys.stdout.flush()
            _render(current)

def ask_yn(prompt_text: str, default: bool = True) -> bool:
    choices = ["Sí", "No"]
    default_choice = "Sí" if default else "No"
    return ask_choice(prompt_text, choices, default_choice) == "Sí"

def ask_int(prompt_text: str, default: int, mn: int = 1, mx: int = 65535) -> int:
    while True:
        raw = ask(prompt_text, str(default))
        try:
            v = int(raw)
            if mn <= v <= mx:
                return v
            err(f"Debe estar entre {mn} y {mx}.")
        except ValueError:
            err("Introduce un número entero.")

def ask_list(prompt_text: str) -> list[str]:
    raw = ask(prompt_text)
    return [v.strip() for v in raw.split(",") if v.strip()]

def display_versions(engine: str) -> None:
    info("Consultando versiones disponibles...")
    versions = get_available_versions(engine)
    if versions:
        print(f"    {C.DIM}Recientes: {', '.join(versions[:8])}{C.RESET}" if _color()
              else f"    Recientes: {', '.join(versions[:8])}")

# ═══════════════════════════════════════════════════════════════════
#  INSTALACIÓN DE PLUGINS
# ═══════════════════════════════════════════════════════════════════
def install_plugins(plugins_dir: Path, urls: dict[str, str]) -> None:
    plugins_dir.mkdir(parents=True, exist_ok=True)
    for name, url in urls.items():
        dest = plugins_dir / f"{name}.jar"
        try:
            info(f"Descargando plugin: {name}")
            download(url, dest)
            ok(name)
        except Exception as e:
            # Intentar fallback si es un release de GitHub (URL de releases/download)
            fallback_tried = False
            if "github.com" in str(url) or name.lower().startswith("viav"):
                try:
                    info(f"Intentando resolver última release de GitHub para: {name}")
                    new_url = resolve_github_latest_asset(str(url), name_prefix=name)
                    if new_url:
                        fallback_tried = True
                        info(f"Descargando versión más reciente desde: {new_url}")
                        download(new_url, dest)
                        ok(f"{name} (latest)")
                except Exception as e2:
                    warn(f"Fallback GitHub para '{name}' falló: {e2}")

            if not fallback_tried or not dest.exists():
                warn(f"Plugin '{name}' falló: {e}")

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE IP / DOMINIO
# ═══════════════════════════════════════════════════════════════════
def configure_network(port: int, protocol: str = "tcp") -> dict:
    """Detecta IPs y configura dominio/IP del servidor."""
    step("Configuración de red e IP")

    public_ip = get_public_ip()
    local_ip  = get_local_ip()
    ok(f"IP pública detectada:  {C.WHITE}{public_ip}{C.RESET}" if _color() else f"IP pública: {public_ip}")
    ok(f"IP local detectada:    {C.WHITE}{local_ip}{C.RESET}"  if _color() else f"IP local:   {local_ip}")
    sep()

    print()
    print(f"  {C.BOLD}¿Cómo se conectarán los jugadores?{C.RESET}" if _color()
          else "  ¿Cómo se conectarán los jugadores?")
    print(f"  {C.DIM}1) IP pública directa  ({public_ip}:{port}){C.RESET}" if _color()
          else f"  1) IP publica ({public_ip}:{port})")
    print(f"  {C.DIM}2) Dominio propio      (ej: mc.miservidor.com){C.RESET}" if _color()
          else "  2) Dominio propio")
    print(f"  {C.DIM}3) Solo red local      ({local_ip}:{port}){C.RESET}" if _color()
          else f"  3) Solo red local ({local_ip}:{port})")
    print(f"  {C.DIM}4) IP personalizada    (introducir manualmente){C.RESET}" if _color()
          else "  4) IP personalizada")
    print()

    choice = ask_choice("Elige una opción", ["1", "2", "3", "4"], "1")

    domain     = ""
    bind_ip    = ""       # vacío = escucha en todas las interfaces
    connect_ip = public_ip

    if choice == "1":
        connect_ip = public_ip
        bind_ip    = ""
        ok(f"Los jugadores se conectarán a: {public_ip}:{port}")

    elif choice == "2":
        print()
        info("Para usar un dominio, necesitas apuntar un registro DNS tipo A a tu IP pública.")
        info(f"  Tu IP pública es: {public_ip}")
        info("  En tu panel DNS crea:  A  mc.tudominio.com  →  " + public_ip)
        print()
        domain = ask("Introduce tu dominio (ej: mc.tudominio.com)")
        if domain:
            resolved = resolve_domain(domain)
            if resolved == public_ip:
                ok(f"Dominio {domain} resuelve correctamente a {public_ip} ✔")
            elif resolved == "No resuelto":
                warn(f"El dominio '{domain}' no resuelve todavía. Puede tardar hasta 24-48h en propagarse.")
            else:
                warn(f"'{domain}' resuelve a {resolved}, pero tu IP pública es {public_ip}.")
                warn("Comprueba tu configuración DNS.")
            connect_ip = domain
        bind_ip = ""

    elif choice == "3":
        connect_ip = local_ip
        bind_ip    = local_ip
        warn("Modo red local: solo jugadores en la misma red WiFi/LAN podrán conectarse.")

    elif choice == "4":
        connect_ip = ask("IP o hostname al que conectarse", public_ip)
        bind_ip    = ask("IP en la que escucha el servidor (vacío = todas)", "")

    # Verificar puerto
    if check_port_available(port):
        ok(f"Puerto {port} disponible.")
    else:
        warn(f"Puerto {port} parece estar en uso. Puede haber un conflicto.")

    # Abrir puerto en firewall
    if is_root():
        open_firewall_port(port, protocol)
        if protocol == "tcp":
            # Abrir también UDP por si acaso (algunos configs lo requieren)
            pass
    else:
        warn(f"No root: abre el puerto {port}/{protocol} manualmente en tu firewall.")

    return {
        "public_ip":  public_ip,
        "local_ip":   local_ip,
        "connect_ip": connect_ip,
        "bind_ip":    bind_ip,
        "domain":     domain,
        "port":       port,
    }

# ═══════════════════════════════════════════════════════════════════
#  WIZARD PRINCIPAL
# ═══════════════════════════════════════════════════════════════════
def run_wizard() -> int:
    banner()
    check_dependencies()
    title("Bienvenido al asistente de configuración v3.0")
    print("  Este asistente configura todo lo necesario para que tu servidor")
    print("  Minecraft quede corriendo en Linux de forma permanente.")
    print(f"  {C.DIM}Presiona Enter para aceptar el valor entre [corchetes].{C.RESET}\n" if _color()
          else "  Presiona Enter para el valor por defecto.\n")

    # Cargar progreso previo si existe
    prev = load_progress()
    resume_state = None
    completed: set[str] = set()
    if prev:
        if ask_yn("Se encontró una configuración previa. ¿Deseas reanudarla?", True):
            ok("Reanudando configuración previa.")
            resume_state = prev.get("data", {})
            completed = set(prev.get("completed", []))
            # validar
            valid, msgs = validate_state(resume_state)
            if not valid:
                warn("La configuración guardada tiene problemas:")
                for m in msgs:
                    warn(" - " + m)
                if not ask_yn("¿Deseas intentar continuar con la configuración guardada de todos modos?", False):
                    clear_progress()
                    resume_state = None
                    completed = set()
        else:
            clear_progress()

    if not is_root():
        warn("No estás ejecutando como root (sudo). Algunas funciones estarán limitadas:")
        warn("  - No se podrá crear usuario del sistema")
        warn("  - No se instalarán servicios systemd en /etc/systemd/system")
        warn("  - No se abrirán puertos en el firewall automáticamente")
        print()
        confirm = ask_yn("¿Continuar sin root?", True)
        if not confirm:
            info("Ejecuta con: sudo python3 <script>")
            return 1

    # ── JAVA CHECK ────────────────────────────────────────────────
    step("Verificando Java")
    java_ver, java_path = detect_java()
    if java_ver:
        ok(f"Java detectado: {java_ver}")
        if java_path:
            info(f"Ruta: {java_path}")
    else:
        warn("Java no encontrado.")
        if is_root():
            do_install = ask_yn("¿Instalar Java 21 automáticamente?", True)
            if do_install:
                install_java_if_missing()
        else:
            err("Instala Java manualmente: sudo apt install openjdk-21-jre-headless")

    # marcar progreso
    state = resume_state or {}
    state.setdefault("completed", [])
    if "java_check" not in state["completed"]:
        state["completed"].append("java_check")
        state["data"] = state.get("data", {})
        save_progress({"completed": state["completed"], "data": state["data"]})

    # ── NOMBRE Y DATOS BÁSICOS ────────────────────────────────────
    step("Datos básicos del servidor")
    if resume_state and "basic" in completed:
        server_name = resume_state.get("server_name", "Servidor")
        motd = resume_state.get("motd", f"§b{server_name} §7» §aOnline")
    else:
        server_name = ask("Nombre del servidor", "Servidor")
        motd        = ask("MOTD (mensaje en la lista)", f"§b{server_name} §7» §aOnline")
        # guardar
        state = state if 'state' in locals() else {"completed": [], "data": {}}
        state["data"]["server_name"] = server_name
        state["data"]["motd"] = motd
        if "basic" not in state["completed"]:
            state["completed"].append("basic")
        save_progress({"completed": state["completed"], "data": state["data"]})

    # ── TIPO DE SERVIDOR ──────────────────────────────────────────
    step("¿Qué tipo de servidor quieres instalar?")
    print(f"  {C.CYAN}java{C.RESET}    → Java Edition (PC, Mac, Linux)" if _color() else "  java    → Java Edition")
    print(f"  {C.CYAN}bedrock{C.RESET} → Bedrock Edition (Windows 10, móvil, consolas)" if _color() else "  bedrock → Bedrock Edition")
    print(f"  {C.CYAN}ambos{C.RESET}   → Ambas ediciones\n" if _color() else "  ambos   → Ambas ediciones\n")
    if resume_state and "server_type" in completed:
        server_type = resume_state.get("server_type", "java")
    else:
        server_type = ask_choice("Tipo", ["java", "bedrock", "ambos"], "java")
        state["data"]["server_type"] = server_type
        if "server_type" not in state["completed"]:
            state["completed"].append("server_type")
        save_progress({"completed": state["completed"], "data": state["data"]})
    do_java    = server_type in ("java", "ambos")
    do_bedrock = server_type in ("bedrock", "ambos")

    # ── MODO ONLINE / OFFLINE ─────────────────────────────────────
    step("Modo de autenticación")
    print(f"  {C.BOLD}online-mode=true{C.RESET}  → Solo jugadores con cuenta Minecraft ORIGINAL (más seguro)" if _color()
          else "  online-mode=true  → Solo cuentas originales")
    print(f"  {C.BOLD}online-mode=false{C.RESET} → Cualquier jugador puede entrar (cuentas no-premium / cracked)" if _color()
          else "  online-mode=false → Cuentas no-premium / cracked")
    print()
    if resume_state and "auth_mode" in completed:
        online_mode = resume_state.get("online_mode", False)
        ok(f"Usando online_mode guardado: {online_mode}")
    else:
        online_mode = ask_yn("¿Requerir cuenta Minecraft original (online-mode)?", False)
        state["data"]["online_mode"] = online_mode
        if "auth_mode" not in state["completed"]:
            state["completed"].append("auth_mode")
        save_progress({"completed": state["completed"], "data": state["data"]})
    if not online_mode:
        warn("online-mode=false: cualquier jugador puede entrar sin verificación.")
        warn("Recomendado instalar AuthMe o similar para seguridad.")
    else:
        ok("online-mode=true: solo cuentas originales podrán conectarse.")

    # ── INSTANCIAS JAVA ───────────────────────────────────────────
    java_instances: list[dict] = []
    if do_java:
        if resume_state and "java_instances" in completed:
            java_instances = resume_state.get("java_instances", [])
            ok(f"Usando {len(java_instances)} instancias Java guardadas.")
        else:
            step("Configuración Java Edition")
            n = ask_int("¿Cuántas instancias Java quieres?", 1, 1, 10)

            for i in range(n):
                print()
                print(f"  {C.BOLD}── Instancia Java #{i+1} ──{C.RESET}" if _color()
                    else f"  -- Instancia Java #{i+1} --")
                print()
                print("  Motores disponibles:")
            engines = {
                "paper":   "Alto rendimiento, compatible con plugins Bukkit/Spigot (recomendado)",
                "purpur":  "Fork de Paper con opciones extra de configuración",
                "vanilla": "Servidor oficial Mojang, sin plugins",
                "spigot":  "Base de Paper, requiere compilar con BuildTools",
                "fabric":  "Ligero y rápido, ideal para mods técnicos",
            }
            for eng, desc in engines.items():
                mark = f"{C.GREEN}●{C.RESET} {C.BOLD}{eng:<10}{C.RESET}" if _color() else f"  * {eng:<10}"
                print(f"  {mark} {C.DIM}{desc}{C.RESET}" if _color() else f"  {mark} {desc}")
            print()

            engine  = ask_choice("Motor", list(engines.keys()), "paper")
            info("Consultando versiones disponibles...")
            available = get_available_versions(engine)
            if len(available) > 1:
                version_choice = ask_choice(f"Versión de {engine}", available, available[0])
                # Si la elección es 'latest (X.X.X)', extraer solo 'latest'
                version = "latest" if version_choice.startswith("latest") else version_choice
            else:
                version = "latest"

            default_port = 25565 + i
            net = configure_network(default_port, "tcp")

            max_players = ask_int("Máximo de jugadores", 40, 1, 1000)
            difficulty  = ask_choice("Dificultad", ["peaceful", "easy", "normal", "hard"], "normal")
            gamemode    = ask_choice("Modo de juego", ["survival", "creative", "adventure", "spectator"], "survival")
            pvp         = ask_yn("¿PvP activado?", True)
            cmd_blocks  = ask_yn("¿Bloques de comandos?", False)
            whitelist   = ask_yn("¿Lista blanca (whitelist)?", False)
            view_dist   = ask_int("Distancia de visión (chunks)", 10, 2, 32)
            seed        = ask("Semilla del mundo (vacío = aleatoria)", "")
            jvm_flags   = ask("JVM flags", "-Xms512M -Xmx2G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200")

            java_instances.append({
                "engine": engine, "version": version,
                "net": net,
                "max_players": max_players, "difficulty": difficulty,
                "gamemode": gamemode, "pvp": pvp, "cmd_blocks": cmd_blocks,
                "whitelist": whitelist, "view_dist": view_dist,
                "seed": seed, "jvm_flags": jvm_flags,
                "online_mode": online_mode,
                "name": server_name, "motd": motd,
            })
            # guardar instancias java
            state["data"]["java_instances"] = java_instances
            if "java_instances" not in state["completed"]:
                state["completed"].append("java_instances")
            save_progress({"completed": state["completed"], "data": state["data"]})

    # ── INSTANCIAS BEDROCK ────────────────────────────────────────
    bedrock_instances: list[dict] = []
    if do_bedrock:
        if resume_state and "bedrock_instances" in completed:
            bedrock_instances = resume_state.get("bedrock_instances", [])
            ok(f"Usando {len(bedrock_instances)} instancias Bedrock guardadas.")
        else:
            step("Configuración Bedrock Edition")
            n = ask_int("¿Cuántas instancias Bedrock?", 1, 1, 5)
            for i in range(n):
                print(f"\n  {C.BOLD}── Instancia Bedrock #{i+1} ──{C.RESET}" if _color()
                      else f"\n  -- Bedrock #{i+1} --")
                info("Consultando versiones de Bedrock disponibles...")
                available_bedrock = get_available_versions("bedrock")
                bver_choice = ask_choice("Versión Bedrock", available_bedrock, available_bedrock[0])
                bver = "latest" if bver_choice.startswith("latest") else bver_choice
                net  = configure_network(19132 + i, "udp")
                bedrock_instances.append({"version": bver, "net": net})
            state["data"]["bedrock_instances"] = bedrock_instances
            if "bedrock_instances" not in state["completed"]:
                state["completed"].append("bedrock_instances")
            save_progress({"completed": state["completed"], "data": state["data"]})

    # ── PLUGINS / MODS ────────────────────────────────────────────
    selected_plugins: dict[str, str] = {}
    selected_mods:    dict[str, str] = {}
    if do_java:
        if resume_state and "plugins_mods" in completed:
            selected_plugins = resume_state.get("plugins", {})
            selected_mods = resume_state.get("mods", {})
            ok(f"Usando plugins/mods guardados: {', '.join(selected_plugins.keys())}")
        else:
            step("Plugins y Mods")

            # ── Geyser + Floodgate: crossplay Java <-> Bedrock ──────────
            if do_java:
                step("Juego cruzado Java Edition ↔ Bedrock Edition")
                print()
                if _color():
                    print(f"  {C.CYAN}Geyser{C.RESET} permite que jugadores de {C.BOLD}Bedrock{C.RESET} (móvil, consola, Windows 10)")
                    print(f"  se conecten a tu servidor {C.BOLD}Java Edition{C.RESET} sin modificar el cliente.")
                    print(f"  {C.CYAN}Floodgate{C.RESET} les permite entrar {C.BOLD}sin cuenta Java{C.RESET} (Xbox/PSN/cuenta Bedrock).")
                else:
                    print("  Geyser permite que jugadores Bedrock se conecten al servidor Java.")
                    print("  Floodgate les permite entrar sin cuenta Java.")
                print()
                add_geyser = ask_yn("¿Instalar Geyser + Floodgate (crossplay Java ↔ Bedrock)?", do_bedrock)
                if add_geyser:
                    selected_plugins["Geyser-Spigot"] = PLUGINS["Geyser-Spigot"]
                    selected_plugins["Floodgate"]     = PLUGINS["Floodgate"]
                    ok("Geyser + Floodgate añadidos.")
                    info("Los jugadores Bedrock se conectarán al mismo puerto que Java (25565 por defecto).")
                    if not online_mode:
                        info("Con online-mode=false y Floodgate, los jugadores Bedrock entran con su cuenta Xbox/PSN.")

            # Auto-agregar ViaVersion si online_mode es False (para que conecten varias versiones)
            multiversion = ask_yn("¿Permitir que se conecten jugadores de distintas versiones de Minecraft?", False)
            if multiversion:
                selected_plugins["ViaVersion"]   = PLUGINS["ViaVersion"]
                selected_plugins["ViaBackwards"] = PLUGINS["ViaBackwards"]
                ok("ViaVersion + ViaBackwards añadidos (soporte multi-versión).")

            # Si offline, sugerir AuthMe
            if not online_mode:
                add_authme = ask_yn("¿Instalar plugin de login/registro (AuthMe) para cuentas no-premium?", True)
                if add_authme:
                    selected_plugins["AuthMe"] = (
                        "https://github.com/AuthMe/AuthMeReloaded/releases/download/5.6.0/AuthMe-5.6.0.jar"
                    )
                    ok("AuthMe añadido para gestión de cuentas no-premium.")

            use_plugins = ask_yn("¿Instalar plugins adicionales?", False)
            if use_plugins:
                print()
                print("  Plugins disponibles:")
                for name in PLUGINS:
                    print(f"  {C.CYAN}  {name}{C.RESET}" if _color() else f"    {name}")
                print()
                defaults = ask_yn("¿Instalar paquete básico? (LuckPerms + EssentialsX + Vault)", True)
                if defaults:
                    for p in ("LuckPerms", "EssentialsX", "Vault"):
                        selected_plugins[p] = PLUGINS[p]
                else:
                    names = ask_list(f"Nombres separados por comas ({', '.join(PLUGINS.keys())})")
                    for n in names:
                        match = next((k for k in PLUGINS if k.lower() == n.lower()), None)
                        if match:
                            selected_plugins[match] = PLUGINS[match]
                        else:
                            warn(f"Plugin '{n}' no reconocido.")

                extra_urls = ask_list("URLs adicionales de plugins (vacío para omitir)")
                for url in extra_urls:
                    name = url.split("/")[-1].replace(".jar", "")
                    selected_plugins[name] = url

            fabric_inst = [i for i in java_instances if i["engine"] == "fabric"]
            if fabric_inst:
                use_mods = ask_yn("¿Instalar mods de rendimiento para Fabric? (Lithium + FerriteCore)", True)
                if use_mods:
                    selected_mods.update({"Lithium": MODS["Lithium"], "FerriteCore": MODS["FerriteCore"]})
                extra_mod_urls = ask_list("URLs adicionales de mods (vacío para omitir)")
                for url in extra_mod_urls:
                    name = url.split("/")[-1].replace(".jar", "")
                    selected_mods[name] = url
        # guardar plugins/mods
        state["data"]["plugins"] = selected_plugins
        state["data"]["mods"] = selected_mods
        if "plugins_mods" not in state["completed"]:
            state["completed"].append("plugins_mods")
        save_progress({"completed": state["completed"], "data": state["data"]})

    # ── PERSISTENCIA ─────────────────────────────────────────────
    step("Persistencia — ¿Cómo debe mantenerse corriendo el servidor?")
    print()
    persist_opts = {
        "systemd": "Servicio del sistema Linux (RECOMENDADO) — arranca con el servidor y se reinicia solo",
        "screen":  "GNU Screen — sesiones detachables, fácil de gestionar",
        "tmux":    "tmux — sesiones detachables más avanzadas",
        "docker":  "Docker — contenedores aislados",
        "manual":  "Manual — solo genera start.sh, tú lo ejecutas",
    }
    for k, v in persist_opts.items():
        bullet = f"{C.GREEN}●{C.RESET}" if _color() else "*"
        print(f"  {bullet} {C.BOLD}{k:<10}{C.RESET} {C.DIM}{v}{C.RESET}" if _color()
              else f"  * {k:<10} {v}")
    print()

    # Recomendar screen si no hay root
    default_persist = "systemd" if is_root() else "screen"
    if resume_state and "persistence" in completed:
        persistence = resume_state.get("persistence", default_persist)
        system_user = resume_state.get("system_user", "minecraft")
        systemd_opts = resume_state.get("systemd_opts", {})
        ok(f"Usando persistencia guardada: {persistence}")
    else:
        persistence = ask_choice("Modo", list(persist_opts.keys()), default_persist)
        system_user = "minecraft"
        if persistence == "systemd" and is_root():
            system_user = ask("Usuario del sistema para el servicio", "minecraft")
            if not user_exists(system_user):
                create_system_user(system_user)
            advanced = ask_yn("¿Configurar opciones avanzadas del servicio systemd?", False)
            systemd_opts = configure_systemd_options() if advanced else {}
        else:
            systemd_opts = {}
        state["data"]["persistence"] = persistence
        state["data"]["system_user"] = system_user
        state["data"]["systemd_opts"] = systemd_opts
        if "persistence" not in state["completed"]:
            state["completed"].append("persistence")
        save_progress({"completed": state["completed"], "data": state["data"]})

    # ── BACKUPS ───────────────────────────────────────────────────
    step("Backups automáticos")
    if resume_state and "backups" in completed:
        do_backups = resume_state.get("do_backups", True)
        setup_cron = resume_state.get("setup_cron", False)
        ok(f"Usando configuración de backups guardada: do_backups={do_backups}")
    else:
        do_backups = ask_yn("¿Generar script de backup?", True)
        if do_backups and persistence == "systemd" and is_root():
            setup_cron = ask_yn("¿Programar backup diario automático con cron?", True)
        else:
            setup_cron = False
        state["data"]["do_backups"] = do_backups
        state["data"]["setup_cron"] = setup_cron
        if "backups" not in state["completed"]:
            state["completed"].append("backups")
        save_progress({"completed": state["completed"], "data": state["data"]})

    # ── RESUMEN ANTES DE INSTALAR ─────────────────────────────────
    step("Resumen de configuración")
    print()
    for i, inst in enumerate(java_instances, 1):
        net = inst["net"]
        ip_str = net.get("domain") or net.get("connect_ip", "?")
        ok(f"Java #{i}: {inst['engine']} {inst['version']}"
           f"  |  {ip_str}:{net['port']}"
           f"  |  {'PREMIUM' if inst['online_mode'] else 'NO-PREMIUM/CRACKED'}"
           f"  |  {inst['max_players']} jugadores")
    for i, inst in enumerate(bedrock_instances, 1):
        net = inst["net"]
        ip_str = net.get("domain") or net.get("connect_ip", "?")
        ok(f"Bedrock #{i}: {inst['version']}  |  {ip_str}:{net['port']} UDP")
    if selected_plugins:
        ok(f"Plugins: {', '.join(selected_plugins.keys())}")
    if selected_mods:
        ok(f"Mods:    {', '.join(selected_mods.keys())}")
    ok(f"Persistencia: {persistence}")
    ok(f"Backups: {'si' if do_backups else 'no'}")
    print()
    # marcar resumen completado y guardar estado
    state["data"]["plugins_list"] = list(selected_plugins.keys())
    state["data"]["mods_list"] = list(selected_mods.keys())
    if "summary" not in state["completed"]:
        state["completed"].append("summary")
    save_progress({"completed": state["completed"], "data": state["data"]})

    if not ask_yn("¿Confirmar e iniciar instalación?", True):
        warn("Instalación cancelada.")
        return 1

    # ═══════════════════════════════════════════════════════════════
    #  INSTALACIÓN
    # ═══════════════════════════════════════════════════════════════
    step("Iniciando instalación")
    for d in (SERVERS, BACKUPS, LOGS, DOCS, SYSTEMD, TESTS):
        d.mkdir(parents=True, exist_ok=True)

    write_gitignore(ROOT / ".gitignore")

    FETCHERS = {
        "paper":   lambda v, d: fetch_papermc(v, None, d),
        "purpur":  lambda v, d: fetch_purpur(v, None, d),
        "vanilla": lambda v, d: fetch_vanilla(v, d),
        "spigot":  lambda v, d: fetch_spigot(v, d),
        "fabric":  lambda v, d: fetch_fabric(v, d),
    }

    installed_java:    list[Path] = []
    installed_bedrock: list[Path] = []
    start_scripts:     list[tuple[str, Path]] = []
    docker_services:   list[dict] = []
    systemd_units:     list[Path] = []

    # ── INSTALAR JAVA ─────────────────────────────────────────────
    for i, inst in enumerate(java_instances, 1):
        engine  = inst["engine"]
        version = inst["version"]
        net     = inst["net"]
        label   = f"{server_name}-{engine}-{i}"
        td      = SERVERS / label
        td.mkdir(parents=True, exist_ok=True)

        step(f"Instalando Java #{i}: {engine} {version}")
        try:
            result = FETCHERS[engine](version, td)
        except SystemExit as e:
            err(str(e)); continue

        verify_jar(result)
        if result.get("note"):
            info(f"Nota: {result['note']}")

        write_eula(td / "eula.txt")
        write_server_properties(td / "server.properties", {
            "name":            inst["name"],
            "motd":            inst["motd"],
            "bind_ip":         net.get("bind_ip", ""),
            "port":            net["port"],
            "online_mode":     inst["online_mode"],
            "max_players":     inst["max_players"],
            "difficulty":      inst["difficulty"],
            "gamemode":        inst["gamemode"],
            "pvp":             inst["pvp"],
            "command_blocks":  inst["cmd_blocks"],
            "whitelist":       inst["whitelist"],
            "enforce_whitelist": inst["whitelist"],
            "view_distance":   inst["view_dist"],
            "seed":            inst["seed"],
        })

        jar_name = result["jar"].name if result.get("jar") else "server.jar"
        write_start_script(td, jar_name, inst["jvm_flags"], label)

        (td / "plugins").mkdir(exist_ok=True)
        (td / "logs").mkdir(exist_ok=True)

        if selected_plugins and engine not in ("vanilla",):
            install_plugins(td / "plugins", selected_plugins)
        if selected_mods and engine == "fabric":
            install_plugins(td / "mods", selected_mods)

        # Permisos
        if is_root() and persistence == "systemd":
            set_directory_permissions(td, system_user)
            ensure_parents_traversable(td)
        if persistence == "systemd":
            unit_name = f"{label}.service"
            unit_path = SYSTEMD / unit_name
            write_systemd_unit(unit_path, td, td / "start.sh", system_user,
                               description=f"{label}",
                               opts=systemd_opts)

        # Docker
        if persistence == "docker":
            write_dockerfile(td / "Dockerfile", jar_name, inst["jvm_flags"])
            docker_services.append({"name": label, "port": net["port"],
                                     "path": str(td), "proto": "tcp"})

        start_scripts.append((label, td / "start.sh"))
        if persistence == "systemd":
            systemd_units.append(unit_path)
        installed_java.append(td)
        ok(f"Java #{i} listo en: {td}")

    # ── INSTALAR BEDROCK ──────────────────────────────────────────
    for i, inst in enumerate(bedrock_instances, 1):
        net = inst["net"]
        td  = SERVERS / f"{server_name}-bedrock-{inst['version']}-{i}"
        td.mkdir(parents=True, exist_ok=True)

        step(f"Instalando Bedrock #{i}: {inst['version']}")
        result = fetch_bedrock(inst["version"], td)
        if result.get("jar"):
            ok(f"Bedrock descargado: {result['jar']}")
        elif result.get("note"):
            warn(result["note"])

        write_bedrock_start(td)

        if is_root() and persistence == "systemd":
            set_directory_permissions(td, system_user)
            ensure_parents_traversable(td)
            unit_name = f"{server_name}-bedrock-{i}.service"
            unit_path = SYSTEMD / unit_name
            write_systemd_unit(unit_path, td, td / "start.sh", system_user,
                               description=f"{server_name} Bedrock #{i}",
                               opts=systemd_opts)
            systemd_units.append(unit_path)

        if persistence == "docker":
            docker_services.append({"name": f"{server_name}-bedrock-{i}", "port": net["port"],
                                     "path": str(td), "proto": "udp"})

        start_scripts.append((f"{server_name}-bedrock-{i}", td / "start.sh"))
        installed_bedrock.append(td)
        ok(f"Bedrock #{i} listo en: {td}")

    all_installed = installed_java + installed_bedrock

    # ── BACKUP ────────────────────────────────────────────────────
    if do_backups and all_installed:
        write_backup_script(ROOT / "backup.sh", all_installed)
        ok("backup.sh generado.")
        if setup_cron and is_root():
            cron_line = f"0 3 * * * root /usr/bin/python3 {ROOT}/<script> backup >> {LOGS}/backup.log 2>&1"
            cron_file = Path("/etc/cron.d/minecraft-backup")
            try:
                cron_file.parent.mkdir(parents=True, exist_ok=True)
                cron_file.write_text(cron_line + "\n")
                ok(f"Cron diario instalado: {cron_file} (a las 3:00 AM)")
            except Exception as e:
                warn(f"No se pudo instalar cron: {e}")
                info(f"Agrega manualmente: {cron_line}")

    # ── PERSISTENCIA ─────────────────────────────────────────────
    step(f"Configurando persistencia: {persistence}")

    if persistence == "systemd" and is_root():
        sys_dir = Path("/etc/systemd/system")
        for unit in systemd_units:
            target = sys_dir / unit.name
            try:
                shutil.copy2(str(unit), str(target))
                ok(f"Instalado: {target}")
            except Exception as e:
                warn(f"No se pudo copiar {unit.name}: {e}")
        try:
            subprocess.check_call(["systemctl", "daemon-reload"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok("systemctl daemon-reload ejecutado.")
        except Exception as e:
            warn(f"daemon-reload falló: {e}")
        for unit in systemd_units:
            try:
                subprocess.check_call(["systemctl", "enable", unit.stem],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok(f"Habilitado al arranque: {unit.stem}")
                subprocess.check_call(["systemctl", "start", unit.stem],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok(f"Iniciado: {unit.stem}")
            except Exception as e:
                warn(f"No se pudo habilitar/iniciar {unit.stem}: {e}")

    elif persistence == "screen":
        if not shutil.which("screen"):
            warn("GNU Screen no instalado.")
            if is_root():
                try:
                    subprocess.check_call(["apt-get", "install", "-y", "screen"],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    ok("screen instalado.")
                except Exception:
                    warn("Instala screen manualmente: sudo apt install screen")
        launcher = ROOT / "launch_all.sh"
        write_screen_launcher(launcher, start_scripts)
        ok(f"launch_all.sh generado.")
        # Lanzar ahora
        if ask_yn("¿Iniciar todos los servidores ahora?", True):
            subprocess.call(["bash", str(launcher)])

    elif persistence == "tmux":
        if not shutil.which("tmux"):
            warn("tmux no instalado.")
            if is_root():
                try:
                    subprocess.check_call(["apt-get", "install", "-y", "tmux"],
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    ok("tmux instalado.")
                except Exception:
                    warn("Instala tmux: sudo apt install tmux")
        launcher = ROOT / "launch_all.sh"
        write_tmux_launcher(launcher, start_scripts)
        ok("launch_all.sh generado.")
        if ask_yn("¿Iniciar todos los servidores ahora?", True):
            subprocess.call(["bash", str(launcher)])

    elif persistence == "docker":
        if docker_services:
            write_docker_compose(ROOT / "docker-compose.yml", docker_services)
            ok("docker-compose.yml generado.")
        if ask_yn("¿Lanzar con docker-compose ahora?", False):
            subprocess.call(["docker-compose", "up", "-d"])

    elif persistence == "manual":
        ok("Scripts start.sh generados en cada directorio de servidor.")
        info("Para iniciar: bash servers/java-paper-1/start.sh")

    # ── README ────────────────────────────────────────────────────
    net_info = java_instances[0]["net"] if java_instances else (
               bedrock_instances[0]["net"] if bedrock_instances else {})
    write_readme(ROOT / "README.md", {
        "server_name": server_name,
        "public_ip":   net_info.get("public_ip", ""),
        "domain":      net_info.get("domain", ""),
        "java_port":   java_instances[0]["net"]["port"] if java_instances else 25565,
        "bedrock_port": bedrock_instances[0]["net"]["port"] if bedrock_instances else 19132,
    })

    # ── GUARDAR CONFIG ────────────────────────────────────────────
    config = {
        "server_name":       server_name,
        "persistence":       persistence,
        "system_user":       system_user if persistence == "systemd" else "",
        "java_instances":    [
            {k: v for k, v in inst.items() if k != "net"}
            | {"port": inst["net"]["port"], "connect_ip": inst["net"].get("connect_ip", "")}
            for inst in java_instances
        ],
        "bedrock_instances": [
            {"version": inst["version"], "port": inst["net"]["port"]}
            for inst in bedrock_instances
        ],
        "plugins":  list(selected_plugins.keys()),
        "mods":     list(selected_mods.keys()),
    }
    CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    ok("Configuración guardada en config.json")
    # Instalación completada: eliminar progreso guardado
    try:
        clear_progress()
    except Exception:
        pass

    # ── TEST STUB ─────────────────────────────────────────────────
    test_file = TESTS / "test_installer.py"
    if not test_file.exists():
        test_file.write_text(textwrap.dedent("""\
            import unittest, json
            from pathlib import Path
            ROOT = Path(__file__).resolve().parent.parent
            class TestInstaller(unittest.TestCase):
                def test_config_exists(self):
                    self.assertTrue((ROOT / 'config.json').exists())
                def test_servers_exist(self):
                    self.assertTrue((ROOT / 'servers').is_dir())
                def test_config_valid(self):
                    cfg = json.loads((ROOT / 'config.json').read_text())
                    self.assertIn('server_name', cfg)
            if __name__ == '__main__':
                unittest.main()
        """))

    # ── RESUMEN FINAL ─────────────────────────────────────────────
    print()
    sep()
    title("✅  ¡Instalación completada!")
    sep()
    print()
    for inst in java_instances:
        net    = inst["net"]
        ip_str = net.get("domain") or net.get("connect_ip", "?")
        mode   = "PREMIUM" if inst["online_mode"] else "NO-PREMIUM"
        ok(f"Java  {inst['engine']:<8} {inst['version']:<12} → {ip_str}:{net['port']}  [{mode}]")
    for inst in bedrock_instances:
        net    = inst["net"]
        ip_str = net.get("domain") or net.get("connect_ip", "?")
        ok(f"Bedrock  {inst['version']:<12}           → {ip_str}:{net['port']} UDP")
    print()

    if persistence == "systemd":
        info("Servidores habilitados como servicios del sistema.")
        info(f"  Estado:   sudo systemctl status java-paper-1")
        info(f"  Logs:     sudo journalctl -u java-paper-1 -f")
        info(f"  Detener:  sudo systemctl stop java-paper-1")
    elif persistence in ("screen", "tmux"):
        info(f"Servidores lanzados con {persistence}.")
        info(f"  bash launch_all.sh   (relanzar todos)")
    elif persistence == "docker":
        info("  docker-compose ps    (ver estado)")
        info("  docker-compose logs  (ver logs)")
    elif persistence == "manual":
        info("  bash servers/java-paper-1/start.sh")

    print()
    info("Otros comandos:")
    info("  sudo python3 <script> start    → Iniciar todos")
    info("  sudo python3 <script> stop     → Detener todos")
    info("  sudo python3 <script> status   → Ver estado")
    info("  sudo python3 <script> backup   → Crear backup")
    info("  sudo python3 <script> logs     → Ver logs")
    print()
    return 0

# ═══════════════════════════════════════════════════════════════════
#  COMANDOS DE GESTIÓN
# ═══════════════════════════════════════════════════════════════════
def load_config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    return {}

def run_start() -> int:
    cfg = load_config()
    persistence = cfg.get("persistence", "manual")
    title("Iniciando servidores")

    if persistence == "systemd":
        units = list(SYSTEMD.glob("*.service"))
        if not units:
            err("No se encontraron units de systemd. Ejecuta el asistente primero.")
            return 1
        for unit in units:
            try:
                subprocess.check_call(["systemctl", "start", unit.stem])
                ok(f"Iniciado: {unit.stem}")
            except Exception as e:
                err(f"No se pudo iniciar {unit.stem}: {e}")

    elif persistence in ("screen", "tmux"):
        launcher = ROOT / "launch_all.sh"
        if launcher.exists():
            return subprocess.call(["bash", str(launcher)])
        err("launch_all.sh no encontrado.")
        return 1

    elif persistence == "docker":
        return subprocess.call(["docker-compose", "up", "-d"])

    else:  # manual
        scripts = list(SERVERS.rglob("start.sh"))
        if not scripts:
            err("No hay start.sh. Ejecuta el asistente primero.")
            return 1
        for sh in scripts:
            info(f"Iniciando: {sh.parent.name}")
            subprocess.Popen(["bash", str(sh)], cwd=str(sh.parent))
    return 0

def run_stop() -> int:
    cfg = load_config()
    persistence = cfg.get("persistence", "manual")
    title("Deteniendo servidores")

    if persistence == "systemd":
        units = list(SYSTEMD.glob("*.service"))
        for unit in units:
            try:
                subprocess.check_call(["systemctl", "stop", unit.stem])
                ok(f"Detenido: {unit.stem}")
            except Exception as e:
                err(f"No se pudo detener {unit.stem}: {e}")

    elif persistence == "screen":
        result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "mc_" in line:
                name = line.strip().split(".")[1].split("\t")[0] if "." in line else ""
                if name:
                    subprocess.run(["screen", "-S", name, "-X", "quit"])
                    ok(f"Sesión screen detenida: {name}")

    elif persistence == "tmux":
        result = subprocess.run(["tmux", "ls"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            name = line.split(":")[0]
            if name:
                subprocess.run(["tmux", "kill-session", "-t", name])
                ok(f"Sesión tmux detenida: {name}")

    elif persistence == "docker":
        return subprocess.call(["docker-compose", "down"])

    else:
        # Enviar SIGTERM a procesos Java del servidor
        result = subprocess.run(["pgrep", "-f", "server.jar"], capture_output=True, text=True)
        for pid in result.stdout.splitlines():
            try:
                subprocess.call(["kill", "-TERM", pid])
                ok(f"Proceso {pid} terminado.")
            except Exception:
                pass
    return 0

def run_status() -> int:
    cfg = load_config()
    persistence = cfg.get("persistence", "manual")
    title("Estado de servidores")

    if persistence == "systemd":
        units = list(SYSTEMD.glob("*.service"))
        if not units:
            warn("No hay units instaladas.")
            return 0
        for unit in units:
            try:
                r = subprocess.run(["systemctl", "is-active", unit.stem],
                                   capture_output=True, text=True)
                status = r.stdout.strip()
                if status == "active":
                    ok(f"{unit.stem}: {C.GREEN}activo{C.RESET}" if _color() else f"{unit.stem}: ACTIVO")
                else:
                    err(f"{unit.stem}: {status}")
            except Exception:
                err(f"{unit.stem}: no disponible")

    elif persistence == "screen":
        subprocess.call(["screen", "-ls"])

    elif persistence == "tmux":
        subprocess.call(["tmux", "ls"])

    elif persistence == "docker":
        subprocess.call(["docker-compose", "ps"])

    else:
        result = subprocess.run(["pgrep", "-af", "server.jar"], capture_output=True, text=True)
        if result.stdout.strip():
            for line in result.stdout.splitlines():
                ok(f"Proceso activo: {line.strip()}")
        else:
            warn("No hay procesos de servidor Java activos.")

    # Mostrar info de conexión
    print()
    for inst in cfg.get("java_instances", []):
        ip = inst.get("connect_ip", "?")
        ok(f"Java  → {ip}:{inst.get('port', 25565)}")
    for inst in cfg.get("bedrock_instances", []):
        ok(f"Bedrock → puerto {inst.get('port', 19132)} UDP")
    return 0

def run_backup() -> int:
    title("Creando backup")
    sh = ROOT / "backup.sh"
    if sh.exists():
        return subprocess.call(["bash", str(sh)])
    err("backup.sh no encontrado. Ejecuta el asistente primero.")
    return 1

def run_logs() -> int:
    cfg = load_config()
    persistence = cfg.get("persistence", "manual")
    title("Logs de servidores")

    if persistence == "systemd":
        units = list(SYSTEMD.glob("*.service"))
        if units:
            unit = units[0]
            info(f"Mostrando logs de {unit.stem} (Ctrl+C para salir)...")
            return subprocess.call(["journalctl", "-u", unit.stem, "-f", "--no-pager"])

    # Buscar logs directamente
    log_files = list(SERVERS.rglob("logs/latest.log"))
    if log_files:
        lf = log_files[0]
        info(f"Mostrando: {lf}  (Ctrl+C para salir)")
        return subprocess.call(["tail", "-f", str(lf)])

    err("No se encontraron logs. ¿El servidor está corriendo?")
    return 1

def run_validate() -> int:
    title("Validando instalación")
    all_ok = True
    # Archivos requeridos
    required = [
        (CONFIG, "Configuración (config.json)"),
        (ROOT / ".gitignore", ".gitignore"),
        (ROOT / "README.md", "README.md"),
    ]

    for p, desc in required:
        rel = p.relative_to(ROOT)
        if not p.exists():
            err(f"FALTANTE: {rel}  — {desc}")
            all_ok = False
        else:
            # Comprobación ligera de README
            if rel.name == "README.md":
                txt = p.read_text(errors="ignore")
                if "Auralix" not in txt:
                    warn(f"README.md parece incompleto ({rel})")
                else:
                    ok(f"OK: {rel}")
            else:
                ok(f"OK: {rel}")

    # backup script (either shell or powershell) in bin/
    bsh = ROOT / "bin" / "backup.sh"
    bps = ROOT / "bin" / "backup.ps1"
    if bsh.exists() or bps.exists():
        ok("OK: bin/backup script encontrado")
    else:
        err("FALTANTE: bin/backup.sh o bin/backup.ps1")
        all_ok = False
    

    print()
    title("Sintaxis Python")
    try:
        py_compile.compile(str(Path(__file__)), doraise=True)
        ok("script — sintaxis válida")
    except Exception as e:
        err(f"script — error de sintaxis: {e}")
        all_ok = False

    print()
    title("Servidores instalados")
    if SERVERS.exists():
        jars = list(SERVERS.rglob("server.jar"))
        if jars:
            for j in jars:
                size = j.stat().st_size // 1048576
                ok(f"{j.parent.relative_to(ROOT)}  ({size} MB)")
        else:
            warn("No hay server.jar instalados aún.")
    else:
        warn("Directorio servers/ no existe todavía.")

    print()
    title("Estado del sistema")
    java_ver, _ = detect_java()
    if java_ver:
        ok(f"Java: {java_ver}")
    else:
        err("Java no detectado.")
        all_ok = False

    pub_ip = get_public_ip()
    ok(f"IP pública: {pub_ip}")
    ok(f"IP local:   {get_local_ip()}")

    print()
    if all_ok:
        ok("RESULTADO FINAL: Todo correcto ✔")
    else:
        err("RESULTADO FINAL: Hay errores — revísalos arriba.")
    return 0 if all_ok else 2

def run_delete() -> int:
    """Elimina un servidor instalado: para el servicio, borra archivos y actualiza config."""
    if not is_root():
        err("Necesitas ejecutar como root: sudo python3 auralix.py delete")
        return 1

    title("Eliminar servidor")

    marker  = "# ── Generado por el instalador v3.0 ──"
    sys_dir = Path("/etc/systemd/system")

    # Detectar servidores instalados desde units generadas por el instalador
    candidates: list[Path] = []
    for d in (SYSTEMD, sys_dir):
        if d.exists():
            for f in d.glob("*.service"):
                try:
                    if marker in f.read_text(encoding="utf-8", errors="ignore"):
                        candidates.append(f)
                except Exception:
                    pass

    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        if c.name not in seen:
            seen.add(c.name)
            unique.append(c)

    # Además, detectar directorios en servers/ sin unit asociada
    orphan_dirs: list[Path] = []
    if SERVERS.exists():
        known_stems = {u.stem for u in unique}
        for d in sorted(SERVERS.iterdir()):
            if d.is_dir() and d.name not in known_stems:
                orphan_dirs.append(d)

    if not unique and not orphan_dirs:
        warn("No se encontraron servidores instalados.")
        return 0

    # Construir opciones para el menú
    choices: list[str] = []
    for u in unique:
        content = u.read_text(encoding="utf-8", errors="ignore")
        wdir    = re.search(r'^WorkingDirectory=(.+)$', content, re.MULTILINE)
        label   = wdir.group(1).strip() if wdir else str(u.stem)
        choices.append(f"{u.stem}  [{label}]")
    for d in orphan_dirs:
        choices.append(f"{d.name}  [sin servicio]")
    choices.append("Cancelar")

    sel = ask_choice("Servidor a eliminar", choices, choices[-1])
    if sel == "Cancelar":
        info("Operación cancelada.")
        return 0

    idx = choices.index(sel)

    # Resolver qué tenemos: unit o solo directorio
    is_unit   = idx < len(unique)
    unit_file = unique[idx] if is_unit else None
    server_dir: Path | None = None

    if unit_file:
        content   = unit_file.read_text(encoding="utf-8", errors="ignore")
        wdir_m    = re.search(r'^WorkingDirectory=(.+)$', content, re.MULTILINE)
        server_dir = Path(wdir_m.group(1).strip()) if wdir_m else None
    else:
        server_dir = orphan_dirs[idx - len(unique)]

    # Confirmación
    sep()
    if unit_file:
        warn(f"Se eliminará el servicio:  {unit_file.stem}")
    if server_dir and server_dir.exists():
        warn(f"Se borrará el directorio:  {server_dir}")
    sep()
    try:
        confirm = input("  Escribe el nombre del servidor para confirmar: ").strip()
    except (EOFError, KeyboardInterrupt):
        return 0
    expected = unit_file.stem if unit_file else (server_dir.name if server_dir else "")
    if confirm != expected:
        err("Nombre incorrecto. Operación cancelada.")
        return 1

    # 1. Detener y deshabilitar el servicio
    if unit_file:
        stem = unit_file.stem
        for cmd in ("stop", "disable"):
            try:
                subprocess.check_call(["systemctl", cmd, stem],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok(f"systemctl {cmd} {stem}")
            except Exception as e:
                warn(f"systemctl {cmd} {stem}: {e}")

        # 2. Eliminar unit de /etc/systemd/system/
        sys_unit = sys_dir / unit_file.name
        for p in (sys_unit, SYSTEMD / unit_file.name):
            try:
                if p.exists():
                    p.unlink()
                    ok(f"Eliminado: {p}")
            except Exception as e:
                warn(f"No se pudo borrar {p}: {e}")

        try:
            subprocess.check_call(["systemctl", "daemon-reload"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok("daemon-reload ejecutado.")
        except Exception as e:
            warn(f"daemon-reload: {e}")

    # 3. Borrar directorio del servidor
    if server_dir and server_dir.exists():
        try:
            shutil.rmtree(server_dir)
            ok(f"Directorio eliminado: {server_dir}")
        except Exception as e:
            err(f"No se pudo borrar {server_dir}: {e}")
            return 1

    # 4. Actualizar config.json
    if CONFIG.exists() and unit_file:
        try:
            cfg = json.loads(CONFIG.read_text())
            stem = unit_file.stem
            server_name = cfg.get("server_name", "")
            # Intentar remover la instancia Java correspondiente
            ji = cfg.get("java_instances", [])
            bi = cfg.get("bedrock_instances", [])
            new_ji: list[dict] = []
            for n, inst in enumerate(ji, 1):
                label = f"{server_name}-{inst.get('engine','java')}-{n}"
                if label != stem:
                    new_ji.append(inst)
            cfg["java_instances"] = new_ji
            # Bedrock
            new_bi: list[dict] = []
            for n, inst in enumerate(bi, 1):
                blabel = f"{server_name}-bedrock-{n}"
                if blabel != stem:
                    new_bi.append(inst)
            cfg["bedrock_instances"] = new_bi
            CONFIG.write_text(json.dumps(cfg, indent=4, ensure_ascii=False))
            ok("config.json actualizado.")
        except Exception as e:
            warn(f"No se pudo actualizar config.json: {e}")

    ok(f"Servidor '{expected}' eliminado correctamente.")
    return 0


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        prog="script",
        description="Minecraft Server Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Ejemplos:
              sudo python3 <script>           # Asistente completo
              sudo python3 <script> start     # Iniciar servidores
              sudo python3 <script> stop      # Detener servidores
              sudo python3 <script> status    # Estado
              sudo python3 <script> backup    # Backup
              sudo python3 <script> logs      # Ver logs
              sudo python3 <script> validate  # Verificar instalación
        """)
    )
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("start",    help="Iniciar todos los servidores")
    sub.add_parser("stop",     help="Detener todos los servidores")
    sub.add_parser("status",   help="Ver estado de los servidores")
    sub.add_parser("backup",   help="Crear backup")
    sub.add_parser("logs",     help="Ver logs en tiempo real")
    sub.add_parser("validate", help="Verificar instalación")
    sub.add_parser("test",     help="Ejecutar tests unitarios")
    sub.add_parser("repair",   help="Reparar units systemd generadas (permisos, ProtectHome)")
    sub.add_parser("delete",   help="Eliminar un servidor instalado")

    args = p.parse_args()

    try:
        if   args.cmd is None:     sys.exit(run_wizard())
        elif args.cmd == "start":  sys.exit(run_start())
        elif args.cmd == "stop":   sys.exit(run_stop())
        elif args.cmd == "status": sys.exit(run_status())
        elif args.cmd == "backup": sys.exit(run_backup())
        elif args.cmd == "logs":   sys.exit(run_logs())
        elif args.cmd == "validate": sys.exit(run_validate())
        elif args.cmd == "repair": sys.exit(repair_systemd_units())
        elif args.cmd == "delete": sys.exit(run_delete())
        elif args.cmd == "test":
            sys.exit(subprocess.call(
                [sys.executable, "-m", "unittest", "discover", "-s", str(TESTS)]
            ))
    except KeyboardInterrupt:
        print("\n\n  Interrumpido por el usuario.")
        sys.exit(130)

if __name__ == "__main__":
    main()