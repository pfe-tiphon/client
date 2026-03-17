import cv2
import numpy as np
import time
import os
import base64
from ultralytics import YOLO
from config import *

class MaritimeAnalyzer:
    def __init__(self):
        self.prev_time = time.time()
        self.class_cache = {} 
        self.alert_sent_ids = set()  
        
        # 1. Chargement UNIQUE au démarrage
        self.modelA = None
        self.modelB = None
        self.modelC = None
        self.load_models()
        
        # Pour éviter de re-classifier le même objet à chaque frame
        self.last_fine_classification = {} # tid: time

    def load_models(self):
        """Charge les 3 moteurs TensorRT sur le GPU"""
        print("[AI] Initialisation des moteurs TensorRT...")
        try:
            # Modèle A (Général + Tracking)
            pathA = ENGINE_A_PATH if os.path.exists(ENGINE_A_PATH) else MODEL_A_PATH
            self.modelA = YOLO(pathA, task="detect")
            
            # Modèle B (Militaire vs Commerce)
            pathB = ENGINE_B_PATH if os.path.exists(ENGINE_B_PATH) else MODEL_B_PATH
            self.modelB = YOLO(pathB, task="detect")
            
            # Modèle C (Type précis)
            pathC = ENGINE_C_PATH if os.path.exists(ENGINE_C_PATH) else MODEL_C_PATH
            self.modelC = YOLO(pathC, task="detect")
            
            print("[AI] Les 3 modèles sont chargés sur le GPU (Device 0).")
        except Exception as e:
            print(f"[ERREUR] Chargement modèles : {e}")

    def process_frame(self, frame, draw_output=False):
        now = time.time()
        fps = 1.0 / (now - self.prev_time) if (now - self.prev_time) > 0 else 0
        self.prev_time = now

        # --- ÉTAPE 1 : DETECTION & TRACKING (MODÈLE A) ---
        # On force imgsz=640 pour la vitesse, même si la source est 1080p
        results = self.modelA.track(frame, persist=True, conf=CONF_THRESHOLD_A, 
                                   tracker="bytetrack.yaml", device=0, imgsz=640, verbose=False)[0]
        
        final_ships = []
        
        if results and getattr(results.boxes, "id", None) is not None:
            boxes = results.boxes.xyxy.cpu().numpy()
            ids = results.boxes.id.int().cpu().numpy()
            cls_a = results.boxes.cls.int().cpu().numpy()
            
            for b, tid, ca in zip(boxes, ids, cls_a):
                tid = int(tid)
                current_class = modelA_names[ca]
                
                # --- ÉTAPE 2 : CLASSIFICATION FINE (MODÈLES B & C) ---
                # On ne lance l'analyse que si c'est un "Bateau" et qu'on ne l'a pas fait récemment
                if current_class == "Bateau":
                    # Si pas en cache OU si la dernière analyse date de plus de 2 secondes
                    if tid not in self.class_cache or (now - self.last_fine_classification.get(tid, 0) > 2.0):
                        x1, y1, x2, y2 = map(int, b)
                        crop = frame[max(0,y1):y2, max(0,x1):x2]
                        
                        if crop.size > 0:
                            # Appel synchrone (plus stable que le ThreadPool sur Jetson)
                            new_label = self._do_heavy_analysis(crop)
                            if new_label:
                                self.class_cache[tid] = new_label
                                self.last_fine_classification[tid] = now
                    
                    current_class = self.class_cache.get(tid, "Bateau")

                # Calcul distance
                h_box = max(1, b[3] - b[1])
                dist = (boat_heights.get(current_class, REAL_BOAT_HEIGHT) * 800) / h_box
                
                final_ships.append({
                    "id": tid,
                    "class": current_class,
                    "distance": round(dist, 1),
                    "bbox": [int(x) for x in b]
                })

        return final_ships, fps, None

    def _do_heavy_analysis(self, crop):
        """Chaîne les modèles B et C sur un crop d'image"""
        try:
            # Modèle B
            resB = self.modelB(crop, conf=CONF_THRESHOLD_B, device=0, verbose=False)[0]
            if len(resB.boxes) > 0:
                cls_id_b = int(resB.boxes.cls[0])
                label_b = modelB_names[cls_id_b]
                
                # Modèle C (si nécessaire)
                if label_b in ["Militaire", "Commerce", "Loisir"]:
                    resC = self.modelC(crop, conf=CONF_THRESHOLD_C, device=0, verbose=False)[0]
                    if len(resC.boxes) > 0:
                        cls_id_c = int(resC.boxes.cls[0])
                        return modelC_names[cls_id_c]
                
                return label_b
        except:
            pass
        return None

    # --- TES AUTRES FONCTIONS (CONSERVÉES POUR PLUS TARD) ---
    def get_alert_image_base64(self, frame, bbox):
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        crop = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
        if crop.size == 0: return None
        resized = cv2.resize(crop, (ALERT_IMAGE_WIDTH, 240))
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buffer).decode('utf-8')

    def _compute_ancestors_map(self, m):
        # Ta logique de map...
        return {}

    def iou(self, a, b):
        return 0