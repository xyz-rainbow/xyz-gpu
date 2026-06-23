import os
import sys
import json
import socket
import subprocess
import time
import locale

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

# Diccionario de Traducciones para soporte Español / Inglés
T = {
    "es": {
        "device": "EQUIPO ACTUAL",
        "config": "CONFIGURACIÓN DEL CLÚSTER EN EL ENTORNO",
        "assigned_master": "Nodo Master Asignado",
        "active_model": "Modelo Activo",
        "parallelism": "Paralelismo",
        "vram_allocation": "Asignación de VRAM",
        "cluster_status": "Estado del Clúster",
        "menu_settings": "Ajustes / Settings",
        "menu_start": "Desplegar / Iniciar Clúster (Docker Compose Up)",

        "menu_stop": "Apagar / Liberar GPUs (Docker Compose Down)",
        "menu_gpu": "Diagnóstico de GPU de NVIDIA (nvidia-smi)",
        "menu_instructions": "Instrucciones de Uso",
        "menu_lang": "Cambiar Idioma / Change Language (Español)",
        "menu_exit": "Salir",
        "select_option": "Selecciona una opción: ",
        "press_enter": "Presiona Enter para continuar...",
        "press_enter_menu": "Presiona Enter para volver al menú...",
        
        "settings_title": "MENÚ AJUSTES / SETTINGS",
        "settings_migrate": "Forzar y Migrar: Establecer ESTE equipo como MASTER",
        "settings_model": "Modificar Nombre del Modelo",
        "settings_parallel": "Modificar Tamaños de Paralelismo (Pipeline / Tensor)",
        "settings_manual_ip": "Configurar IP del Master Manualmente (Sin ruta compartida)",
        "settings_vram": "Modificar Límite de Asignación de VRAM (GPU Utilization)",
        "settings_defaults": "Restaurar Valores por Defecto (Valores de Fábrica)",
        "settings_ping": "Menú de Ping Diagnóstico (Nodos del Clúster)",
        "settings_back": "Volver al Menú Principal",
        "select_settings_option": "Selecciona una opción de Ajustes: ",
        "manual_ip_prompt": "Modificar IP del Master Manualmente",
        "manual_ip_input": "IP del Nodo Master",
        "manual_ip_success": "IP del Master configurada manualmente y registrada.",
        "vram_prompt": "Modificar Límite de VRAM (Valor decimal entre 0.1 y 1.0)",
        "vram_input": "Porcentaje de VRAM para vLLM",
        "vram_success": "Límite de asignación de VRAM actualizado con éxito.",


        
        "ping_title": "SUBMENÚ PING DIAGNÓSTICO (NODOS REGISTRADOS)",
        "ping_all": "Hacer Ping a TODOS los nodos en la lista",
        "ping_back": "Volver a Ajustes",
        "ping_exit": "Salir",
        "select_ping_option": "Selecciona una opción de Ping: ",
        "ping_master_label": "Probando conectividad con el Nodo Master asignado",
        "ping_sweep_label": "Iniciando barrido completo de ping a todos los nodos...",
        "ping_status_label": "Nodos activos en la red interna de Ray:",
        "ping_success": "Conexión establecida.",
        "ping_failed": "Tiempo de espera agotado. Revisa el cable/red local.",
        "ping_ray_advice": "Consejo: Arranca el clúster primero (Opción [2]) para registrar los workers en Ray.",
        
        "cfg_generating": "Generando archivo de entorno local",
        "cfg_launching": "Inicializando servicios con Docker Compose...",
        "cfg_stopping": "Apagando clúster de contenedores y liberando GPUs...",
        "cfg_success_stop": "Entorno limpio y GPU disponible de nuevo.",
        "cfg_success_start": "Contenedor lanzado con éxito en segundo plano.",
        "cfg_err_stop": "Falló al detener contenedores",
        "cfg_err_start": "Error al levantar Docker Compose",
        
        "monitor_title": "Diagnóstico dinámico de GPU (Actualizando cada 2s...)",
        "monitor_help": "Presiona [q] o [Enter] para regresar al menú principal.",
        "monitor_err": "No se pudo ejecutar nvidia-smi. Revisa los drivers.",
        
        "migrate_run": "Migrando la cabecera del clúster a este dispositivo...",
        "migrate_success": "Modificado. Ahora este PC es el nodo central.",
        "model_prompt": "Modificar Nombre del Modelo",
        "model_input": "Nombre del modelo",
        "model_success": "Modelo actualizado globalmente en el JSON.",
        "parallel_prompt": "Modificar Tamaños de Paralelismo",
        "parallel_success": "Paralelismo actualizado globalmente en el JSON.",
        "defaults_run": "Restaurando configuración del clúster a valores de fábrica...",
        "defaults_success": "Valores de fábrica restaurados correctamente.",
        "err_invalid": "Opción no válida.",
        "menu_models": "Gestión de Modelos (Descargar / Seleccionar)",
        "models_title": "SUBMENÚ DE GESTIÓN DE MODELOS",
        "models_list_popular": "Ver Modelos Populares y Descargados",
        "models_change_custom": "Cambiar y Registrar Nuevo Modelo (Hugging Face ID)",
        "models_predownload": "Pre-descargar Modelo Activo en la Cache",
        "models_back": "Volver al Menú Principal",
        "select_models_option": "Selecciona una opción de Modelos: ",
        "models_popular_title": "MODELOS POPULARES DISPONIBLES:",
        "models_cached_title": "MODELOS DETECTADOS EN TU CACHÉ LOCAL (~/.cache):",
        "models_cached_empty": "No se detectaron modelos en la caché local.",
        "models_download_start": "Descargando modelo en segundo plano a través de Docker (esto puede tardar)...",
        "models_download_success": "Modelo descargado con éxito.",
        "models_download_error": "Error al descargar el modelo. Verifica tu conexión e ID de repositorio.",
        "models_prompt_custom": "Introduce el ID de Hugging Face del modelo (ej: Qwen/Qwen2.5-VL-7B-Instruct): ",
        "menu_update": "Actualizar Orquestador (Git Pull desde GitHub)",
        "update_run": "Buscando actualizaciones en GitHub (git pull)...",
        "update_success": "Orquestador actualizado con éxito. Reinicia el asistente para aplicar los cambios.",
        "update_failed": "No se pudo actualizar. Asegúrate de tener Git instalado y configurado en esta carpeta."


    },
    "en": {
        "device": "CURRENT DEVICE",
        "config": "CLUSTER CONFIGURATION IN ENVIRONMENT",
        "assigned_master": "Assigned Master Node",
        "active_model": "Active Model",
        "parallelism": "Parallelism",
        "vram_allocation": "VRAM Allocation",
        "cluster_status": "Cluster Status",
        "menu_settings": "Settings / Ajustes",
        "menu_start": "Deploy / Start Cluster (Docker Compose Up)",

        "menu_stop": "Shutdown / Release GPUs (Docker Compose Down)",
        "menu_gpu": "NVIDIA GPU Diagnostics (nvidia-smi)",
        "menu_instructions": "Instructions of Use",
        "menu_lang": "Change Language / Cambiar Idioma (English)",
        "menu_exit": "Exit",
        "select_option": "Select an option: ",
        "press_enter": "Press Enter to continue...",
        "press_enter_menu": "Press Enter to return to the menu...",
        
        "settings_title": "SETTINGS MENU",
        "settings_migrate": "Force & Migrate: Set THIS device as MASTER",
        "settings_model": "Modify Model Name",
        "settings_parallel": "Modify Parallelism Sizes (Pipeline / Tensor)",
        "settings_manual_ip": "Configure Master IP Manually (No shared path)",
        "settings_vram": "Modify VRAM Allocation Limit (GPU Utilization)",
        "settings_defaults": "Restore Factory Defaults",
        "settings_ping": "Diagnostic Ping Menu (Cluster Nodes)",
        "settings_back": "Back to Main Menu",
        "select_settings_option": "Select a Settings option: ",
        "manual_ip_prompt": "Modify Master IP Manually",
        "manual_ip_input": "Master Node IP",
        "manual_ip_success": "Master IP manually updated and registered.",
        "vram_prompt": "Modify VRAM Limit (Decimal value between 0.1 and 1.0)",
        "vram_input": "VRAM percentage for vLLM",
        "vram_success": "VRAM allocation limit updated successfully.",


        
        "ping_title": "DIAGNOSTIC PING SUBMENU (REGISTERED NODES)",
        "ping_all": "Ping ALL listed nodes",
        "ping_back": "Back to Settings",
        "ping_exit": "Exit",
        "select_ping_option": "Select a Ping option: ",
        "ping_master_label": "Testing connectivity to the assigned Master node",
        "ping_sweep_label": "Starting complete ping sweep to all nodes...",
        "ping_status_label": "Active nodes in Ray's internal network:",
        "ping_success": "Connection established.",
        "ping_failed": "Request timed out. Check local cable or network config.",
        "ping_ray_advice": "Tip: Start the cluster first (Option [2]) to register workers in Ray.",
        
        "cfg_generating": "Generating local environment file",
        "cfg_launching": "Initializing services with Docker Compose...",
        "cfg_stopping": "Shutting down container cluster and releasing GPUs...",
        "cfg_success_stop": "Environment cleaned and GPU available again.",
        "cfg_success_start": "Container launched successfully in the background.",
        "cfg_err_stop": "Failed to stop containers",
        "cfg_err_start": "Error launching Docker Compose",
        
        "monitor_title": "Dynamic GPU Diagnostics (Updating every 2s...)",
        "monitor_help": "Press [q] or [Enter] to return to the main menu.",
        "monitor_err": "Could not execute nvidia-smi. Check GPU drivers.",
        
        "migrate_run": "Migrating cluster head node to this device...",
        "migrate_success": "Modified. This PC is now the central node.",
        "model_prompt": "Modify Model Name",
        "model_input": "Model name",
        "model_success": "Model updated globally in the JSON.",
        "parallel_prompt": "Modify Parallelism Sizes",
        "parallel_success": "Parallelism updated globally in the JSON.",
        "defaults_run": "Restoring cluster configuration to factory defaults...",
        "defaults_success": "Factory defaults successfully restored.",
        "err_invalid": "Invalid option.",
        "menu_models": "Model Management (Download / Select)",
        "models_title": "MODEL MANAGEMENT SUBMENU",
        "models_list_popular": "View Popular & Cached Models",
        "models_change_custom": "Change & Register New Model (Hugging Face ID)",
        "models_predownload": "Pre-download Active Model to Cache",
        "models_back": "Back to Main Menu",
        "select_models_option": "Select a Model option: ",
        "models_popular_title": "POPULAR MODELS AVAILABLE:",
        "models_cached_title": "MODELS DETECTED IN YOUR LOCAL CACHE (~/.cache):",
        "models_cached_empty": "No models detected in local cache.",
        "models_download_start": "Downloading model in background via Docker (this might take a while)...",
        "models_download_success": "Model downloaded successfully.",
        "models_download_error": "Error downloading model. Check connection and repository ID.",
        "models_prompt_custom": "Enter Hugging Face Model ID (e.g., Qwen/Qwen2.5-VL-7B-Instruct): ",
        "menu_update": "Update Orchestrator (Git Pull from GitHub)",
        "update_run": "Checking for updates on GitHub (git pull)...",
        "update_success": "Orchestrator successfully updated. Please restart the assistant to apply changes.",
        "update_failed": "Failed to update. Make sure Git is installed and configured in this folder."
    }


}

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def check_exit_key():
    if os.name == 'nt':
        try:
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in [b'q', b'Q', b'\x1b', b'\r']:
                    return True
        except ImportError:
            pass
    else:
        try:
            import select
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                ch = sys.stdin.read(1)
                if ch.lower() in ['q', '\n', '\x1b']:
                    return True
        except Exception:
            pass
    return False

