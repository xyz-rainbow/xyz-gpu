import os
import sys
import json
import socket
import subprocess
import time
import locale

# Asegurar que el directorio de trabajo es el del propio script para soportar cualquier ruta
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
        "menu_bridge": "Puente USB para Móviles (ADB Bridge)",
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
        "settings_quant": "Modificar Cuantización del Modelo",
        "settings_context": "Modificar Límite de Contexto (max-model-len)",
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
        "quant_prompt": "Modificar Método de Cuantización (opciones: None, awq, gptq, squeezellm)",
        "quant_input": "Método de cuantización (deja vacío para precisión nativa FP16)",
        "quant_success": "Cuantización del modelo actualizada con éxito.",
        "context_prompt": "Modificar Límite de Contexto del Modelo (Tokens máximos)",
        "context_input": "Tokens de contexto",
        "context_success": "Límite de contexto actualizado con éxito.",
        "quantization_label": "Cuantización",
        "context_label": "Límite de Contexto",
        "settings_startup": "Encender al inicio del sistema",
        "startup_success": "Inicio automático actualizado con éxito.",
        "menu_farm": "Granja de Móviles (Mobile USB Farm)",
        "farm_title": "AJUSTES DE GRANJA DE MÓVILES USB",
        "farm_toggle": "Activar / Desactivar Granja de Móviles",
        "farm_nodes": "Modificar Número de Nodos Móviles",
        "farm_port": "Modificar Puerto Inicial del Reenvío",
        "farm_success_toggle": "Estado de la granja de móviles actualizado.",
        "farm_success_nodes": "Número de nodos móviles actualizado con éxito.",
        "farm_success_port": "Puerto inicial actualizado con éxito.",
        "farm_back": "Volver a Ajustes",



        
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
        "menu_update": "Centro de Actualizaciones (Git)",
        "update_run": "Buscando actualizaciones en GitHub (git pull)...",
        "update_success": "Orquestador actualizado con éxito. Reinicia el asistente para aplicar los cambios.",
        "update_failed": "No se pudo actualizar. Asegúrate de tener Git instalado y configurado en esta carpeta.",
        "update_title": "CENTRO DE ACTUALIZACIONES",
        "update_check": "Buscar actualizaciones (Comprobar estado remoto)",
        "update_run_btn": "Aplicar actualizaciones disponibles (Git Pull)",
        "update_current": "Versión local actual (Commit)",
        "update_checking": "Conectando con GitHub para comprobar actualizaciones...",
        "update_latest": "¡Estás en la última versión!",
        "update_available": "Hay una nueva versión disponible en GitHub.",
        "update_error_check": "No se pudo comprobar el estado remoto.",
        "update_back": "Volver al Menú Principal",
        "select_update_option": "Selecciona una opción de Actualización: ",


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
        "menu_bridge": "USB Mobile Bridge (ADB Bridge)",
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
        "settings_quant": "Modify Model Quantization",
        "settings_context": "Modify Context Limit (max-model-len)",
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
        "quant_prompt": "Modify Quantization Method (options: None, awq, gptq, squeezellm)",
        "quant_input": "Quantization method (leave empty for native FP16)",
        "quant_success": "Model quantization successfully updated.",
        "context_prompt": "Modify Model Context Limit (Max Tokens)",
        "context_input": "Context tokens",
        "context_success": "Context limit successfully updated.",
        "quantization_label": "Quantization",
        "context_label": "Context Limit",
        "settings_startup": "Start on system boot",
        "startup_success": "Auto-start setting updated successfully.",
        "menu_farm": "Mobile Farm (Mobile USB Farm)",
        "farm_title": "MOBILE USB FARM CONFIGURATION",
        "farm_toggle": "Toggle Mobile USB Farm",
        "farm_nodes": "Modify Number of Mobile Nodes",
        "farm_port": "Modify Forward Start Port",
        "farm_success_toggle": "Mobile farm status updated.",
        "farm_success_nodes": "Number of mobile nodes successfully updated.",
        "farm_success_port": "Start port successfully updated.",
        "farm_back": "Back to Settings",



        
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
        "menu_update": "Update Center (Git)",
        "update_run": "Checking for updates on GitHub (git pull)...",
        "update_success": "Orchestrator successfully updated. Please restart the assistant to apply changes.",
        "update_failed": "Failed to update. Make sure Git is installed and configured in this folder.",
        "update_title": "UPDATE CENTER",
        "update_check": "Check for updates (Check remote status)",
        "update_run_btn": "Apply available updates (Git Pull)",
        "update_current": "Current local version (Commit)",
        "update_checking": "Connecting to GitHub to check for updates...",
        "update_latest": "You are on the latest version!",
        "update_available": "A new version is available on GitHub.",
        "update_error_check": "Could not check remote status.",
        "update_back": "Back to Main Menu",
        "select_update_option": "Select an Update option: ",
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

