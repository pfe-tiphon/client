import os

# === CHEMINS DES MODÈLES ===
# Chemins absolus recommandés pour éviter les erreurs de fichier non trouvé sur Jetson
BASE_DIR = "/home/tiphon/Documents/tiphon_v1.0/Tiphon"
MODEL_A_PATH = os.path.join(BASE_DIR, "clientV3/best_modelA.pt")
ENGINE_A_PATH = os.path.join(BASE_DIR, "clientV3/best_modelA.engine")

MODEL_B_PATH = os.path.join(BASE_DIR, "clientV3/best_modelB.pt")
ENGINE_B_PATH = os.path.join(BASE_DIR, "clientV3/best_modelB.engine")

MODEL_C_PATH = os.path.join(BASE_DIR, "clientV3/best_modelC.pt")
ENGINE_C_PATH = os.path.join(BASE_DIR, "clientV3/best_modelC.engine")

# === SEUILS DE DÉTECTION (CONFIDENCE) ===
CONF_THRESHOLD_A = 0.45  
CONF_THRESHOLD_B = 0.50  
CONF_THRESHOLD_C = 0.60  

# === PARAMÈTRES DE TRACKING ===
MAX_TRACK_AGE = 30       
CLASS_VOTE_WINDOW = 15   
VOTE_MIN_CONFIRM = 5     
CLASSIFY_INTERVAL = 30   

# === PARAMÈTRES IMAGE ===
PROC_MAX_WIDTH = 640     
MAX_CROP_SIDE = 224      
JPEG_QUALITY = 85        

# === PHYSIQUE & CALCULS ===
REAL_BOAT_HEIGHT = 5.0   
boat_heights = {
    "Voilier": 12.0, "Cargo": 25.0, "Yacht": 8.0, 
    "Militaire": 15.0, "Fregate": 20.0, "Porte-avion": 35.0,
    "Petrolier": 22.0, "Porte-conteneur": 30.0
}

# === MAPPING DES CLASSES (YOLO) ===
modelA_names = ['Autre', 'Bateau']
modelB_names = ['Commerce', 'Militaire', 'Loisir']
modelC_names = [
    'Autre', 'Fregate', 'Patrouilleur', 'Porte-avion', 'Ravitailleur', 
    'Sous-marin', 'Porte-conteneur', 'Bateau de peche', 'Petrolier', 
    'Navire de croisiere', 'Ferry', 'Voilier', 'Bateau a moteur', 'Petit bateau'
]

# === HIÉRARCHIE (ANALOGY_MAP) ===
ANALOGY_MAP = {
    "Bateau": ['Commerce', 'Militaire', 'Loisir'],
    "Commerce": ["Porte-conteneur", "Bateau de peche", "Petrolier", "Navire de croisiere"],
    "Militaire": ["Fregate", "Patrouilleur", "Porte-avion", "Ravitailleur", "Sous-marin"],
    "Loisir": ["Navire de croisiere", "Voilier", "Ferry", "Bateau a moteur", "Petit bateau"]
}

# === CONFIGURATION DES ALERTES (SILENCE SAUF POUR CES CLASSES) ===
# Seules ces classes déclenchent un envoi UART vers l'ESP32
ALERT_CLASSES = ["Militaire", "Fregate", "Patrouilleur", "Porte-avion", "Ravitailleur", "Sous-marin"] 

# Paramètres de compression pour l'image d'alerte
ALERT_IMAGE_WIDTH = 320  
ALERT_IMAGE_QUALITY = 60 

# === COULEURS DES CLASSES (BGR) ===
class_colors = {
    "Loisir": (255, 0, 0), "Militaire": (0, 0, 255),
    "Commerce": (0, 255, 255), "Bateau": (0, 255, 0)
}

use_cuda = True