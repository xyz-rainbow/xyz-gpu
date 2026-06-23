import os
import sys
import json
import socket
import subprocess
import time
import locale

# Asegurar que el directorio de trabajo es el del propio script
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir:
    os.chdir(script_dir)

# Habilitar soporte ANSI en Windows de forma nativa
if os.name == 'nt':
    os.system('')

# Paleta Estética Cyberpunk / RAINBOWTECHNOLOGY
C_LIME = "\033[38;5;118m"      # #bfffa6-ish
C_PINK = "\033[38;5;207m"      # #ffb1de-ish
C_CYAN = "\033[38;5;81m"       # #a6e7ff-ish
C_PURPLE = "\033[38;5;141m"     # #e9bbff-ish
C_ORANGE = "\033[38;5;202m"     # Neon Orange
C_RED = "\033[38;5;196m"        # Fire Red
C_RESET = "\033[0m"
C_BOLD = "\033[1m"

STATE_FILE = "cluster_state.json"

T = {
    "es": {
        "title": "PUENTE USB ADB / CLÚSTER DE MÓVILES",
        "desc": "Conecta tus teléfonos por USB en el portátil y expónlos al resto de nodos.",
        "opt_local": "Modo Local (Portátil): Iniciar Servidor ADB en red + Forward local",
        "opt_remote": "Modo Remoto (Torre / Otros): Conectar a Servidor ADB del portátil",
        "opt_list": "Listar reenvíos actuales (Adb Forwards)",
        "opt_clear": "Limpiar todos los reenvíos de puertos",
        "opt_exit": "Salir al menú anterior / Salir",
        "select_option": "Selecciona una opción: ",
        "press_enter": "Presiona Enter para continuar...",
        "checking_adb": "Verificando ADB en el sistema...",
        "adb_ok": "ADB detectado en el PATH.",
        "adb_fail": "ADB no detectado. Instálalo o agrégalo al PATH (ej. Platform Tools).",
        "local_host_running": "Iniciando servidor local ADB escuchando en toda la red (0.0.0.0:5037)...",
        "local_host_warn": "Asegúrate de permitir las conexiones en el Firewall si se solicita.",
        "devices_found": "Dispositivos detectados:",
        "no_devices": "No se detectaron dispositivos móviles conectados por USB.",
        "forwarding_device": "Reenviando puerto local {local_port} al puerto {target_port} en dispositivo {serial}...",
        "success_forward": "Reenvío completado con éxito.",
        "err_forward": "Error al configurar el reenvío para el dispositivo {serial}.",
        "enter_laptop_ip": "Introduce la dirección IP del portátil (donde están conectados los móviles): ",
        "connecting_remote": "Conectando al servidor ADB remoto en {ip}:5037...",
        "remote_success": "Conectado al portátil. Obteniendo dispositivos...",
        "remote_fail": "Error de conexión con el servidor ADB en el portátil. Revisa que el servidor local esté corriendo.",
        "clearing_forwards": "Limpiando todos los reenvíos de puertos...",
        "forwards_cleared": "Todos los reenvíos se han limpiado correctamente.",
        "current_forwards": "Reenvíos de puertos activos:",
        "target_port_prompt": "Introduce el puerto del servidor LLM en el móvil (por defecto 8080): ",
        "laptop_ip_help": "Nodos registrados en el clúster (detectados automáticamente):",
        "farm_disabled_warning": "La granja de móviles está desactivada en los ajustes del sistema. Los reenvíos no se aplicarán.",
        "farm_zero_nodes": "El número máximo de nodos móviles está configurado en 0 o desactivado. No se reenviará ningún puerto.",
        "farm_max_nodes_warn": "Se detectaron {total} móviles conectados, pero la granja de móviles está limitada a un máximo de {max} nodos en los ajustes."
    },
    "en": {
        "title": "USB ADB BRIDGE / MOBILE CLUSTER",
        "desc": "Connect your phones via USB on the laptop and expose them to other nodes.",
        "opt_local": "Local Mode (Laptop): Start ADB Server on network + Local forward",
        "opt_remote": "Remote Mode (Torre / Others): Connect to Laptop's ADB Server",
        "opt_list": "List active port forwards (Adb Forwards)",
        "opt_clear": "Clear all port forwards",
        "opt_exit": "Back to main menu / Exit",
        "select_option": "Select an option: ",
        "press_enter": "Press Enter to continue...",
        "checking_adb": "Verifying ADB on the system...",
        "adb_ok": "ADB detected in PATH.",
        "adb_fail": "ADB not detected. Please install it or add it to PATH (Platform Tools).",
        "local_host_running": "Starting local ADB server listening on all network interfaces (0.0.0.0:5037)...",
        "local_host_warn": "Please ensure you allow connections in your Firewall if prompted.",
        "devices_found": "Devices detected:",
        "no_devices": "No mobile devices detected via USB.",
        "forwarding_device": "Forwarding local port {local_port} to port {target_port} on device {serial}...",
        "success_forward": "Forward configured successfully.",
        "err_forward": "Error configuring forward for device {serial}.",
        "enter_laptop_ip": "Enter the laptop's IP address (where phones are physically connected): ",
        "connecting_remote": "Connecting to remote ADB server at {ip}:5037...",
        "remote_success": "Connected to laptop. Querying devices...",
        "remote_fail": "Connection error to the laptop's ADB server. Verify it is running.",
        "clearing_forwards": "Clearing all port forwards...",
        "forwards_cleared": "All port forwards have been cleared.",
        "current_forwards": "Active port forwards:",
        "target_port_prompt": "Enter the LLM server port on the phone (default 8080): ",
        "laptop_ip_help": "Registered nodes in cluster (auto-detected):",
        "farm_disabled_warning": "The mobile farm is disabled in the system settings. Port forwards will not be applied.",
        "farm_zero_nodes": "The maximum number of mobile nodes is set to 0 or disabled. No ports will be forwarded.",
        "farm_max_nodes_warn": "Detected {total} connected mobile phones, but the mobile farm is limited to a maximum of {max} nodes in the settings."
    }
}

