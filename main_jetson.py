import os
os.environ['ULTRALYTICS_OFFLINE'] = 'True'

import cv2
import serial
import json
import time
import threading
from maritime_analyzer import MaritimeAnalyzer
from config import *

class FastCamera:
    def __init__(self, src=0, width=1280, height=720):
        self.cap = cv2.VideoCapture(src)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.ret, self.frame = self.cap.read()
        else:
            print(f"[ERREUR] Impossible d'ouvrir la caméra (source {src}).")
            self.ret, self.frame = False, None
            
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
            time.sleep(0.005)

    def read(self):
        return self.ret, self.frame
        
    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.cap.release()

def get_jetson_stats():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu = int(f.read().strip()) / 1000.0
        with open("/sys/class/thermal/thermal_zone1/temp", "r") as f:
            gpu = int(f.read().strip()) / 1000.0
    except:
        cpu, gpu = 0.0, 0.0
    return round(cpu, 1), round(gpu, 1)

def main():
    print("[MAIN] Démarrage du script principal...")
    
    # 1. GESTION ROBUSTE DE L'UART (Attente de libération par le launcher)
    ser = None
    for _ in range(10): # Tente d'ouvrir le port pendant 5 secondes
        try:
            ser = serial.Serial("/dev/ttyTHS1", 921600, timeout=0.001)
            print("[MAIN] Port série ouvert avec succès.")
            break
        except Exception as e:
            time.sleep(0.5)
            
    if ser is None:
        print("[MAIN] ERREUR FATALE : Impossible de récupérer le port série.")
        return # Si on échoue ici, on rend la main au launcher

    # 2. ENVOI IMMÉDIAT D'UN HEARTBEAT "ACTIVE"
    # Cela permet à l'interface PC de passer le voyant au VERT instantanément
    try:
        startup_msg = {"type": "heartbeat", "status": "active", "fps": 0, "cpu": 0, "gpu": 0}
        ser.write((json.dumps(startup_msg) + "\n").encode('utf-8'))
        ser.flush()
    except:
        pass

    # 3. CHARGEMENT DE L'IA (Prend quelques secondes)
    print("[MAIN] Chargement des modèles d'IA (Veuillez patienter)...")
    analyzer = MaritimeAnalyzer()
    
    # 4. INITIALISATION DE LA CAMÉRA
    print("[MAIN] Démarrage du flux vidéo...")
    cap = FastCamera(0, 1280, 720) # Modifie le 0 par la bonne source si besoin
    time.sleep(1.0) # Laisse le temps au capteur de s'adapter à la lumière
    
    if not cap.isOpened():
        print("[MAIN] ERREUR FATALE : Caméra non détectée. Arrêt.")
        ser.close()
        return

    print("[MAIN] Système TIPHON opérationnel et en cours d'inférence !")
    
    last_heartbeat_time = time.time()
    pending_alerts = [] 
    current_fps = 0.0

    try:
        while cap.isOpened():
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # --- ANALYSE GPU ---
            ships, _, _ = analyzer.process_frame(frame, draw_output=False)

            # --- LECTURE UART NON-BLOQUANTE ---
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode(errors='ignore').strip()
                    if line:
                        if '"cmd": "STOP"' in line:
                            print("[MAIN] Ordre STOP reçu du serveur.")
                            break 
                        
                        if '"type": "ack"' in line:
                            resp = json.loads(line)
                            ack_id = resp.get("id")
                            pending_alerts = [a for a in pending_alerts if a['id'] != ack_id]
                except:
                    pass

            # --- GESTION DES CIBLES ---
            for s in ships:
                tid = s["id"]
                if s["class"] in ALERT_CLASSES and tid not in analyzer.alert_sent_ids:
                    print(f"[ALERTE] Cible confirmée : {s['class']} (ID:{tid})")
                    img_b64 = analyzer.get_alert_image_base64(frame, s["bbox"])
                    if img_b64:
                        pending_alerts.append({
                            "id": tid, "cl": s["class"], "d": s["distance"], "img": img_b64
                        })
                        analyzer.alert_sent_ids.add(tid)

            # --- CALCUL FPS ---
            now = time.time()
            loop_time = now - start_time
            if loop_time > 0:
                current_fps = (current_fps * 0.9) + ((1.0 / loop_time) * 0.1)

            # --- ENVOI DES ALERTES ---
            if pending_alerts:
                payload = {"f": round(current_fps, 1), "alerts": [pending_alerts[0]]}
                try:
                    ser.write((json.dumps(payload) + "\n").encode('utf-8'))
                except:
                    pass
            
            # --- TÉLÉMÉTRIE ---
            if now - last_heartbeat_time > 2.0:
                cpu_temp, gpu_temp = get_jetson_stats()
                heartbeat = {
                    "type": "heartbeat",
                    "status": "active",
                    "fps": round(current_fps, 1),
                    "cpu": cpu_temp,
                    "gpu": gpu_temp
                }
                try:
                    ser.write((json.dumps(heartbeat) + "\n").encode('utf-8'))
                    ser.flush()
                    last_heartbeat_time = now
                except:
                    pass

    finally:
        print("[MAIN] Nettoyage et arrêt...")
        cap.release()
        ser.close()
        print("[MAIN] Terminé. Retour au Launcher.")

if __name__ == "__main__":
    main()