def update_startup_shortcut(enabled):
    startup_folder = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    startup_file = os.path.join(startup_folder, "xyz_gpu_startup.bat")
    
    if enabled:
        if os.name == 'nt':
            try:
                local_hostname = socket.gethostname().upper()
                env_file = os.path.join(script_dir, f".env.{local_hostname}")
                content = f"""@echo off
cd /d "{script_dir}"
python install_gpu.py --generate-env-only
docker compose --env-file "{env_file}" up -d
"""
                with open(startup_file, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                pass
    else:
        if os.name == 'nt' and os.path.exists(startup_file):
            try:
                os.remove(startup_file)
            except Exception:
                pass

def generate_litellm_config(state):
    enabled = state.get("mobile_farm_enabled", False)
    num_nodes = int(state.get("mobile_farm_nodes", 7))
    start_port = int(state.get("mobile_farm_start_port", 50051))
    
    config = {
        "model_list": [
            {
                "model_name": "hybrid-model",
                "litellm_params": {
                    "model": "openai/vllm",
                    "api_base": "http://localhost:8000/v1",
                    "api_key": "any-key",
                    "rpm": 100,
                    "tpm": 100000
                }
            }
        ],
        "router_settings": {
            "routing_strategy": "failover",
            "allowed_fails": 2,
            "cooldown_time": 10
        }
    }
    
    if enabled and num_nodes > 0:
        for i in range(1, num_nodes + 1):
            port = start_port + i - 1
            config["model_list"].append({
                "model_name": "hybrid-model",
                "litellm_params": {
                    "model": f"openai/mobile-node-{i}",
                    "api_base": f"http://localhost:{port}/v1",
                    "api_key": "any-key",
                    "rpm": 15
                },
                "fallback_value": True
            })
            
    yaml_lines = ["model_list:"]
    for model in config["model_list"]:
        yaml_lines.append(f"  - model_name: {model['model_name']}")
        yaml_lines.append("    litellm_params:")
        yaml_lines.append(f"      model: {model['litellm_params']['model']}")
        yaml_lines.append(f"      api_base: {model['litellm_params']['api_base']}")
        yaml_lines.append(f"      api_key: \"{model['litellm_params']['api_key']}\"")
        if "rpm" in model['litellm_params']:
            yaml_lines.append(f"      rpm: {model['litellm_params']['rpm']}")
        if "tpm" in model['litellm_params']:
            yaml_lines.append(f"      tpm: {model['litellm_params']['tpm']}")
        if model.get("fallback_value"):
            yaml_lines.append("    fallback_value: true")
        yaml_lines.append("")
        
    yaml_lines.append("router_settings:")
    yaml_lines.append(f"  routing_strategy: {config['router_settings']['routing_strategy']}")
    yaml_lines.append(f"  allowed_fails: {config['router_settings']['allowed_fails']}")
    yaml_lines.append(f"  cooldown_time: {config['router_settings']['cooldown_time']}")
    
    try:
        with open("litellm-config.yaml", "w", encoding="utf-8") as f:
            f.write("\n".join(yaml_lines) + "\n")
    except Exception:
        pass


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
            "quantization": "",
            "max_model_len": "2048",
            "startup_enabled": True,
            "mobile_farm_enabled": False,
            "mobile_farm_nodes": "7",
            "mobile_farm_start_port": "50051",
            "language": detect_system_language(),
            "registered_nodes": {
                local_hostname: local_ip
            }
        }
        save_state(default_state)
        update_startup_shortcut(True)
        generate_litellm_config(default_state)
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
        if "quantization" not in state:
            state["quantization"] = ""
        if "max_model_len" not in state:
            state["max_model_len"] = "2048"
        if "startup_enabled" not in state:
            state["startup_enabled"] = True
        if "mobile_farm_enabled" not in state:
            state["mobile_farm_enabled"] = False
        if "mobile_farm_nodes" not in state:
            state["mobile_farm_nodes"] = "7"
        if "mobile_farm_start_port" not in state:
            state["mobile_farm_start_port"] = "50051"
            
        save_state(state)
        update_startup_shortcut(state.get("startup_enabled", True))
        generate_litellm_config(state)
            
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
            "quantization": "",
            "max_model_len": "2048",
            "startup_enabled": True,
            "mobile_farm_enabled": False,
            "mobile_farm_nodes": "7",
            "mobile_farm_start_port": "50051",
            "language": detect_system_language(),
            "registered_nodes": {
                local_hostname: local_ip
            }
        }

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
        generate_litellm_config(state)
    except Exception as e:
        print(f"\n{C_PINK}[ERR] No se pudo guardar el archivo de estado central: {e}{C_RESET}")

def trigger_auto_restart_if_active(state, local_hostname):
    if is_cluster_running():
        lang = state.get("language", "es")
        master_hostname = state.get("master_hostname", "").upper()
        master_ip = state.get("master_ip", "")
        if local_hostname == master_hostname:
            current_role = "head"
        else:
            current_role = "worker"
        
        env_file = f".env.{local_hostname}"
        print(f"\n🔄 {C_CYAN}[AUTO-RESTART]{C_RESET} " + 
              ("Aplicando cambios y reiniciando contenedores..." if lang == "es" else "Applying changes and restarting containers..."))
        
        generate_env_file(local_hostname, current_role, master_ip, state)
        
        try:
            print(f"🛑 {T[lang]['cfg_stopping']}")
            subprocess.run(["docker", "compose", "--env-file", env_file, "down"], check=True)
            print(f"🚀 {T[lang]['cfg_launching']}")
            subprocess.run(["docker", "compose", "--env-file", env_file, "up", "-d"], check=True)
            print(f"\n{C_LIME}[SUCCESS] " + 
                  ("Clúster reiniciado con éxito con la nueva configuración." if lang == "es" else "Cluster successfully restarted with the new configuration.") + 
                  f"{C_RESET}")
        except Exception as e:
            print(f"\n{C_PINK}[ERROR] " + 
                  (f"Error al reiniciar: {e}" if lang == "es" else f"Restart failed: {e}") + 
                  f"{C_RESET}")

