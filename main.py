from jetson_bridge import JetsonBridge
import time

# --- CONFIGURATION ---
# Utilise '/dev/ttyTHS0' sur Jetson ou 'COMx' sur Windows pour tes tests
#BRIDGE = JetsonBridge(port='/dev/ttyTHS0', baudrate=115200)
BRIDGE = JetsonBridge(port='COM12', baudrate=115200)

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

# --- SIMULATION DETECTION BATEAU (Pour ton modèle IA) ---
def on_boat_detected(label, confidence, position):
    """Fonction à appeler par ton modèle IA"""
    timestamp = time.strftime("%H:%M:%S")
    msg = f"ALERTE : {label} detecte ({confidence}%) à {position} à {timestamp}"
    
    # 1. Envoyer le texte
    BRIDGE.send_text(msg)
    # 2. Envoyer l'image (capture d'écran de la détection par exemple)
    BRIDGE.send_image("detection_capture.jpg")

# --- BOUCLE PRINCIPALE ---
def main():
    print("Système prêt et écoute du port série...")
    try:
        while True:
            # 1. Vérifier si le PC envoie une commande
            BRIDGE.check_commands(COMMANDS)
            
            # 2. Emplacement pour ton code de détection IA
            # Exemple : 
            # if model.detect(frame) == 'Bateau':
            #    on_boat_detected("Cargo", 98, "N-45.2 E-5.1")
            
            time.sleep(0.01) # Évite de saturer le CPU
            
    except KeyboardInterrupt:
        print("Arrêt demandé...")
    finally:
        BRIDGE.close()

if __name__ == "__main__":
    main()