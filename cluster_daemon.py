"""
cluster_daemon.py — XYZ-GPU Cluster Coordinator
================================================
Runs as a background thread on the MASTER node.
Workers POST /register and /heartbeat; master rewrites litellm-config.yaml
and reloads LiteLLM whenever the active-node set changes.

Ports:
  5555  — Cluster coordinator HTTP API
  8000  — vLLM OpenAI API (per node, host networking)
  4000  — LiteLLM unified gateway (master only)
  6379  — Ray GCS (master only)
"""

import json
import os
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

COORDINATOR_PORT = 5555
HEARTBEAT_TIMEOUT = 45
HEARTBEAT_INTERVAL = 15
VLLM_PORT = 8000
STATE_FILE = "cluster_state.json"

_active_nodes: dict = {}
_lock = threading.Lock()
_script_dir = os.path.dirname(os.path.abspath(__file__))

C_LIME   = "\033[38;5;118m"
C_PINK   = "\033[38;5;207m"
C_CYAN   = "\033[38;5;81m"
C_ORANGE = "\033[38;5;202m"
C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"


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


def _save_state(state: dict):
    path = os.path.join(_script_dir, STATE_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def _rewrite_litellm_config(nodes_snapshot: dict):
    state = _load_state()
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
        print(f"\n{C_CYAN}[DAEMON]{C_RESET} litellm-config.yaml rewritten ({len(nodes_snapshot)} GPU node(s) active)")
    except Exception as e:
        print(f"\n{C_PINK}[DAEMON][ERR]{C_RESET} Could not write litellm-config: {e}")


def _reload_litellm():
    local_hostname = socket.gethostname().upper()
    env_file = os.path.join(_script_dir, f".env.{local_hostname}")
    if not os.path.exists(env_file):
        return
    try:
        subprocess.run(
            ["docker", "compose", "--env-file", env_file, "restart", "litellm"],
            capture_output=True, timeout=30
        )
        print(f"{C_CYAN}[DAEMON]{C_RESET} LiteLLM container reloaded.")
    except Exception as e:
        print(f"{C_PINK}[DAEMON][ERR]{C_RESET} LiteLLM reload failed: {e}")


def _on_cluster_change(nodes_snapshot: dict, reason: str):
    print(f"\n{C_LIME}[DAEMON] Cluster change: {reason}{C_RESET}")
    print(f"  Active nodes: {list(nodes_snapshot.keys()) or ['(none)']}")

    state = _load_state()
    state["registered_nodes"] = {h: v["ip"] for h, v in nodes_snapshot.items()}
    state["active_nodes"]     = {h: {"ip": v["ip"], "vram": v.get("vram", 0), "gpus": v.get("gpus", 0)}
                                   for h, v in nodes_snapshot.items()}
    _save_state(state)
    _rewrite_litellm_config(nodes_snapshot)
    threading.Thread(target=_reload_litellm, daemon=True).start()


class _ClusterHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

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

    def do_GET(self):
        if self.path == "/nodes":
            with _lock:
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            self._respond(200, {"nodes": snapshot})
        elif self.path == "/ping":
            self._respond(200, {"status": "master-alive"})
        else:
            self._respond(404, {"error": "not found"})

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
                if not was_present:
                    changed = True
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            if changed:
                _on_cluster_change(snapshot, f"{hostname} JOINED ({ip})")
            self._respond(200, {"status": "registered", "nodes": list(snapshot.keys())})

        elif self.path == "/heartbeat":
            with _lock:
                if hostname in _active_nodes:
                    _active_nodes[hostname]["last_seen"] = time.time()
            self._respond(200, {"status": "ok"})

        elif self.path == "/unregister":
            changed = False
            with _lock:
                if hostname in _active_nodes:
                    del _active_nodes[hostname]
                    changed = True
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            if changed:
                _on_cluster_change(snapshot, f"{hostname} LEFT/STOPPED")
            self._respond(200, {"status": "unregistered"})

        elif self.path == "/settings":
            with _lock:
                snapshot = {h: dict(v) for h, v in _active_nodes.items()}
            _rewrite_litellm_config(snapshot)
            threading.Thread(target=_reload_litellm, daemon=True).start()
            self._respond(200, {"status": "reloaded"})

        else:
            self._respond(404, {"error": "unknown endpoint"})


def _watchdog_loop():
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        now = time.time()
        evicted = []
        with _lock:
            for hostname in list(_active_nodes.keys()):
                if now - _active_nodes[hostname]["last_seen"] > HEARTBEAT_TIMEOUT:
                    evicted.append(hostname)
            for h in evicted:
                del _active_nodes[h]
            snapshot = {h: dict(v) for h, v in _active_nodes.items()}
        if evicted:
            _on_cluster_change(snapshot, f"Timeout evicted: {evicted}")


def _worker_heartbeat_loop(master_ip: str, hostname: str, local_ip: str):
    import urllib.request
    url_hb  = f"http://{master_ip}:{COORDINATOR_PORT}/heartbeat"
    payload = json.dumps({"hostname": hostname, "ip": local_ip}).encode()
    headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
            req = urllib.request.Request(url_hb, data=payload, headers=headers, method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass


_server_thread = None
_heartbeat_thread = None


def start_master_daemon(local_ip: str):
    global _server_thread
    local_hostname = socket.gethostname().upper()
    gpus = _get_gpu_count()
    with _lock:
        _active_nodes[local_hostname] = {
            "ip": local_ip, "vram": 0.0, "gpus": gpus, "last_seen": time.time(),
        }
    snapshot = {h: dict(v) for h, v in _active_nodes.items()}
    _rewrite_litellm_config(snapshot)
    try:
        server = HTTPServer(("0.0.0.0", COORDINATOR_PORT), _ClusterHandler)
    except OSError:
        print(f"{C_ORANGE}[DAEMON] Port {COORDINATOR_PORT} already in use — daemon skipped.{C_RESET}")
        return
    _server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    _server_thread.start()
    threading.Thread(target=_watchdog_loop, daemon=True).start()
    print(f"\n{C_LIME}[DAEMON]{C_RESET} Master coordinator started on :{COORDINATOR_PORT}")
    print(f"  {C_BOLD}{local_hostname}{C_RESET} ({local_ip}) — {gpus} GPU(s)")


def stop_master_daemon():
    global _server_thread
    with _lock:
        _active_nodes.clear()
    _server_thread = None


def register_as_worker(master_ip: str):
    import urllib.request
    global _heartbeat_thread
    local_hostname = socket.gethostname().upper()
    local_ip = _get_local_ip()
    gpus = _get_gpu_count()
    payload = json.dumps({"hostname": local_hostname, "ip": local_ip, "vram": 0.0, "gpus": gpus}).encode()
    headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
    url = f"http://{master_ip}:{COORDINATOR_PORT}/register"
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        resp = urllib.request.urlopen(req, timeout=8)
        body = json.loads(resp.read())
        print(f"\n{C_LIME}[DAEMON]{C_RESET} Registered with master {master_ip}")
        print(f"  Cluster nodes: {body.get('nodes', [])}")
    except Exception as e:
        print(f"\n{C_ORANGE}[DAEMON] Could not register with master ({master_ip}:{COORDINATOR_PORT}): {e}{C_RESET}")
    _heartbeat_thread = threading.Thread(
        target=_worker_heartbeat_loop,
        args=(master_ip, local_hostname, local_ip),
        daemon=True
    )
    _heartbeat_thread.start()


def unregister_as_worker(master_ip: str):
    import urllib.request
    local_hostname = socket.gethostname().upper()
    local_ip = _get_local_ip()
    payload = json.dumps({"hostname": local_hostname, "ip": local_ip}).encode()
    headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
    url = f"http://{master_ip}:{COORDINATOR_PORT}/unregister"
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        urllib.request.urlopen(req, timeout=5)
        print(f"\n{C_LIME}[DAEMON]{C_RESET} Unregistered from master {master_ip}")
    except Exception as e:
        print(f"\n{C_ORANGE}[DAEMON] Could not unregister: {e}{C_RESET}")


def notify_master_settings_changed(master_ip: str):
    import urllib.request
    url = f"http://{master_ip}:{COORDINATOR_PORT}/settings"
    try:
        req = urllib.request.Request(url, data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json", "Content-Length": "2"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def get_active_nodes(master_ip: str = "127.0.0.1") -> dict:
    import urllib.request
    url = f"http://{master_ip}:{COORDINATOR_PORT}/nodes"
    try:
        resp = urllib.request.urlopen(url, timeout=3)
        return json.loads(resp.read()).get("nodes", {})
    except Exception:
        with _lock:
            if _active_nodes:
                return {h: dict(v) for h, v in _active_nodes.items()}
        return {}


def is_master_daemon_running(master_ip: str = "127.0.0.1") -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        result = s.connect_ex((master_ip, COORDINATOR_PORT))
        s.close()
        return result == 0
    except Exception:
        return False