def generate_env_file(hostname, role, master_ip, state):
    env_filename = f".env.{hostname}"
    try:
        hf_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
        hf_cache = hf_cache.replace("\\", "/")
        with open(env_filename, "w", encoding="utf-8") as f:
            f.write(f"NODE_ROLE={role}\n")
            f.write(f"MASTER_IP={master_ip}\n")
            f.write(f"MODEL_NAME={state.get('model_name', 'Qwen/Qwen2.5-VL-7B-Instruct')}\n")
            f.write(f"PIPELINE_SIZE={state.get('pipeline_parallel_size', '2')}\n")
            f.write(f"TENSOR_SIZE={state.get('tensor_parallel_size', '1')}\n")
            f.write(f"GPU_MEM_LIMIT={state.get('gpu_memory_utilization', '0.90')}\n")
            f.write(f"VLLM_QUANTIZATION={state.get('quantization', '')}\n")
            f.write(f"MAX_MODEL_LEN={state.get('max_model_len', '2048')}\n")
            f.write(f"HF_CACHE_DIR={hf_cache}\n")
        return env_filename
    except Exception as e:
        print(f"\n{C_PINK}[ERR] Error al generar el archivo de entorno {env_filename}: {e}{C_RESET}")
        return None

def spawn_detached_notifications(lang):
    if os.name == 'nt':
        text_5_es = "El clúster [XYZ-GPU] está en ejecución (5m). Recuerda verificar el auto-inicio."
        text_5_en = "The [XYZ-GPU] cluster is running (5m). Remember to check the auto-start."
        text_15_es = "El clúster [XYZ-GPU] sigue activo en segundo plano (15m). Libera las GPUs si no las usas."
        text_15_en = "The [XYZ-GPU] cluster is still active in the background (15m). Release GPUs if not in use."
        
        t5 = text_5_es if lang == "es" else text_5_en
        t15 = text_15_es if lang == "es" else text_15_en
        
        ps_cmd = f"""Start-Sleep -Seconds 300
$docker = docker ps --filter "name=vllm-cluster-node" --filter "status=running" --format "{{{{.Names}}}}"
if ($docker -like "*vllm-cluster-node*") {{
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
    $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
    $objNotifyIcon.BalloonTipIcon = 'Info'
    $objNotifyIcon.BalloonTipText = '{t5}'
    $objNotifyIcon.BalloonTipTitle = '[XYZ-GPU]'
    $objNotifyIcon.Visible = $True
    $objNotifyIcon.ShowBalloonTip(10000)
}}
Start-Sleep -Seconds 600
$docker = docker ps --filter "name=vllm-cluster-node" --filter "status=running" --format "{{{{.Names}}}}"
if ($docker -like "*vllm-cluster-node*") {{
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
    $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
    $objNotifyIcon.BalloonTipIcon = 'Info'
    $objNotifyIcon.BalloonTipText = '{t15}'
    $objNotifyIcon.BalloonTipTitle = '[XYZ-GPU]'
    $objNotifyIcon.Visible = $True
    $objNotifyIcon.ShowBalloonTip(10000)
}}
"""
        try:
            subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps_cmd], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                             creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        except Exception:
            pass

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
    running = is_cluster_running()
    if running:
        status_label = f"{C_BOLD}{C_LIME}ON{C_RESET}"
        model_display = f"{C_LIME}[{state.get('model_name')}]{C_RESET}"
    else:
        status_label = f"{C_BOLD}{C_RED}OFF{C_RESET}"
        model_display = f"\033[90m[{'Ninguno (No iniciado en este equipo)' if lang == 'es' else 'None (Not running on this node)'}]\033[0m"
        
    print(f" {C_BOLD}{T[lang]['device']}:{C_RESET} {C_ORANGE}{local_hostname}{C_RESET} ({local_ip}) -> {role_label}")
    print(f" {C_BOLD}{T[lang]['config']}:{C_RESET}")
    print(f"  ├── {C_BOLD}{T[lang]['assigned_master']}:{C_RESET} {C_RED}[{master_hostname}]{C_RESET} ({master_ip})")
    print(f"  ├── {T[lang]['active_model']}:        {model_display}")
    # Mostrar cuantización del modelo
    quant_display = state.get('quantization', '')
    if not quant_display:
        quant_display = "Ninguna (FP16)" if lang == "es" else "None (FP16)"
    if not running:
        quant_display = f"\033[90m{quant_display}\033[0m"
    print(f"  ├── {T[lang]['quantization_label']}:          {C_CYAN}{quant_display}{C_RESET}" if running else f"  ├── {T[lang]['quantization_label']}:          {quant_display}")
    # Mostrar límite de contexto
    context_val = state.get('max_model_len', '2048')
    if not running:
        context_display = f"\033[90m{context_val} tokens\033[0m"
    else:
        context_display = f"{C_PURPLE}{context_val} tokens{C_RESET}"
    print(f"  ├── {T[lang]['context_label']}:    {context_display}")
    
    if not running:
        parallel_display = f"\033[90mPipeline: {state.get('pipeline_parallel_size')} | Tensor: {state.get('tensor_parallel_size')}\033[0m"
    else:
        parallel_display = f"Pipeline: {state.get('pipeline_parallel_size')} | Tensor: {state.get('tensor_parallel_size')}"
    print(f"  ├── {T[lang]['parallelism']}:          {parallel_display}")
    # Mostrar límite de asignación de VRAM
    vram_percent = int(float(state.get('gpu_memory_utilization', '0.90')) * 100)
    vram_val = state.get('gpu_memory_utilization', '0.90')
    if not running:
        vram_display = f"\033[90m{vram_percent}% ({vram_val})\033[0m"
    else:
        vram_display = f"{vram_percent}% ({vram_val})"
    print(f"  ├── {T[lang]['vram_allocation']}:       {vram_display}")
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

