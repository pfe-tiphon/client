from jetson_bridge import JetsonBridge
import time
import threading

# --- CONFIGURATION ---
#BRIDGE = JetsonBridge(port='/dev/ttyTHS1', baudrate=115200)
BRIDGE = JetsonBridge(port='COM6', baudrate=115200)

# --- LOGIQUE DES COMMANDES (Extensions faciles) ---
def cmd_photo():
    BRIDGE.send_image("logo_tiphon.jpg")

def cmd_status():
    BRIDGE.send_text("Jetson Orin Nano: GPU OK - Drone en vol")

def cmd_help():
    liste_commandes = ", ".join(COMMANDS.keys())
    BRIDGE.send_text(f"Commandes disponibles : {liste_commandes}")

def cmd_specs():
    stats = BRIDGE.get_stats()
    # On envoie les stats ligne par ligne ou en un bloc
    BRIDGE.send_text(stats)

COMMANDS = {
    "photo": cmd_photo,
    "status": cmd_status,
    "help": cmd_help,
    "specs": cmd_specs
}

# --- SIMULATION DETECTION BATEAU ---
def on_boat_detected(label, confidence, position):
    """Fonction à appeler par ton modèle IA"""
    timestamp = time.strftime("%H:%M:%S")
    msg = f"ALERTE : {label} detecte ({confidence}%) à {position} à {timestamp}"
    
    # 1. Envoyer le texte
    BRIDGE.send_text(msg)
    # 2. Envoyer l'image (capture d'écran de la détection par exemple)
    BRIDGE.send_image("detection_capture.jpg")

BRIDGE.start_background_listener(COMMANDS)

def main():
    print("Système prêt et écoute du port série...")
    try:
        while True:
            # ICI : code de détection IA
            
            
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Arrêt...")
    finally:
        BRIDGE.close()

if __name__ == "__main__":
    main()