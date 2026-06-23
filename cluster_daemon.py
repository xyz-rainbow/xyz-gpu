"""
cluster_daemon.py — XYZ-GPU Cluster Coordinator  v2
=====================================================
Mejoras v2:
  - Debounce de 2.5s en el reload de LiteLLM (evita reinicios en cascada)
  - Worker auto-reconexion si pierde contacto con el master
  - get_active_nodes() sin llamada HTTP cuando somos el master (in-process)
  - save_state no notifica durante el arranque inicial (flag _daemon_ready)
"""

import json
import os
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

# ─── Constantes ───────────────────────────────────────────────────────────────
COORDINATOR_PORT  = 5555
HEARTBEAT_TIMEOUT = 45    # segundos sin pulso → nodo eviccionado
HEARTBEAT_INTERVAL = 15   # frecuencia de heartbeat del worker
VLLM_PORT         = 8000
DEBOUNCE_DELAY    = 2.5   # segundos de espera antes de recargar LiteLLM
STATE_FILE        = "cluster_state.json"


# ─── Logger del daemon (no contamina el TUI) ─────────────────────────────────
_LOG_FILE = os.path.join(_script_dir, "cluster_daemon.log")

def _log(msg: str):
    """Escribe en el log del daemon en vez de stdout."""
    try:
        ts = time.strftime("%H:%M:%S")
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            # Limpiar códigos ANSI para el archivo de log
            import re as _re
            clean = _re.sub(r'\033\[[0-9;]*m', '', msg)
            f.write(f"[{ts}] {clean}\n")
    except Exception:
        pass
# ─── Estado en proceso ────────────────────────────────────────────────────────
_active_nodes: dict = {}
_lock          = threading.Lock()
_script_dir    = os.path.dirname(os.path.abspath(__file__))
_daemon_ready  = False   # True solo cuando el servidor HTTP está corriendo

# Debounce: timer que se cancela/reinicia en cada evento de cluster
_reload_timer: threading.Timer | None = None
_reload_lock  = threading.Lock()

# ─── ANSI ────────────────────────────────────────────────────────────────────
C_LIME   = "\033[38;5;118m"
C_PINK   = "\033[38;5;207m"
C_CYAN   = "\033[38;5;81m"
C_ORANGE = "\033[38;5;202m"
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"


# ══════════════════════════════════════════════════════════════════════════════
# Utilidades
# ══════════════════════════════════════════════════════════════════════════════

def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _get_gpu_count() -> int:
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        return len([l for l in res.stdout.strip().splitlines() if l.strip()])
    except Exception:
        return 0


