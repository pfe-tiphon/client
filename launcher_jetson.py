import serial
import json
import subprocess
import time
import os

# Chemins système
PYTHON_PATH = "/home/tiphon/Documents/tiphon_v1.0/Tiphon/venv310/bin/python"
MAIN_SCRIPT = "/home/tiphon/Documents/tiphon_v1.0/Tiphon/clientV3/main_jetson.py"

def main():
    # Préparation de l'environnement headless (sans écran)
    my_env = os.environ.copy()
    my_env["QT_QPA_PLATFORM"] = "offscreen"

    while True:
        # Tentative d'ouverture du port série en mode veille
        try:
            ser = serial.Serial("/dev/ttyTHS1", 921600, timeout=1)
            print("[Launcher] Système en veille. Port /dev/ttyTHS1 ouvert.")
        except Exception as e:
            print(f"[Launcher] Attente port série... ({e})")
            time.sleep(2)
            continue

        try:
            while True:
                # 1. Envoi du Heartbeat de veille au serveur
                ser.write(b'{"type": "heartbeat", "status": "standby"}\n')
                
                # 2. Écoute de la commande START
                if ser.in_waiting > 0:
                    line = ser.readline().decode(errors='ignore').strip()
                    
                    if '"cmd": "START"' in line:
                        print("[Launcher] Ordre START reçu. Libération du port...")
                        
                        # Fermeture du port pour le laisser au script principal
                        ser.close()
                        
                        # Lancement du processus de détection en mode headless
                        process = subprocess.Popen([PYTHON_PATH, MAIN_SCRIPT], env=my_env)
                        
                        # Le launcher attend ici que le programme principal s'arrête (via l'ordre STOP)
                        process.wait()
                        
                        print("[Launcher] Programme principal arrêté. Reprise du contrôle.")
                        break # Sort de la boucle interne pour réouvrir le port proprement
                
                time.sleep(1)
                
        except Exception as e:
            print(f"[Launcher] Erreur boucle : {e}")
        finally:
            if ser.is_open:
                ser.close()
        
        # Petite pause avant de tenter de réouvrir le port
        time.sleep(1)

if __name__ == "__main__":
    main()