def detect_system_language():
    if os.name == 'nt':
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lcid:
                name = locale.windows_locale.get(lcid, "")
                if name:
                    lang = name.split('_')[0].lower()
                    if lang in ['es', 'en']:
                        return lang
        except Exception:
            pass
    try:
        lang_code, _ = locale.getdefaultlocale()
        if lang_code:
            lang = lang_code.split('_')[0].lower()
            if lang in ['es', 'en']:
                return lang
    except Exception:
        pass
    return "en"

def load_lang():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("language", detect_system_language())
        except Exception:
            pass
    return detect_system_language()

def get_registered_nodes():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                return state.get("registered_nodes", {})
        except Exception:
            pass
    return {}

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{C_RED}  ██╗  ██╗ ██╗   ██╗ ███████╗            ██████╗  ██████╗  ██╗ ██████╗   ██████╗  ███████╗ {C_RESET}")
    print(f"{C_ORANGE}  ╚██╗██╔╝ ╚██╗ ██╔╝ ╚══███╔╝            ██╔══██╗ ██╔══██╗ ██║ ██╔══██╗ ██╔════╝  ██╔════╝ {C_RESET}")
    print(f"{C_LIME}   ╚███╔╝   ╚████╔╝     ███╔╝  ████████╗ ██████╔╝ ██████╔╝ ██║ ██║  ██║ ██║  ███╗ █████╗   {C_RESET}")
    print(f"{C_CYAN}   ██╔██╗    ╚██╔╝     ███╔╝   ╚═══════╝ ██╔══██╗ ██╔══██╗ ██║ ██║  ██║ ██║   ██║ ██╔══╝   {C_RESET}")
    print(f"{C_PURPLE}  ██╔╝ ██╗    ██║     ███████╗           ██████╔╝ ██║  ██║ ██║ ██████╔╝ ╚██████╔╝ ███████╗ {C_RESET}")
    print(f"{C_PINK}  ╚═╝  ╚═╝    ╚═╝     ╚══════╝           ╚══════╝  ╚═╝  ╚═╝ ╚═╝ ╚═════╝   ╚═════╝  ╚══════╝ {C_RESET}")
    print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")

def check_adb_installed(lang):
    try:
        subprocess.run(["adb", "version"], capture_output=True, check=True)
        return True
    except Exception:
        print(f"\n{C_PINK}❌ {T[lang]['adb_fail']}{C_RESET}")
        return False

def get_devices(adb_host=None):
    cmd = ["adb"]
    if adb_host:
        cmd.extend(["-H", adb_host])
    cmd.append("devices")
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = res.stdout.strip().splitlines()
        devices = []
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
        return devices
    except Exception:
        return []