def _load_state() -> dict:
    path = os.path.join(_script_dir, STATE_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state_daemon(state: dict):
    """Guardado interno del daemon — NO llama a notify (evita bucle)."""
    path = os.path.join(_script_dir, STATE_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Reescritura de config + Debounce del reload
# ══════════════════════════════════════════════════════════════════════════════

def _rewrite_litellm_config(nodes_snapshot: dict):
    state    = _load_state()
    mobile_enabled = state.get("mobile_farm_enabled", False)
    mobile_nodes   = int(state.get("mobile_farm_nodes", 7))
    mobile_port    = int(state.get("mobile_farm_start_port", 50051))
    local_ip       = _get_local_ip()

    lines = ["model_list:"]

    if not nodes_snapshot:
        lines += [
            "  - model_name: hybrid-model",
            "    litellm_params:",
            "      model: openai/vllm",
            "      api_base: http://localhost:8000/v1",
            '      api_key: "any-key"',
            "      rpm: 100",
            "      tpm: 100000",
            "",
        ]
    else:
        for hostname, info in nodes_snapshot.items():
            ip   = info.get("ip", "localhost")
            host = "localhost" if ip == local_ip else ip
            lines += [
                "  - model_name: hybrid-model",
                "    litellm_params:",
                f"      model: openai/vllm-{hostname.lower()}",
                f"      api_base: http://{host}:{VLLM_PORT}/v1",
                '      api_key: "any-key"',
                "      rpm: 100",
                "      tpm: 100000",
                "",
            ]

    if mobile_enabled and mobile_nodes > 0:
        for i in range(1, mobile_nodes + 1):
            port = mobile_port + i - 1
            lines += [
                "  - model_name: hybrid-model",
                "    litellm_params:",
                f"      model: openai/mobile-node-{i}",
                f"      api_base: http://localhost:{port}/v1",
                '      api_key: "any-key"',
                "      rpm: 15",
                "    fallback_value: true",
                "",
            ]

    lines += [
        "router_settings:",
        "  routing_strategy: least-busy",
        "  allowed_fails: 2",
        "  cooldown_time: 10",
        "",
    ]

    config_path = os.path.join(_script_dir, "litellm-config.yaml")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        n = len(nodes_snapshot)
        _log(f"[DAEMON] litellm-config.yaml → {n} nodo(s) GPU activo(s)")
    except Exception as e:
        _log(f"[DAEMON][ERR] config write failed: {e}")


def _do_reload_litellm():
    """Ejecuta el restart real — llamado desde el timer del debounce."""
    local_hostname = socket.gethostname().upper()
    env_file = os.path.join(_script_dir, f".env.{local_hostname}")
    if not os.path.exists(env_file):
        return
    try:
        subprocess.run(
            ["docker", "compose", "--env-file", env_file, "restart", "litellm"],
            capture_output=True, timeout=30
        )
        _log(f"[DAEMON]{C_RESET} {C_LIME}LiteLLM recargado.{C_RESET}")
    except Exception as e:
        _log(f"[DAEMON][ERR]{C_RESET} LiteLLM reload: {e}")


def _schedule_reload():
    """
    Debounce: cancela el timer existente y programa uno nuevo.
    Solo se ejecuta _do_reload_litellm() una vez que DEBOUNCE_DELAY
    segundos pasan sin nuevos eventos de cluster.
    """
    global _reload_timer
    with _reload_lock:
        if _reload_timer is not None:
            _reload_timer.cancel()
        _reload_timer = threading.Timer(DEBOUNCE_DELAY, _do_reload_litellm)
        _reload_timer.daemon = True
        _reload_timer.start()


def _on_cluster_change(nodes_snapshot: dict, reason: str):
    """Llamado en cada JOIN/LEAVE/EVICT — reescribe config y agenda reload."""
    _log(f"[DAEMON] {reason}")
    active_list = list(nodes_snapshot.keys())
    _log(f"  Nodos activos: {active_list or ['(ninguno)']}") 

    # Persistir en cluster_state.json
    state = _load_state()
    state["registered_nodes"] = {h: v["ip"] for h, v in nodes_snapshot.items()}
    state["active_nodes"] = {
        h: {"ip": v["ip"], "vram": v.get("vram", 0), "gpus": v.get("gpus", 0)}
        for h, v in nodes_snapshot.items()
    }
    _save_state_daemon(state)

    # Reescritura inmediata del YAML
    _rewrite_litellm_config(nodes_snapshot)

    # Reload de LiteLLM con debounce de 2.5s
    _schedule_reload()


# ══════════════════════════════════════════════════════════════════════════════
# HTTP Handler
# ══════════════════════════════════════════════════════════════════════════════

class _ClusterHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silenciar log de acceso

    def _respond(self, code: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # GET ─────────────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/nodes":
            with _lock:
                snap = {h: dict(v) for h, v in _active_nodes.items()}
            self._respond(200, {"nodes": snap})
        elif self.path == "/ping":
            self._respond(200, {"status": "master-alive"})
        else:
            self._respond(404, {"error": "not found"})

    # POST ────────────────────────────────────────────────────────────────────
    def do_POST(self):
        data     = self._read_json()
        hostname = data.get("hostname", "").upper()
        ip       = data.get("ip", self.client_address[0])

        if not hostname:
            self._respond(400, {"error": "hostname required"})
            return

        if self.path == "/register":
            changed = False
            with _lock:
                was_present = hostname in _active_nodes
                _active_nodes[hostname] = {
                    "ip":        ip,
                    "vram":      data.get("vram", 0.0),
                    "gpus":      data.get("gpus", 0),
                    "last_seen": time.time(),
                }
                changed  = not was_present
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            if changed:
                _on_cluster_change(snapshot, f"✅ {hostname} UNIDO ({ip})")
            else:
                # Re-register tras reconexión — actualizar config de todas formas
                _rewrite_litellm_config(snapshot)
            self._respond(200, {"status": "registered", "nodes": list(snapshot.keys())})

        elif self.path == "/heartbeat":
            with _lock:
                if hostname in _active_nodes:
                    _active_nodes[hostname]["last_seen"] = time.time()
                    self._respond(200, {"status": "ok"})
                else:
                    # Nodo desconocido manda heartbeat → pedirle que se re-registre
                    self._respond(404, {"status": "unknown", "action": "re-register"})

        elif self.path == "/unregister":
            changed = False
            with _lock:
                if hostname in _active_nodes:
                    del _active_nodes[hostname]
                    changed = True
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            if changed:
                _on_cluster_change(snapshot, f"🔴 {hostname} SALIÓ")
            self._respond(200, {"status": "unregistered"})

        elif self.path == "/settings":
            # Forzar reescritura + reload (cambio de configuración)
            with _lock:
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            _rewrite_litellm_config(snapshot)
            _schedule_reload()
            self._respond(200, {"status": "reloaded"})

        else:
            self._respond(404, {"error": "unknown endpoint"})


# ══════════════════════════════════════════════════════════════════════════════
# Watchdog (master) — evicta nodos sin pulso
# ══════════════════════════════════════════════════════════════════════════════

def _watchdog_loop():
    while True:
        time.sleep(5)  # Chequeo cada 5s para detección rápida
        now     = time.time()
        evicted = []
        with _lock:
            for hostname in list(_active_nodes.keys()):
                if now - _active_nodes[hostname]["last_seen"] > HEARTBEAT_TIMEOUT:
                    evicted.append(hostname)
            for h in evicted:
                del _active_nodes[h]
            snapshot = {h: dict(v) for h, v in _active_nodes.items()}
        if evicted:
            _on_cluster_change(snapshot, f"⏱️ Timeout eviccionado: {evicted}")


# ══════════════════════════════════════════════════════════════════════════════
# Worker: heartbeat con auto-reconexión
# ══════════════════════════════════════════════════════════════════════════════

def _worker_heartbeat_loop(master_ip: str, hostname: str, local_ip: str, gpus: int):
    """
    Loop de heartbeat del worker con auto-reconexion.
    Estado 'registered' como flag: si falla cualquier heartbeat → re-registro.
    Patron: intenta registrar hasta conseguirlo, luego manda pulsos.
    """
    import urllib.request

    url_reg = f"http://{master_ip}:{COORDINATOR_PORT}/register"
    url_hb  = f"http://{master_ip}:{COORDINATOR_PORT}/heartbeat"

    reg_payload = json.dumps({"hostname": hostname, "ip": local_ip,
                              "vram": 0.0, "gpus": gpus}).encode()
    hb_payload  = json.dumps({"hostname": hostname, "ip": local_ip}).encode()
    reg_headers = {"Content-Type": "application/json",
                   "Content-Length": str(len(reg_payload))}
    hb_headers  = {"Content-Type": "application/json",
                   "Content-Length": str(len(hb_payload))}

    registered = False

    while True:
        if not registered:
            # Intentar registro hasta conseguirlo
            try:
                req  = urllib.request.Request(url_reg, data=reg_payload,
                                              headers=reg_headers, method="POST")
                resp = urllib.request.urlopen(req, timeout=5)
                body = json.loads(resp.read())
                registered = True
                nodes = body.get('nodes', [])
                _log(f"[DAEMON] (Re)registrado en master {master_ip}")
                _log(f"  Nodos activos: {nodes}")
            except Exception:
                pass  # Master caido, reintentar en siguiente ciclo
        else:
            # Enviar heartbeat
            try:
                req  = urllib.request.Request(url_hb, data=hb_payload,
                                              headers=hb_headers, method="POST")
                resp = urllib.request.urlopen(req, timeout=5)
                body = json.loads(resp.read())
                # Si master no nos conoce (reinicio) → forzar re-registro
                if body.get("action") == "re-register" or resp.status == 404:
                    registered = False
            except Exception:
                # Conexion perdida → volver a estado no-registrado
                registered = False
                _log(f"[DAEMON] Master {master_ip} no responde, re-registrando...{C_RESET}")


        time.sleep(HEARTBEAT_INTERVAL)


# ══════════════════════════════════════════════════════════════════════════════
# API pública — llamada desde install_gpu.py
# ══════════════════════════════════════════════════════════════════════════════

_server_thread    = None
_heartbeat_thread = None


def start_master_daemon(local_ip: str):
    """Arranca el coordinador HTTP + watchdog en el nodo MASTER."""
    global _server_thread, _daemon_ready
    local_hostname = socket.gethostname().upper()
    gpus = _get_gpu_count()

    with _lock:
        _active_nodes[local_hostname] = {
            "ip": local_ip, "vram": 0.0, "gpus": gpus, "last_seen": time.time(),
        }

    # Reescribir config con solo el master (sin reload todavía — Docker acaba de arrancar)
    snapshot = {h: dict(v) for h, v in _active_nodes.items()}
    _rewrite_litellm_config(snapshot)

    try:
        server = HTTPServer(("0.0.0.0", COORDINATOR_PORT), _ClusterHandler)
    except OSError:
        _log(f"[DAEMON] Puerto {COORDINATOR_PORT} en uso — daemon omitido.{C_RESET}")
        return

    _server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    _server_thread.start()
    threading.Thread(target=_watchdog_loop, daemon=True).start()

    _daemon_ready = True
    _log(f"[DAEMON]{C_RESET} Coordinador master iniciado en :{COORDINATOR_PORT}")
    _log(f"  {C_BOLD}{local_hostname}{C_RESET} ({local_ip}) — {gpus} GPU(s)")


def stop_master_daemon():
    """Limpia el estado cuando el master apaga Docker."""
    global _server_thread, _daemon_ready
    with _lock:
        _active_nodes.clear()
    _daemon_ready  = False
    _server_thread = None


def register_as_worker(master_ip: str):
    """Registra este nodo como worker con el master y arranca el heartbeat."""
    import urllib.request
    global _heartbeat_thread

    local_hostname = socket.gethostname().upper()
    local_ip = _get_local_ip()
    gpus     = _get_gpu_count()

    payload = json.dumps({
        "hostname": local_hostname, "ip": local_ip,
        "vram": 0.0, "gpus": gpus,
    }).encode()
    headers = {"Content-Type": "application/json",
               "Content-Length": str(len(payload))}

    url = f"http://{master_ip}:{COORDINATOR_PORT}/register"
    try:
        req  = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        resp = urllib.request.urlopen(req, timeout=8)
        body = json.loads(resp.read())
        _log(f"[DAEMON] Registrado con master {master_ip}")
        _log(f"  Nodos en el cluster: {body.get('nodes', [])}")
    except Exception as e:
        _log(f"[DAEMON] No se pudo registrar en {master_ip}:{COORDINATOR_PORT}: {e}{C_RESET}")
        _log(f"  Asegúrate de que el master tiene Docker Up activo.")

    _heartbeat_thread = threading.Thread(
        target=_worker_heartbeat_loop,
        args=(master_ip, local_hostname, local_ip, gpus),
        daemon=True
    )
    _heartbeat_thread.start()


def unregister_as_worker(master_ip: str):
    """Notifica al master que este worker para."""
    import urllib.request
    local_hostname = socket.gethostname().upper()
    local_ip = _get_local_ip()
    payload  = json.dumps({"hostname": local_hostname, "ip": local_ip}).encode()
    headers  = {"Content-Type": "application/json",
                "Content-Length": str(len(payload))}
    url = f"http://{master_ip}:{COORDINATOR_PORT}/unregister"
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        urllib.request.urlopen(req, timeout=5)
        _log(f"[DAEMON]{C_RESET} Desregistrado del master {master_ip}")
    except Exception as e:
        _log(f"[DAEMON] No se pudo desregistrar: {e}{C_RESET}")


def notify_master_settings_changed(master_ip: str):
    """
    Notifica al master que hubo un cambio de configuración.
    Solo se ejecuta si el daemon está listo (evita notificaciones en el arranque).
    """
    if not _daemon_ready and master_ip in ("127.0.0.1", _get_local_ip()):
        return  # Somos el master pero el daemon no ha arrancado todavía
    import urllib.request
    url = f"http://{master_ip}:{COORDINATOR_PORT}/settings"
    try:
        req = urllib.request.Request(
            url, data=b"{}", method="POST",
            headers={"Content-Type": "application/json", "Content-Length": "2"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Master no disponible o somos worker sin master activo


def get_active_nodes(master_ip: str = "127.0.0.1") -> dict:
    """
    Devuelve los nodos activos.
    - Si somos el master (tenemos datos en proceso) → devuelve directo sin HTTP.
    - Si somos worker → consulta al master vía HTTP.
    """
    # Leer in-process primero (somos master o tenemos datos cacheados)
    with _lock:
        if _active_nodes:
            return {h: dict(v) for h, v in _active_nodes.items()}

    # Worker: consultar al master
    import urllib.request
    url = f"http://{master_ip}:{COORDINATOR_PORT}/nodes"
    try:
        resp = urllib.request.urlopen(url, timeout=2)
        return json.loads(resp.read()).get("nodes", {})
    except Exception:
        return {}


def is_master_daemon_running(master_ip: str = "127.0.0.1") -> bool:
    """Comprueba si hay un coordinador escuchando en master_ip:5555."""
    if _daemon_ready:
        return True  # Somos el master, no necesitamos check de red
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        ok = s.connect_ex((master_ip, COORDINATOR_PORT)) == 0
        s.close()
        return ok
    except Exception:
        return False