def mobile_farm_menu(local_hostname, local_ip):
    while True:
        state = load_state()
        master_hostname = state.get("master_hostname", "").upper()
        lang = state.get("language", "es")
        
        if local_hostname == master_hostname:
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_BOLD}{T[lang]['farm_title']}:{C_RESET}")
        
        farm_enabled = state.get("mobile_farm_enabled", False)
        farm_enabled_str = f"{C_LIME}[ ACTIVADO / ON ]{C_RESET}" if farm_enabled else f"{C_PINK}[ DESACTIVADO / OFF ]{C_RESET}"
        
        print(f"  {C_LIME}[1]{C_RESET} {T[lang]['farm_toggle']} {farm_enabled_str}")
        print(f"  {C_LIME}[2]{C_RESET} {T[lang]['farm_nodes']} [{state.get('mobile_farm_nodes', '7')}]")
        print(f"  {C_LIME}[3]{C_RESET} {T[lang]['farm_port']} [{state.get('mobile_farm_start_port', '50051')}]")
        print(f"  {C_LIME}[4]{C_RESET} {T[lang]['farm_back']}")
        print(f"  {C_LIME}[5]{C_RESET} {T[lang]['menu_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        opc = input(f" {C_BOLD}{T[lang]['select_settings_option']}{C_RESET}").strip()
        
        if opc == "1":
            new_val = not farm_enabled
            state["mobile_farm_enabled"] = new_val
            save_state(state)
            print(f"\n{C_LIME}[OK] {T[lang]['farm_success_toggle']}{C_RESET}")
            trigger_auto_restart_if_active(state, local_hostname)
            input(f"\n{T[lang]['press_enter']}")
        elif opc == "2":
            entered_nodes = input(f"\n📝 {T[lang]['farm_nodes']} (0-10): ").strip()
            if entered_nodes:
                try:
                    val = int(entered_nodes)
                    if 0 <= val <= 10:
                        state["mobile_farm_nodes"] = str(val)
                        save_state(state)
                        print(f"{C_LIME}[OK] {T[lang]['farm_success_nodes']}{C_RESET}")
                        trigger_auto_restart_if_active(state, local_hostname)
                    else:
                        print(f"{C_PINK}[ERR] Debe ser un número entre 0 y 10.{C_RESET}")
                except ValueError:
                    print(f"{C_PINK}[ERR] Formato no válido.{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif opc == "3":
            entered_port = input(f"\n📝 {T[lang]['farm_port']}: ").strip()
            if entered_port:
                try:
                    val = int(entered_port)
                    if 1024 <= val <= 65535:
                        state["mobile_farm_start_port"] = str(val)
                        save_state(state)
                        print(f"{C_LIME}[OK] {T[lang]['farm_success_port']}{C_RESET}")
                        trigger_auto_restart_if_active(state, local_hostname)
                    else:
                        print(f"{C_PINK}[ERR] Debe ser un puerto entre 1024 y 65535.{C_RESET}")
                except ValueError:
                    print(f"{C_PINK}[ERR] Formato no válido.{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif opc == "4":
            break
        elif opc == "5":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)


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
        print(f"  {C_LIME}[6]{C_RESET} {T[lang]['settings_quant']}")
        print(f"  {C_LIME}[7]{C_RESET} {T[lang]['settings_context']}")
        
        farm_status = f"{C_LIME}[ ACTIVADO / ON ]{C_RESET}" if state.get("mobile_farm_enabled", False) else f"{C_PINK}[ DESACTIVADO / OFF ]{C_RESET}"
        print(f"  {C_LIME}[8]{C_RESET} {T[lang]['menu_farm']} {farm_status}")
        
        startup_status = f"{C_LIME}[ ACTIVADO / ON ]{C_RESET}" if state.get("startup_enabled", True) else f"{C_PINK}[ DESACTIVADO / OFF ]{C_RESET}"
        print(f"  {C_LIME}[9]{C_RESET} {T[lang]['settings_startup']} {startup_status}")
        
        print(f"  {C_LIME}[10]{C_RESET} {T[lang]['menu_bridge']}")
        lang_str = "English" if lang == "es" else "Español"
        print(f"  {C_LIME}[11]{C_RESET} {T[lang]['menu_lang']} ({lang_str})")
        
        print(f"  {C_LIME}[12]{C_RESET} {T[lang]['settings_defaults']}")
        print(f"  {C_LIME}[13]{C_RESET} {T[lang]['settings_ping']}")
        print(f"  {C_LIME}[14]{C_RESET} {T[lang]['settings_back']}")
        print(f"  {C_LIME}[15]{C_RESET} {T[lang]['menu_exit']}")
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        sub_opc = input(f" {C_BOLD}{T[lang]['select_settings_option']}{C_RESET}").strip()
        
        if sub_opc == "1":
            print(f"\n🔄 {T[lang]['migrate_run']}")
            state["master_hostname"] = local_hostname
            state["master_ip"] = local_ip
            save_state(state)
            print(f"{C_LIME}[OK] {T[lang]['migrate_success']}{C_RESET}")
            trigger_auto_restart_if_active(state, local_hostname)
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "2":
            print(f"\n📝 {C_BOLD}{T[lang]['model_prompt']}:{C_RESET}")
            new_model = input(f" {T[lang]['model_input']} [{state.get('model_name')}]: ").strip()
            if new_model:
                state["model_name"] = new_model
                save_state(state)
                print(f"{C_LIME}[OK] {T[lang]['model_success']}{C_RESET}")
                trigger_auto_restart_if_active(state, local_hostname)
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
                trigger_auto_restart_if_active(state, local_hostname)
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
                trigger_auto_restart_if_active(state, local_hostname)
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
                        trigger_auto_restart_if_active(state, local_hostname)
                    else:
                        print(f"{C_PINK}[ERR] El valor debe estar entre 0.1 y 1.0 / Value must be between 0.1 and 1.0{C_RESET}")
                except ValueError:
                    print(f"{C_PINK}[ERR] Formato no válido / Invalid format{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "6":
            print(f"\n📝 {C_BOLD}{T[lang]['quant_prompt']}:{C_RESET}")
            entered_quant = input(f" {T[lang]['quant_input']} [{state.get('quantization', '')}]: ").strip()
            if entered_quant.lower() in ["none", ""]:
                state["quantization"] = ""
            else:
                state["quantization"] = entered_quant
            save_state(state)
            print(f"{C_LIME}[OK] {T[lang]['quant_success']}{C_RESET}")
            trigger_auto_restart_if_active(state, local_hostname)
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "7":
            print(f"\n📝 {C_BOLD}{T[lang]['context_prompt']}:{C_RESET}")
            entered_context = input(f" {T[lang]['context_input']} [{state.get('max_model_len', '2048')}]: ").strip()
            if entered_context:
                try:
                    val = int(entered_context)
                    if val > 0:
                        state["max_model_len"] = str(val)
                        save_state(state)
                        print(f"{C_LIME}[OK] {T[lang]['context_success']}{C_RESET}")
                        trigger_auto_restart_if_active(state, local_hostname)
                    else:
                        print(f"{C_PINK}[ERR] El valor debe ser un entero positivo / Value must be a positive integer{C_RESET}")
                except ValueError:
                    print(f"{C_PINK}[ERR] Formato no válido / Invalid format{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "8":
            mobile_farm_menu(local_hostname, local_ip)
        elif sub_opc == "9":
            current_val = state.get("startup_enabled", True)
            new_val = not current_val
            state["startup_enabled"] = new_val
            save_state(state)
            update_startup_shortcut(new_val)
            print(f"\n{C_LIME}[OK] {T[lang]['startup_success']}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "10":
            print(f"\n🔗 Iniciando Puente USB Móvil (ADB Bridge)..." if lang == "es" else f"\n🔗 Starting Mobile USB Bridge (ADB Bridge)...")
            try:
                subprocess.run([sys.executable, "xyz_bridge.py"])
            except Exception as e:
                print(f"{C_PINK}Error launching xyz_bridge.py: {e}{C_RESET}")
                input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "11":
            # Alternar idioma y guardarlo en el archivo de estado compartido
            state["language"] = "en" if lang == "es" else "es"
            save_state(state)
            print(f"\n🔄 Cambiando idioma a Inglés..." if lang == "es" else f"\n🔄 Switching language to Spanish...")
            time.sleep(0.5)
        elif sub_opc == "12":
            print(f"\n🔄 {T[lang]['defaults_run']}")
            state["master_hostname"] = local_hostname
            state["master_ip"] = local_ip
            state["model_name"] = "Qwen/Qwen2.5-VL-7B-Instruct"
            state["pipeline_parallel_size"] = "2"
            state["tensor_parallel_size"] = "1"
            state["gpu_memory_utilization"] = "0.90"
            state["quantization"] = ""
            state["max_model_len"] = "2048"
            state["startup_enabled"] = True
            state["mobile_farm_enabled"] = False
            state["mobile_farm_nodes"] = "7"
            state["mobile_farm_start_port"] = "50051"
            save_state(state)
            update_startup_shortcut(True)
            print(f"{C_LIME}[SUCCESS] {T[lang]['defaults_success']}{C_RESET}")
            trigger_auto_restart_if_active(state, local_hostname)
            input(f"\n{T[lang]['press_enter']}")
        elif sub_opc == "13":
            ping_menu(local_hostname, local_ip)
        elif sub_opc == "14":
            break
        elif sub_opc == "15":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)




def get_git_info():
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        msg = subprocess.run(["git", "log", "-1", "--format=%s"], capture_output=True, text=True, check=True).stdout.strip()
        return commit, msg
    except Exception:
        return "Unknown", "N/A"

def get_remote_git_info():
    try:
        # Intentamos obtener el commit de la rama remota que sigue a la actual
        commit = subprocess.run(["git", "rev-parse", "--short", "@{u}"], capture_output=True, text=True, check=True).stdout.strip()
        msg = subprocess.run(["git", "log", "-1", "--format=%s", "@{u}"], capture_output=True, text=True, check=True).stdout.strip()
        return commit, msg
    except Exception:
        return "Unknown", "N/A"

def check_remote_updates():
    try:
        subprocess.run(["git", "fetch"], capture_output=True, check=True, timeout=5)
        local = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        remote = subprocess.run(["git", "rev-parse", "@{u}"], capture_output=True, text=True, check=True).stdout.strip()
        return local == remote, None
    except Exception as e:
        return False, str(e)

def update_menu(local_hostname, local_ip):
    # Hacer fetch inicial silencioso al abrir el menú de actualizaciones
    print(f"\n📡 Conectando con GitHub para comprobar actualizaciones...")
    up_to_date, err = check_remote_updates()
    
    while True:
        state = load_state()
        master_hostname = state.get("master_hostname", "").upper()
        lang = state.get("language", "es")
        
        if local_hostname == master_hostname:
            role_label = f"{C_CYAN}[ MASTER / HEAD ]{C_RESET}"
        else:
            role_label = f"{C_PINK}[ WORKER NODE ]{C_RESET}"
            
        print_full_header(state, local_hostname, local_ip, role_label)
        print(f" {C_BOLD}{T[lang]['update_title']}:{C_RESET}")
        
        local_commit, local_msg = get_git_info()
        remote_commit, remote_msg = get_remote_git_info()
        
        print(f"  {C_BOLD}{T[lang]['update_current']}:{C_RESET} {C_LIME}{local_commit}{C_RESET} (\"{local_msg}\")")
        
        if err:
            print(f"  {C_BOLD}Versión remota:{C_RESET} {C_PINK}[ERR]{C_RESET} (No se pudo conectar: {err})")
        else:
            if up_to_date:
                print(f"  {C_BOLD}Versión remota:{C_RESET} {C_LIME}{remote_commit}{C_RESET} (✔️ ¡Al día / Up to date!)")
            else:
                print(f"  {C_BOLD}Versión remota:{C_RESET} {C_ORANGE}{remote_commit}{C_RESET} (⚠️ ¡Actualización disponible! / Update available: \"{remote_msg}\")")
                
        print(f"  {C_CYAN}──────────────────────────────────────────────{C_RESET}")
        
        # Opciones consistentes con la misma numeración
        if not up_to_date and not err:
            print(f"  {C_LIME}[1]{C_RESET} {T[lang]['update_run_btn']} ({C_ORANGE}Aplicar {remote_commit}{C_RESET})")
        else:
            # Si no hay actualizaciones o hay error, la opción de aplicar sale deshabilitada en gris oscuro
            if lang == "es":
                print(f"  \033[90m[1] Aplicar actualizaciones disponibles (Git Pull) [Al día / No disponible]\033[0m")
            else:
                print(f"  \033[90m[1] Apply available updates (Git Pull) [Up to date / Not available]\033[0m")
                
        print(f"  {C_LIME}[2]{C_RESET} Volver a comprobar actualizaciones / Re-check updates")
        print(f"  {C_LIME}[3]{C_RESET} {T[lang]['update_back']}")
        print(f"  {C_LIME}[4]{C_RESET} {T[lang]['menu_exit']}")
            
        print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
        
        opc = input(f" {C_BOLD}{T[lang]['select_update_option']}{C_RESET}").strip()
        
        if opc == "1":
            if not up_to_date and not err:
                print(f"\n🔄 {T[lang]['update_run']}")
                try:
                    res = subprocess.run(["git", "pull"], capture_output=True, text=True)
                    print(res.stdout)
                    if res.returncode == 0:
                        print(f"{C_LIME}[SUCCESS] {T[lang]['update_success']}{C_RESET}")
                        up_to_date = True # marcar como al día tras pull exitoso
                    else:
                        print(f"{C_PINK}[ERROR] {T[lang]['update_failed']}{C_RESET}")
                        if res.stderr:
                            print(f"Details: {res.stderr}")
                except Exception as e:
                    print(f"{C_PINK}[ERROR] {T[lang]['update_failed']}: {e}{C_RESET}")
                input(f"\n{T[lang]['press_enter']}")
            else:
                # Opción deshabilitada
                print(f"\n{C_PINK}Esta opción no está disponible porque ya estás al día.{C_RESET}" if lang == "es" else f"\n{C_PINK}This option is unavailable because you are up to date.{C_RESET}")
                time.sleep(1)
                
        elif opc == "2":
            print(f"\n📡 {T[lang]['update_checking']}")
            up_to_date, err = check_remote_updates()
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "3":
            break
            
        elif opc == "4":
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
                        trigger_auto_restart_if_active(state, local_hostname)
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
                trigger_auto_restart_if_active(state, local_hostname)
            input(f"\n{T[lang]['press_enter']}")
            
        elif opc == "3":
            active_model = state.get("model_name", "Qwen/Qwen2.5-VL-7B-Instruct")
            print(f"\n📥 {T[lang]['models_download_start']}")
            print(f"📦 Modelo: {C_BOLD}{active_model}{C_RESET}\n")
            
            hf_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
            hf_cache = hf_cache.replace("\\", "/")
            # Ejecutar docker para descargar el modelo de Hugging Face
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{hf_cache}:/root/.cache/huggingface",
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


def verify_wsl_network(lang):
    if os.name == 'nt':
        wsl_config = os.path.join(os.path.expanduser("~"), ".wslconfig")
        has_mirrored = False
        if os.path.exists(wsl_config):
            try:
                with open(wsl_config, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "networkingmode" in content.lower().replace(" ", "") and "mirrored" in content.lower().replace(" ", ""):
                        has_mirrored = True
            except Exception:
                pass
        
        if not has_mirrored:
            print(f"\n{C_ORANGE}⚠️  [ADVERTENCIA / WARNING] {C_RESET}")
            if lang == "es":
                print(f" {C_BOLD}No se ha detectado el modo espejo (mirrored) en WSL2.{C_RESET}")
                print(f" Esto es crítico para la intercomunicación de Ray entre tus ordenadores.")
                print(f" Por favor, asegúrate de crear el archivo {C_CYAN}%USERPROFILE%\\.wslconfig{C_RESET} con:")
                print(f"   [wsl2]")
                print(f"   networkingMode=mirrored")
            else:
                print(f" {C_BOLD}WSL2 mirrored network mode was not detected.{C_RESET}")
                print(f" This is critical for Ray inter-communication between devices.")
                print(f" Please ensure your {C_CYAN}%USERPROFILE%\\.wslconfig{C_RESET} file contains:")
                print(f"   [wsl2]")
                print(f"   networkingMode=mirrored")
            print(f"{C_CYAN} ─────────────────────────────────────────────────────────────────────────────────────────{C_RESET}")
            time.sleep(3)


def main():
    wsl_checked = False
    while True:

        state = load_state()
        local_hostname = socket.gethostname().upper()
        local_ip = get_local_ip()
        
        master_hostname = state.get("master_hostname", "").upper()
        master_ip = state.get("master_ip", "")
        lang = state.get("language", "es")
        
        if not wsl_checked:
            verify_wsl_network(lang)
            wsl_checked = True

        
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
        print(f" {C_LIME}[5]{C_RESET} {T[lang]['menu_update']}")
        print(f" {C_LIME}[6]{C_RESET} {T[lang]['menu_instructions']}")
        print(f" {C_LIME}[7]{C_RESET} {T[lang]['menu_exit']}")
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
                    spawn_detached_notifications(lang)
                except Exception as e:
                    print(f"\n{C_PINK}[ERROR] {T[lang]['cfg_err_start']}: {e}{C_RESET}")
            input(f"\n{T[lang]['press_enter']}")
        elif opc == "3":
            models_menu(local_hostname, local_ip)
        elif opc == "4":
            # Diagnóstico GPU
            if os.name == 'nt':
                # Ejecutar comando nvidia-smi en bucle de refresco o diagnóstico estático
                try:
                    import keyboard # type: ignore
                except ImportError:
                    pass
                print(f"\n⚡ {T[lang]['monitor_title']}")
                print(f"   {T[lang]['monitor_help']}\n")
                try:
                    # Hacemos una llamada estática inicial
                    res = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
                    if res.returncode == 0:
                        print(res.stdout)
                    else:
                        print(f"{C_PINK}{T[lang]['monitor_err']}{C_RESET}")
                except Exception as e:
                    print(f"{C_PINK}{T[lang]['monitor_err']}: {e}{C_RESET}")
                input(f"\n{T[lang]['press_enter_menu']}")
            else:
                try:
                    subprocess.run(["nvidia-smi"])
                except Exception as e:
                    print(f"{C_PINK}{T[lang]['monitor_err']}: {e}{C_RESET}")
                input(f"\n{T[lang]['press_enter_menu']}")
        elif opc == "5":
            update_menu(local_hostname, local_ip)
                
        elif opc == "6":
            if lang == "es":
                print(f"\n📝 {C_BOLD}INSTRUCCIONES DE USO DE XYZ-GPU:{C_RESET}")
                print("  1. Requisitos: Asegúrate de tener Docker Desktop con integración de WSL2 activo.")
                print("  2. Red Espejo: Verifica que la red 'mirrored' esté configurada en tu .wslconfig.")
                print("  3. Encendido del Clúster:")
                print(f"     - En el PC MASTER ({master_hostname}): Lanza la opción [2]. Levanta Ray, vLLM y LiteLLM.")
                print("     - En el PC WORKER: Lanza la opción [2]. Se conectará automáticamente al Master.")
                print("  4. Capa Unificada LiteLLM:")
                print("     - Al iniciar el Master, se levanta LiteLLM en el puerto 4000 de forma unificada.")
                print("       Todas tus peticiones de inferencia deben ir a http://localhost:4000/v1.")
                print("       LiteLLM se encargará del balanceo de carga y fallback hacia los móviles USB.")
                print("  5. Puente USB (Móviles):")
                print("     - Si conectas móviles al portátil, inicia el Puente USB en el portátil y escoge Modo Local.")
                print("     - En cualquier otro nodo (ej: Torre), inicia el Puente USB y escoge Modo Remoto.")
                print("       Esto conectará tu nodo al servidor ADB del portátil y expondrá los móviles localmente.")
                print("       LiteLLM redirigirá automáticamente el tráfico sobrante o de failover hacia ellos.")
                print("  6. Diagnóstico de GPU en Vivo:")
                print("     - Lanza la opción [4] para ver el estado de la GPU en tiempo real de forma estática.")
                print("  7. Migrar Master: Para alternar el PC principal, ve a ese equipo, selecciona")
                print("     la opción [1] (Ajustes) -> opción [1] (Forzar Master), y luego inicialo con la opción [2].")
                print("     El otro PC se adaptará a Worker automáticamente en su siguiente inicio.")
                print("  8. Restaurar Configuración: Si configuras parámetros erróneos, selecciona la opción [1]")
                print("     (Ajustes) -> opción [10] (Restaurar Valores por Defecto) para volver al modelo y")
                print("     paralelismo originales (Qwen, PP=2, TP=1) y re-establecer el Master al PC local.")
                print("  9. Apagado: Selecciona la opción [2] (cuando esté ON) en ambos PCs para liberar la VRAM.")
            else:
                print(f"\n📝 {C_BOLD}XYZ-GPU USAGE INSTRUCTIONS:{C_RESET}")
                print("  1. Requirements: Make sure Docker Desktop with WSL2 integration is active.")
                print("  2. Mirrored Network: Verify that the network mode 'mirrored' is set in .wslconfig.")
                print("  3. Cluster Booting:")
                print(f"     - On the MASTER PC ({master_hostname}): Choose option [2]. Launches Ray, vLLM, and LiteLLM.")
                print("     - On the WORKER PC: Choose option [2]. Connects automatically to the Master node.")
                print("  4. Unified LiteLLM Layer:")
                print("     - When starting the Master, LiteLLM launches on port 4000 as a unified gateway.")
                print("       All inference requests should be sent to http://localhost:4000/v1.")
                print("       LiteLLM will manage load-balancing and fallback to USB mobile nodes.")
                print("  5. USB Bridge (Mobile):")
                print("     - If you connect phones to the laptop, run USB Bridge on it and select Local Mode.")
                print("     - On any other node (e.g. Torre), run USB Bridge and select Remote Mode.")
                print("       This connects your node to the laptop's ADB server, exposing phones locally.")
                print("       LiteLLM will automatically route failover/spillover traffic to them.")
                print("  6. Live GPU Diagnostics:")
                print("     - Choose option [4] to view real-time GPU statistics (nvidia-smi).")
                print("  7. Migrate Master: To switch the main PC, go to that machine, select")
                print("     Option [1] (Settings) -> Option [1] (Force Master), and then start it using Option [2].")
                print("     The other PC will adapt as a Worker node on its next boot.")
                print("  8. Restore Settings: If you write incorrect parameters, select Option [1] (Settings)")
                print("     -> Option [10] (Restore Factory Defaults) to reset to default values (Qwen, PP=2, TP=1)")
                print("     and set the Master back to the local PC.")
                print("  9. Shutdown: Choose Option [2] (when ON) on both PCs to release GPU VRAM.")
            input(f"\n{T[lang]['press_enter_menu']}")
            
        elif opc == "7":
            print(f"\n{C_PINK}Saliendo del gestor xyz-gpu. ¡Buen código!{C_RESET}\n" if lang == "es" else f"\n{C_PINK}Exiting xyz-gpu manager. Happy coding!{C_RESET}\n")
            sys.exit(0)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--generate-env-only":
        state = load_state()
        local_hostname = socket.gethostname().upper()
        local_ip = get_local_ip()
        master_hostname = state.get("master_hostname", "").upper()
        master_ip = state.get("master_ip", "")
        if local_hostname == master_hostname:
            role = "head"
        else:
            role = "worker"
        generate_env_file(local_hostname, role, master_ip, state)
        sys.exit(0)
    main()