def is_cluster_running():
    try:
        res = subprocess.run(
            ["docker", "ps", "--filter", "name=vllm-cluster-node", "--filter", "status=running", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=False
        )
        return "vllm-cluster-node" in res.stdout
    except Exception:
        return False

def ping_node(ip_or_host):
    param = '-n' if os.name == 'nt' else '-c'
    command = ['ping', param, '1', ip_or_host]
    try:
        res = subprocess.run(command, capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False

def detect_system_language():
    # Intenta detectar mediante ctypes en Windows
    if os.name == 'nt':
        try:
            import ctypes
            # GetUserDefaultUILanguage devuelve el LCID del idioma de la interfaz del usuario
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lcid:
                name = locale.windows_locale.get(lcid, "")
                if name:
                    lang = name.split('_')[0].lower()
                    if lang in ['es', 'en']:
                        return lang
        except Exception:
            pass

    # Intenta con locale estándar
    try:
        lang_code, encoding = locale.getdefaultlocale()
        if lang_code:
            lang = lang_code.split('_')[0].lower()
            if lang in ['es', 'en']:
                return lang
    except Exception:
        pass

    # Fallback para variables de entorno (sistemas Linux/WSL/Mac)
    try:
        for var in ['LANG', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE']:
            val = os.environ.get(var)
            if val:
                lang = val.split('_')[0].lower()
                if lang in ['es', 'en']:
                    return lang
    except Exception:
        pass

    return "en"  # Si no se puede detectar o no es español/inglés, por defecto inglés


def load_state():
    local_hostname = socket.gethostname().upper()
    local_ip = get_local_ip()
    
    if not os.path.exists(STATE_FILE):
        default_state = {
            "master_hostname": local_hostname,
            "master_ip": local_ip,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "pipeline_parallel_size": "2",
            "tensor_parallel_size": "1",
            "gpu_memory_utilization": "0.90",
            "language": detect_system_language(),
            "registered_nodes": {
                local_hostname: local_ip
            }
        }
        save_state(default_state)
        return default_state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            
        if "registered_nodes" not in state:
            state["registered_nodes"] = {}
        if "language" not in state:
            state["language"] = detect_system_language()
        if "gpu_memory_utilization" not in state:
            state["gpu_memory_utilization"] = "0.90"
            save_state(state)
            
        if state["registered_nodes"].get(local_hostname) != local_ip:
            state["registered_nodes"][local_hostname] = local_ip
            save_state(state)
            
        return state
    except Exception:
        return {
            "master_hostname": local_hostname,
            "master_ip": local_ip,
            "model_name": "Qwen/Qwen2.5-VL-7B-Instruct",
            "pipeline_parallel_size": "2",
            "tensor_parallel_size": "1",
            "gpu_memory_utilization": "0.90",
            "language": detect_system_language(),
            "registered_nodes": {
                local_hostname: local_ip
            }
        }

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"\n{C_PINK}[ERR] No se pudo guardar el archivo de estado central: {e}{C_RESET}")

def generate_env_file(hostname, role, master_ip, state):
    env_filename = f".env.{hostname}"
    try:
        with open(env_filename, "w", encoding="utf-8") as f:
            f.write(f"NODE_ROLE={role}\n")
            f.write(f"MASTER_IP={master_ip}\n")
            f.write(f"MODEL_NAME={state.get('model_name', 'Qwen/Qwen2.5-VL-7B-Instruct')}\n")
            f.write(f"PIPELINE_SIZE={state.get('pipeline_parallel_size', '2')}\n")
            f.write(f"TENSOR_SIZE={state.get('tensor_parallel_size', '1')}\n")
            f.write(f"GPU_MEM_LIMIT={state.get('gpu_memory_utilization', '0.90')}\n")
        return env_filename
    except Exception as e:
        print(f"\n{C_PINK}[ERR] Error al generar el archivo de entorno {env_filename}: {e}{C_RESET}")
        return None


def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{C_RED}  ██████╗  ██╗  ██╗ ██╗   ██╗ ███████╗             ██████╗  ██████╗  ██╗   ██╗ ██████╗ {C_RESET}")
    print(f"{C_ORANGE}  ██╔═══╝  ╚██╗██╔╝ ╚██╗ ██╔╝ ╚══███╔╝ █████████╗ ██╔════╝  ██╔══██╗ ██║   ██║ ╚═══██║ {C_RESET}")
    print(f"{C_LIME}  ██║       ╚███╔╝   ╚████╔╝     ███╔╝ ╚════════╝ ██║  ███╗ ██████╔╝ ██║   ██║     ██║ {C_RESET}")
    print(f"{C_CYAN}  ██║       ██╔██╗    ╚██╔╝     ███╔╝  █████████╗ ██║   ██║ ██╔═══╝  ██║   ██║     ██║ {C_RESET}")
    print(f"{C_PURPLE}  ██████╗  ██╔╝ ██╗    ██║     ███████╗           ╚██████╔╝ ██║      ╚██████╔╝ ██████║ {C_RESET}")
    print(f"{C_PINK}  ╚═════╝  ╚═╝  ╚═╝    ╚═╝     ╚══════╝            ╚═════╝  ╚═╝       ╚═════╝  ╚═════╝ {C_RESET}")
    print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")

def print_full_header(state, local_hostname, local_ip, role_label):
    print_banner()
    master_hostname = state.get("master_hostname", "").upper()
    master_ip = state.get("master_ip", "")
    lang = state.get("language", "es")
    
    # Determinar el estado ON/OFF del clúster
    if is_cluster_running():
        status_label = f"{C_BOLD}{C_LIME}ON{C_RESET}"
    else:
        status_label = f"{C_BOLD}{C_RED}OFF{C_RESET}"
        
    print(f" {C_BOLD}{T[lang]['device']}:{C_RESET} {C_ORANGE}{local_hostname}{C_RESET} ({local_ip}) -> {role_label}")
    print(f" {C_BOLD}{T[lang]['config']}:{C_RESET}")
    print(f"  ├── {C_BOLD}{T[lang]['assigned_master']}:{C_RESET} {C_RED}[{master_hostname}]{C_RESET} ({master_ip})")
    print(f"  ├── {T[lang]['active_model']}:        {C_LIME}[{state.get('model_name')}]{C_RESET}")
    print(f"  ├── {T[lang]['parallelism']}:          Pipeline: {state.get('pipeline_parallel_size')} | Tensor: {state.get('tensor_parallel_size')}")
    # Mostrar límite de asignación de VRAM
    vram_percent = int(float(state.get('gpu_memory_utilization', '0.90')) * 100)
    print(f"  ├── {T[lang]['vram_allocation']}:       {vram_percent}% ({state.get('gpu_memory_utilization', '0.90')})")
    print(f"  └── {C_BOLD}{T[lang]['cluster_status']}:   [ {status_label}{C_BOLD} ]{C_RESET}")
    print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")


def ping_menu(local_hostname, local_ip):
    while True:
        state = load_state()
        master_hostname = state.get("master_hostname", "").upper()
        lang = state.get("language", "es")
        
        if local_hostname == master_hostname:
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_BOLD}{T[lang]['ping_title']}:{C_RESET}")
        
        nodes = state.get("registered_nodes", {})
        node_list = sorted(list(nodes.items()))
        
        idx = 1
        for name, ip in node_list:
            node_type = f"{C_RED}[MASTER]{C_RESET}" if name == master_hostname else f"{C_CYAN}[WORKER]{C_RESET}"
            print(f"  {C_LIME}[{idx}]{C_RESET} Ping {T[lang]['ping_exit'].lower()} {node_type} {C_BOLD}{name}{C_RESET} ({ip})")
            idx += 1
            
        print(f"  {C_LIME}[A]{C_RESET} {T[lang]['ping_all']}")
        print(f"  {C_LIME}[V]{C_RESET} {T[lang]['ping_back']}")
        print(f"  {C_LIME}[S]{C_RESET} {T[lang]['ping_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        opc = input(f" {C_BOLD}{T[lang]['select_ping_option']}{C_RESET}").strip().upper()
        
        if opc == "V":
            break
        elif opc == "S":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)
        elif opc == "A":
            print(f"\n⚡ {C_BOLD}{C_CYAN}[PING]{C_RESET} {T[lang]['ping_sweep_label']}")
            for name, ip in node_list:
                node_type = f"{C_RED}[MASTER]{C_RESET}" if name == master_hostname else f"{C_CYAN}[WORKER]{C_RESET}"
                print(f"  ├── {name} {node_type} ({ip})... ", end="", flush=True)
                if ping_node(ip):
                    print(f"{C_LIME}[SUCCESS]{C_RESET}")
                else:
                    print(f"{C_PINK}[FAILED]{C_RESET}")
            
            if is_cluster_running():
                print(f"\n📊 {C_BOLD}{C_PURPLE}[RAY STATUS]{C_RESET} {T[lang]['ping_status_label']}")
                try:
                    res = subprocess.run(
                        ["docker", "exec", "vllm-cluster-node", "ray", "status"],
                        capture_output=True, text=True, timeout=5
                    )
                    if res.returncode == 0:
                        node_lines = [l for l in res.stdout.splitlines() if "Node:" in l or "Active Nodes" in l or "worker" in l.lower() or "head" in l.lower()]
                        for l in node_lines:
                            print(f"     {l}")
                    else:
                        print("     (Sin respuesta / No response)")
                except Exception:
                    pass
            input(f"\n{T[lang]['press_enter']}")
            
        else:
            try:
                sel = int(opc) - 1
                if 0 <= sel < len(node_list):
                    name, ip = node_list[sel]
                    node_type = f"{C_RED}[MASTER]{C_RESET}" if name == master_hostname else f"{C_CYAN}[WORKER]{C_RESET}"
                    print(f"\n⚡ {C_BOLD}{C_CYAN}[PING]{C_RESET} {T[lang]['ping_master_label']} {C_BOLD}{name}{C_RESET} ({ip})...")
                    if ping_node(ip):
                        print(f" {C_LIME}[SUCCESS] {T[lang]['ping_success']}{C_RESET}")
                    else:
                        print(f" {C_PINK}[ERROR] {T[lang]['ping_failed']}{C_RESET}")
                    input(f"\n{T[lang]['press_enter']}")
                else:
                    print(f"\n{C_PINK}[ERR] {T[lang]['err_invalid']}{C_RESET}")
                    time.sleep(1)
            except ValueError:
                print(f"\n{C_PINK}[ERR] {T[lang]['err_invalid']}{C_RESET}")
                time.sleep(1)

def settings_menu(local_hostname, local_ip):
    while True:
        state = load_state()
        master_hostname = state.get("master_hostname", "").upper()
        master_ip = state.get("master_ip", "")
        lang = state.get("language", "es")
        
        if local_hostname == master_hostname:
            current_role = "head"
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            current_role = "worker"
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_BOLD}{T[lang]['settings_title']}:{C_RESET}")
        print(f"  {C_LIME}[1]{C_RESET} {T[lang]['settings_migrate']}")
        print(f"  {C_LIME}[2]{C_RESET} {T[lang]['settings_model']}")
        print(f"  {C_LIME}[3]{C_RESET} {T[lang]['settings_parallel']}")
        print(f"  {C_LIME}[4]{C_RESET} {T[lang]['settings_manual_ip']}")
        print(f"  {C_LIME}[5]{C_RESET} {T[lang]['settings_vram']}")
        print(f"  {C_LIME}[6]{C_RESET} {T[lang]['settings_defaults']}")
        print(f"  {C_LIME}[7]{C_RESET} {T[lang]['settings_ping']}")
        print(f"  {C_LIME}[8]{C_RESET} {T[lang]['settings_back']}")
        print(f"  {C_LIME}[9]{C_RESET} {T[lang]['menu_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        sub_opc = input(f" {C_BOLD}{T[lang]['select_settings_option']}{C_RESET}").strip()
        
        if sub_opc == "1":
            print(f"\n🔄 {T[lang]['migrate_run']}")
            state["master_hostname"] = local_hostname
            state["master_ip"] = local_ip
            save_state(state)
            print(f"{C_LIME}[OK] {T[lang]['migrate_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "2":
            print(f"\n📝 {C_BOLD}{T[lang]['model_prompt']}:{C_RESET}")
            new_model = input(f" {T[lang]['model_input']} [{state.get('model_name')}]: ").strip()
            if new_model:
                state["model_name"] = new_model
                save_state(state)
                print(f"{C_LIME}[OK] {T[lang]['model_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "3":
            print(f"\n📝 {C_BOLD}{T[lang]['parallel_prompt']}:{C_RESET}")
            new_pipe = input(f" Pipeline Parallel Size [{state.get('pipeline_parallel_size')}]: ").strip()
            new_tensor = input(f" Tensor Parallel Size [{state.get('tensor_parallel_size')}]: ").strip()
            
            updated = False
            if new_pipe:
                state["pipeline_parallel_size"] = new_pipe
                updated = True
            if new_tensor:
                state["tensor_parallel_size"] = new_tensor
                updated = True
                
            if updated:
                save_state(state)
                print(f"{C_LIME}[OK] {T[lang]['parallel_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "4":
            print(f"\n📝 {C_BOLD}{T[lang]['manual_ip_prompt']}:{C_RESET}")
            entered_ip = input(f" {T[lang]['manual_ip_input']} [{state.get('master_ip')}]: ").strip()
            if entered_ip:
                state["master_ip"] = entered_ip
                state["master_hostname"] = "MANUAL-MASTER"
                if "registered_nodes" not in state:
                    state["registered_nodes"] = {}
                state["registered_nodes"]["MANUAL-MASTER"] = entered_ip
                save_state(state)
                print(f"{C_LIME}[OK] {T[lang]['manual_ip_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "5":
            print(f"\n📝 {C_BOLD}{T[lang]['vram_prompt']}:{C_RESET}")
            entered_vram = input(f" {T[lang]['vram_input']} [{state.get('gpu_memory_utilization', '0.90')}]: ").strip()
            if entered_vram:
                try:
                    val = float(entered_vram)
                    if 0.1 <= val <= 1.0:
                        state["gpu_memory_utilization"] = f"{val:.2f}"
                        save_state(state)
                        print(f"{C_LIME}[OK] {T[lang]['vram_success']}{C_RESET}")
                    else:
                        print(f"{C_PINK}[ERR] El valor debe estar entre 0.1 y 1.0 / Value must be between 0.1 and 1.0{C_RESET}")
                except ValueError:
                    print(f"{C_PINK}[ERR] Formato no válido / Invalid format{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "6":
            print(f"\n🔄 {T[lang]['defaults_run']}")
            state["master_hostname"] = local_hostname
            state["master_ip"] = local_ip
            state["model_name"] = "Qwen/Qwen2.5-VL-7B-Instruct"
            state["pipeline_parallel_size"] = "2"
            state["tensor_parallel_size"] = "1"
            state["gpu_memory_utilization"] = "0.90"
            save_state(state)
            print(f"{C_LIME}[SUCCESS] {T[lang]['defaults_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "7":
            ping_menu(local_hostname, local_ip)
        elif sub_opc == "8":
            break
        elif sub_opc == "9":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)



def get_downloaded_models():
    hf_hub = os.path.expanduser("~/.cache/huggingface/hub")
    downloaded = []
    if os.path.exists(hf_hub):
        try:
            for item in os.listdir(hf_hub):
                if item.startswith("models--"):
                    parts = item.split("--")[1:]
                    if parts:
                        model_name = "/".join(parts)
                        downloaded.append(model_name)
        except Exception:
            pass
    return downloaded


def models_menu(local_hostname, local_ip):
    popular_models = [
        "Qwen/Qwen2.5-VL-7B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "google/gemma-2-9b-it"
    ]
    
    while True:
        state = load_state()
        master_hostname = state.get("master_hostname", "").upper()
        lang = state.get("language", "es")
        
        if local_hostname == master_hostname:
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_BOLD}{T[lang]['models_title']}:{C_RESET}")
        print(f"  {C_LIME}[1]{C_RESET} {T[lang]['models_list_popular']}")
        print(f"  {C_LIME}[2]{C_RESET} {T[lang]['models_change_custom']}")
        print(f"  {C_LIME}[3]{C_RESET} {T[lang]['models_predownload']}")
        print(f"  {C_LIME}[4]{C_RESET} {T[lang]['models_back']}")
        print(f"  {C_LIME}[5]{C_RESET} {T[lang]['menu_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        opc = input(f" {C_BOLD}{T[lang]['select_models_option']}{C_RESET}").strip()
        
        if opc == "1":
            print(f"\n🔥 {C_BOLD}{T[lang]['models_popular_title']}{C_RESET}")
            for idx, m in enumerate(popular_models, 1):
                print(f"  [{idx}] {m}")
            
            print(f"\n📂 {C_BOLD}{T[lang]['models_cached_title']}{C_RESET}")
            cached = get_downloaded_models()
            clean_cached = [c for c in cached if c not in popular_models]
            
            if clean_cached:
                for idx, m in enumerate(clean_cached, len(popular_models) + 1):
                    print(f"  [{idx}] {C_LIME}{m}{C_RESET} [Caché]")
            else:
                if not cached:
                    print(f"  {T[lang]['models_cached_empty']}")
                else:
                    print(f"  (Todos los modelos de la caché ya son populares / All cached models are popular)")
                
            combined = popular_models + clean_cached
            sel = input(f"\nSelecciona un número para activar ese modelo (o Enter para cancelar): " if lang == "es" else f"\nSelect a number to activate that model (or Enter to cancel): ").strip()
            if sel:
                try:
                    num = int(sel) - 1
                    if 0 <= num < len(combined):
                        selected = combined[num]
                        state["model_name"] = selected
                        save_state(state)
                        print(f"\n{C_LIME}[OK] Modelo cambiado a: {selected}{C_RESET}")
                except ValueError:
                    pass
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "2":
            print(f"\n📝 {C_BOLD}{T[lang]['models_change_custom']}:{C_RESET}")
            new_model = input(f" {T[lang]['models_prompt_custom']}").strip()
            if new_model:
                state["model_name"] = new_model
                save_state(state)
                print(f"\n{C_LIME}[OK] {T[lang]['model_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "3":
            active_model = state.get("model_name", "Qwen/Qwen2.5-VL-7B-Instruct")
            print(f"\n📥 {T[lang]['models_download_start']}")
            print(f"📦 Modelo: {C_BOLD}{active_model}{C_RESET}\n")
            
            # Ejecutar docker para descargar el modelo de Hugging Face
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{os.path.expanduser('~')}/.cache/huggingface:/root/.cache/huggingface",
                "vllm/vllm-openai:v0.4.2",
                "python3", "-c", f"from huggingface_hub import snapshot_download; snapshot_download(repo_id='{active_model}')"
            ]
            try:
                # Mostrar salida a tiempo real
                res = subprocess.run(cmd)
                if res.returncode == 0:
                    print(f"\n{C_LIME}[SUCCESS] {T[lang]['models_download_success']}{C_RESET}")
                else:
                    print(f"\n{C_PINK}[ERROR] {T[lang]['models_download_error']}{C_RESET}")
            except Exception as e:
                print(f"\n{C_PINK}[ERROR] {T[lang]['models_download_error']}: {e}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "4":
            break
        elif opc == "5":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)


def main():

    while True:
        state = load_state()
        local_hostname = socket.gethostname().upper()
        local_ip = get_local_ip()
        
        master_hostname = state.get("master_hostname", "").upper()
        master_ip = state.get("master_ip", "")
        lang = state.get("language", "es")
        
        # Determinar rol dinámico basado en el archivo de estado centralizado
        if local_hostname == master_hostname:
            current_role = "head"
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            current_role = "worker"
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_LIME}[1]{C_RESET} {T[lang]['menu_settings']}")
        
        # Opción 2 Dinámica
        running = is_cluster_running()
        if running:
            print(f" {C_LIME}[2]{C_RESET} {T[lang]['menu_stop']}")
        else:
            print(f" {C_LIME}[2]{C_RESET} {T[lang]['menu_start']}")
            
        print(f" {C_LIME}[3]{C_RESET} {T[lang]['menu_models']}")
        print(f" {C_LIME}[4]{C_RESET} {T[lang]['menu_gpu']}")
        print(f" {C_LIME}[5]{C_RESET} {T[lang]['menu_instructions']}")
        
        print(f" {C_LIME}[6]{C_RESET} {T[lang]['menu_update']}")
        
        # Opción de Idioma Dinámica
        lang_str = "English" if lang == "es" else "Español"
        print(f" {C_LIME}[7]{C_RESET} {T[lang]['menu_lang']} ({lang_str})")
        print(f" {C_LIME}[8]{C_RESET} {T[lang]['menu_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")

        
        opc = input(f" {C_BOLD}{T[lang]['select_option']}{C_RESET}").strip()
        
        if opc == "1":
            settings_menu(local_hostname, local_ip)
            
        elif opc == "2":
            if running:
                print(f"\n🛑  {C_BOLD}{C_PINK}[DOCKER]{C_RESET} {T[lang]['cfg_stopping']}")
                env_file = f".env.{local_hostname}"
                if not os.path.exists(env_file):
                    generate_env_file(local_hostname, current_role, master_ip, state)
                try:
                    subprocess.run(["docker", "compose", "--env-file", env_file, "down"], check=True)
                    print(f"\n{C_LIME}[SUCCESS] {T[lang]['cfg_success_stop']}{C_RESET}")
                except Exception as e:
                    print(f"\n{C_PINK}[ERROR] {T[lang]['cfg_err_stop']}: {e}{C_RESET}")
            else:
                env_file = f".env.{local_hostname}"
                print(f"\n⚙️  {C_BOLD}{C_CYAN}[CONFIG]{C_RESET} {T[lang]['cfg_generating']} ({env_file})...")
                env_file = generate_env_file(local_hostname, current_role, master_ip, state)
                if not env_file:
                    input(f"\n{T[lang]['press_enter']}")
                    continue
                    
                print(f"🚀  {C_BOLD}{C_PURPLE}[DOCKER]{C_RESET} {T[lang]['cfg_launching']}")
                try:
                    subprocess.run(["docker", "compose", "--env-file", env_file, "up", "-d"], check=True)
                    print(f"\n{C_LIME}[SUCCESS] {T[lang]['cfg_success_start']}{C_RESET}")
                    if current_role == "head":
                        print(f"  ├── API Endpoint:     {C_CYAN}http://localhost:8000/v1{C_RESET}")
                        print(f"  └── Ray Dashboard:    {C_PURPLE}http://localhost:8265{C_RESET}")
                except Exception as e:
                    print(f"\n{C_PINK}[ERROR] {T[lang]['cfg_err_start']}: {e}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "3":
            models_menu(local_hostname, local_ip)
            
        elif opc == "4":
            print(f"\n🔍 Iniciando monitor dinámico de GPU..." if lang == "es" else f"\n🔍 Starting dynamic GPU monitor...")
            time.sleep(0.5)
            while True:
                state = load_state()
                print_full_header(state, local_hostname, local_ip, role_label)
                print(f" 🔍 {C_BOLD}{C_CYAN}[MONITOR]{C_RESET} {T[lang]['monitor_title']}")
                print(f" {T[lang]['monitor_help']}")
                print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
                
                try:
                    subprocess.run(["nvidia-smi"])
                except Exception:
                    print(f"\n{C_PINK}[ERROR] {T[lang]['monitor_err']}{C_RESET}")
                    input(f"\n{T[lang]['press_enter']}")
                    break
                    
                print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
                
                exited = False
                for _ in range(20):
                    if check_exit_key():
                        exited = True
                        break
                    time.sleep(0.1)
                
                if exited:
                    break
            
        elif opc == "5":
            if lang == "es":
                print(f"\n📝 {C_BOLD}INSTRUCCIONES DE USO DE XYZ-GPU:{C_RESET}")
                print("  1. Requisitos: Asegúrate de tener Docker Desktop con integración de WSL2 activo.")
                print("  2. Red Espejo: Verifica que la red 'mirrored' esté configurada en tu .wslconfig.")
                print("  3. Encendido del Clúster:")
                print(f"     - En el PC MASTER ({master_hostname}): Lanza la opción [2]. Levanta Ray y vLLM.")
                print("     - En el PC WORKER: Lanza la opción [2]. Se conectará automáticamente al Master.")
                print("  4. Diagnóstico de GPU en Vivo:")
                print("     - Lanza la opción [4] para ver el estado de la GPU en tiempo real de forma estática y")
                print("       dinámica con refresco de 2 segundos. Presiona 'q' o Enter para regresar al menú.")
                print("  5. Parámetros de Paralelismo (Ajustes):")
                print(f"     - {C_BOLD}Pipeline Parallelism (PP):{C_RESET} Divide las capas verticales del modelo en bloques.")
                print("       Por ejemplo, capas 1-16 en PC 1 y 17-32 en PC 2. Se comunican por red local al")
                print("       saltar de bloque. Es ideal para redes domésticas (debes ponerlo en 2).")
                print(f"     - {C_BOLD}Tensor Parallelism (TP):{C_RESET} Divide cada capa matemática individual (tensores)")
                print("       de forma horizontal. Requiere una velocidad de transferencia ultra rápida (ej. NVLink).")
                print("       Al estar en ordenadores separados por red local común, DEBE mantenerse en 1, ya que")
                print("       de lo contrario el clúster se congelará por la latencia del cable de red local.")
                print("  6. Migrar Master: Para alternar el PC principal, ve a ese equipo, selecciona")
                print("     la opción [1] (Ajustes) -> opción [1] (Forzar Master), y luego inicialo con la opción [2].")
                print("     El otro PC se adaptará a Worker automáticamente en su siguiente inicio.")
                print("  7. Restaurar Configuración: Si configuras parámetros erróneos, selecciona la opción [1]")
                print("     (Ajustes) -> opción [5] (Restaurar Valores por Defecto) para volver al modelo y")
                print("     paralelismo originales (Qwen, PP=2, TP=1) y re-establecer el Master al PC local.")
                print("  8. Apagado: Selecciona la opción [2] (cuando esté ON) en ambos PCs para liberar la VRAM.")
                print("  9. Nuevo Portátil / Segundo Equipo: Copia la carpeta a C:\\xyz-gpu, instala los requisitos previos (WSL2/Docker/Red Espejo),")
                print("     abre Ajustes [1] -> opción [4] y escribe la IP del Master. Luego levanta el clúster con la opción [2].")
            else:
                print(f"\n📝 {C_BOLD}XYZ-GPU USAGE INSTRUCTIONS:{C_RESET}")
                print("  1. Requirements: Make sure Docker Desktop with WSL2 integration is active.")
                print("  2. Mirrored Network: Verify that the network mode 'mirrored' is set in .wslconfig.")
                print("  3. Cluster Booting:")
                print(f"     - On the MASTER PC ({master_hostname}): Choose option [2]. Launches Ray and vLLM.")
                print("     - On the WORKER PC: Choose option [2]. Connects automatically to the Master node.")
                print("  4. Live GPU Diagnostics:")
                print("     - Choose option [4] to view real-time GPU statistics (nvidia-smi), refreshing every 2s.")
                print("       Press 'q' or Enter to return to the main menu.")
                print("  5. Parallelism Parameters (Settings):")
                print(f"     - {C_BOLD}Pipeline Parallelism (PP):{C_RESET} Splits the model's layers vertically into blocks.")
                print("       Por example, layers 1-16 on PC 1 and 17-32 on PC 2. They communicate over LAN when")
                print("       transitioning layers. Ideal for local setups (set to 2).")
                print(f"     - {C_BOLD}Tensor Parallelism (TP):{C_RESET} Splits individual matrix operations (tensors)")
                print("       horizontally. Requires ultra-fast bandwidth (e.g., NVLink). Over common LAN, IT MUST")
                print("       remain set to 1, otherwise the cluster will freeze due to network latency.")
                print("  6. Migrate Master: To switch the main PC, go to that machine, select")
                print("     Option [1] (Settings) -> Option [1] (Force Master), and then start it using Option [2].")
                print("     The other PC will adapt as a Worker node on its next boot.")
                print("  7. Restore Settings: If you write incorrect parameters, select Option [1] (Settings)")
                print("     -> Option [5] (Restore Factory Defaults) to reset to default values (Qwen, PP=2, TP=1)")
                print("     and set the Master back to the local PC.")
                print("  8. Shutdown: Choose Option [2] (when ON) on both PCs to release GPU VRAM.")
                print("  9. New Laptop / Second Device: Copy folder to C:\\xyz-gpu, install prerequisites (WSL2/Docker/Mirrored),")
                print("     go to Settings [1] -> Option [4] and enter the Master IP. Then launch the cluster via Option [2].")
            input(f"\n{T[lang]['press_enter_menu']}")

            
        elif opc == "6":
            print(f"\n🔄 {T[lang]['update_run']}")
            try:
                res = subprocess.run(["git", "pull"], capture_output=True, text=True)
                print(res.stdout)
                if res.returncode == 0:
                    print(f"{C_LIME}[SUCCESS] {T[lang]['update_success']}{C_RESET}")
                else:
                    print(f"{C_PINK}[ERROR] {T[lang]['update_failed']}{C_RESET}")
                    if res.stderr:
                        print(f"Details: {res.stderr}")
            except Exception as e:
                print(f"{C_PINK}[ERROR] {T[lang]['update_failed']}: {e}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "7":
            # Alternar idioma y guardarlo en el archivo de estado compartido
            state["language"] = "en" if lang == "es" else "es"
            save_state(state)
            print(f"\n🔄 Cambiando idioma a Inglés..." if lang == "es" else f"\n🔄 Switching language to Spanish...")
            time.sleep(0.5)
            
        elif opc == "8":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)



if __name__ == '__main__':
    main()