def run_adb_command(args, adb_host=None):
    cmd = ["adb"]
    if adb_host:
        cmd.extend(["-H", adb_host])
    cmd.extend(args)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, res.stdout
    except Exception as e:
        return False, str(e)

def main():
    lang = load_lang()
    print_banner()
    
    if not check_adb_installed(lang):
        input(f"\n{T[lang]['press_enter']}")
        return

    while True:
        lang = load_lang()
        print_banner()
        print(f" {C_BOLD}{T[lang]['title']}{C_RESET}")
        print(f" {C_CYAN}{T[lang]['desc']}{C_RESET}\n")
        
        print(f"  {C_LIME}[1]{C_RESET} {T[lang]['opt_local']}")
        print(f"  {C_LIME}[2]{C_RESET} {T[lang]['opt_remote']}")
        print(f"  {C_LIME}[3]{C_RESET} {T[lang]['opt_list']}")
        print(f"  {C_LIME}[4]{C_RESET} {T[lang]['opt_clear']}")
        print(f"  {C_LIME}[5]{C_RESET} {T[lang]['opt_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        opc = input(f" {C_BOLD}{T[lang]['select_option']}{C_RESET}").strip()
        
        if opc == "1":
            # Modo Local (Portátil)
            print(f"\n⚡ {T[lang]['local_host_running']}")
            print(f"⚠️  {T[lang]['local_host_warn']}")
            
            # Detener cualquier servidor existente
            subprocess.run(["adb", "kill-server"], capture_output=True)
            
            # Iniciar servidor ADB expuesto
            try:
                # Usamos subprocess.Popen para levantarlo sin bloquear
                subprocess.Popen(["adb", "-a", "nodaemon", "server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            except Exception as e:
                print(f"{C_PINK}Error starting adb server: {e}{C_RESET}")
            
            # Consultar dispositivos
            devices = get_devices()
            if not devices:
                print(f"\n{C_PINK}⚠️  {T[lang]['no_devices']}{C_RESET}")
            else:
                print(f"\n📱 {T[lang]['devices_found']}")
                for idx, serial in enumerate(devices, 1):
                    print(f"  [{idx}] {C_LIME}{serial}{C_RESET}")
                
                target_port = input(f"\n{T[lang]['target_port_prompt']}").strip()
                if not target_port:
                    target_port = 8080
                else:
                    target_port = int(target_port)
                
                # Configurar reenvío local
                # Cargar configuración dinámica de la granja
                state = {}
                if os.path.exists(STATE_FILE):
                    try:
                        with open(STATE_FILE, "r", encoding="utf-8") as f:
                            state = json.load(f)
                    except Exception:
                        pass
                
                farm_enabled = state.get("mobile_farm_enabled", False)
                try:
                    farm_nodes = int(state.get("mobile_farm_nodes", "7"))
                except ValueError:
                    farm_nodes = 7
                try:
                    start_port = int(state.get("mobile_farm_start_port", "50051"))
                except ValueError:
                    start_port = 50051

                if not farm_enabled:
                    print(f"\n{C_ORANGE}⚠️  [WARN] {T[lang]['farm_disabled_warning']}{C_RESET}")
                
                if farm_nodes == 0 or not farm_enabled:
                    print(f"\n{C_PINK}⚠️  [INFO] {T[lang]['farm_zero_nodes']}{C_RESET}")
                else:
                    active_devices = devices[:farm_nodes]
                    if len(devices) > farm_nodes:
                        print(f"\n{C_ORANGE}⚠️  [WARN] {T[lang]['farm_max_nodes_warn'].format(max=farm_nodes, total=len(devices))}{C_RESET}")
                    
                    for idx, serial in enumerate(active_devices):
                        local_port = start_port + idx
                        print(f"  ├── " + T[lang]['forwarding_device'].format(local_port=local_port, target_port=target_port, serial=serial))
                        success, err = run_adb_command(["-s", serial, "forward", f"tcp:{local_port}", f"tcp:{target_port}"])
                        if success:
                            print(f"  └── {C_LIME}{T[lang]['success_forward']}{C_RESET}")
                        else:
                            print(f"  └── {C_PINK}{T[lang]['err_forward'].format(serial=serial)}: {err}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "2":
            # Modo Remoto (Torre / Otros)
            nodes = get_registered_nodes()
            print(f"\n🌐 {T[lang]['laptop_ip_help']}")
            for name, ip in nodes.items():
                print(f"  ├── {C_CYAN}{name}{C_RESET}: {ip}")
            
            laptop_ip = input(f"\n{T[lang]['enter_laptop_ip']}").strip()
            if not laptop_ip:
                # Buscar algún nodo que parezca laptop o el primero de la lista que no sea el local
                local_hostname = socket.gethostname().upper()
                fallback_ips = [ip for name, ip in nodes.items() if name != local_hostname]
                if fallback_ips:
                    laptop_ip = fallback_ips[0]
                    print(f"  (Auto-seleccionada IP registrada: {laptop_ip})")
                else:
                    print(f"{C_PINK}IP no válida.{C_RESET}")
                    time.sleep(1)
                    continue
            
            print(f"\n⚡ {T[lang]['connecting_remote'].format(ip=laptop_ip)}")
            devices = get_devices(adb_host=laptop_ip)
            
            if not devices:
                print(f"\n{C_PINK}❌ {T[lang]['remote_fail']}{C_RESET}")
            else:
                print(f"\n📱 {T[lang]['devices_found']} ({T[lang]['remote_success']})")
                for idx, serial in enumerate(devices, 1):
                    print(f"  [{idx}] {C_LIME}{serial}{C_RESET}")
                
                target_port = input(f"\n{T[lang]['target_port_prompt']}").strip()
                if not target_port:
                    target_port = 8080
                else:
                    target_port = int(target_port)
                
                # Configurar reenvío en este nodo apuntando al adb server del portátil
                # Cargar configuración dinámica de la granja
                state = {}
                if os.path.exists(STATE_FILE):
                    try:
                        with open(STATE_FILE, "r", encoding="utf-8") as f:
                            state = json.load(f)
                    except Exception:
                        pass
                
                farm_enabled = state.get("mobile_farm_enabled", False)
                try:
                    farm_nodes = int(state.get("mobile_farm_nodes", "7"))
                except ValueError:
                    farm_nodes = 7
                try:
                    start_port = int(state.get("mobile_farm_start_port", "50051"))
                except ValueError:
                    start_port = 50051

                # Limpiar reenvíos locales previos en este nodo
                subprocess.run(["adb", "forward", "--remove-all"], capture_output=True)

                if not farm_enabled:
                    print(f"\n{C_ORANGE}⚠️  [WARN] {T[lang]['farm_disabled_warning']}{C_RESET}")
                
                if farm_nodes == 0 or not farm_enabled:
                    print(f"\n{C_PINK}⚠️  [INFO] {T[lang]['farm_zero_nodes']}{C_RESET}")
                else:
                    active_devices = devices[:farm_nodes]
                    if len(devices) > farm_nodes:
                        print(f"\n{C_ORANGE}⚠️  [WARN] {T[lang]['farm_max_nodes_warn'].format(max=farm_nodes, total=len(devices))}{C_RESET}")
                    
                    for idx, serial in enumerate(active_devices):
                        local_port = start_port + idx
                        print(f"  ├── " + T[lang]['forwarding_device'].format(local_port=local_port, target_port=target_port, serial=serial))
                        # forward local port tcp:local_port to the target device connected on the remote ADB server
                        success, err = run_adb_command(["-s", serial, "forward", f"tcp:{local_port}", f"tcp:{target_port}"], adb_host=laptop_ip)
                        if success:
                            print(f"  └── {C_LIME}{T[lang]['success_forward']}{C_RESET}")
                        else:
                            print(f"  └── {C_PINK}{T[lang]['err_forward'].format(serial=serial)}: {err}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "3":
            # Listar reenvíos
            print(f"\n📊 {T[lang]['current_forwards']}")
            try:
                res = subprocess.run(["adb", "forward", "--list"], capture_output=True, text=True, check=True)
                if not res.stdout.strip():
                    print("  (Ninguno / None)")
                else:
                    for line in res.stdout.strip().splitlines():
                        print(f"  ├── {C_CYAN}{line}{C_RESET}")
            except Exception as e:
                print(f"  Error: {e}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "4":
            # Limpiar reenvíos
            print(f"\n🧹 {T[lang]['clearing_forwards']}")
            subprocess.run(["adb", "forward", "--remove-all"], capture_output=True)
            print(f"{C_LIME}{T[lang]['forwards_cleared']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "5":
            break

if __name__ == "__main__":
    main()
