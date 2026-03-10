import serial
import time
import os
import threading

class JetsonBridge:
    def __init__(self, port='/dev/ttyTHS0', baudrate=115200):
        self.baudrate = baudrate
        self.port = port
        self.start_time = time.time()
        self.total_bytes_sent = 0
        self.lock = threading.Lock()  # Verrou pour protéger l'accès au port série
        self.running = True

        try:
            # On met un timeout=None pour que readline() soit réellement bloquant
            # Cela économise 100% des ressources CPU par rapport au polling
            self.ser = serial.Serial(port, baudrate, timeout=1) 
            print(f"Liaison UART établie sur {port} à {baudrate} bauds.")
        except Exception as e:
            print(f"Erreur d'ouverture du port : {e}")
            self.ser = None

    # --- MÉTHODES D'ENVOI (SÉCURISÉES PAR LOCK) ---

    def send_text(self, message):
        if not self.ser: return
        payload = f"TXT:{message}\n".encode()
        with self.lock: # On attend que le port soit libre
            self.ser.write(payload)
            self.ser.flush()
            self.total_bytes_sent += len(payload)

    def send_image(self, file_path):
        if not self.ser or not os.path.exists(file_path):
            return
        
        filesize = os.path.getsize(file_path)
        header = f"IMG:{filesize}\n".encode()
        
        with self.lock: # Verrouille le port pendant TOUT l'envoi de l'image
            # 1. Envoi du header
            self.ser.write(header)
            self.ser.flush()
            time.sleep(0.1) # Petit délai pour laisser le récepteur se préparer

            # 2. Envoi du flux binaire
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk: break
                    self.ser.write(chunk)
                    self.total_bytes_sent += len(chunk)
            
            self.ser.write(b"\n")
            self.ser.flush()
            print(f"[UART ->] Image envoyée : {file_path} ({filesize} octets)")

    # --- GESTION DU "PSEUDO-INTERRUPT" (THREADING) ---

    def start_background_listener(self, callback_dict):
        """Lance l'écouteur de commandes dans un thread séparé."""
        self.listener_thread = threading.Thread(
            target=self._listener_loop, 
            args=(callback_dict,), 
            daemon=True # Le thread meurt quand le programme s'arrête
        )
        self.listener_thread.start()
        print("[BRIDGE] Écouteur en arrière-plan démarré.")

    def _listener_loop(self, callback_dict):
        """Boucle interne du thread qui attend les commandes."""
        while self.running:
            try:
                if self.ser and self.ser.is_open:
                    # On bloque ici jusqu'à recevoir un '\n'
                    raw_data = self.ser.readline()
                    
                    if not raw_data:
                        continue
                        
                    command = raw_data.decode(errors='ignore').strip().lower()
                    
                    if command:
                        print(f"[UART <- CMD] {command}")
                        if command in callback_dict:
                            # Exécution de la fonction associée
                            callback_dict[command]()
                        else:
                            self.send_text(f"Commande inconnue : {command}")
                else:
                    time.sleep(1) # Si port fermé, on attend avant de retenter
            except Exception as e:
                print(f"Erreur dans l'écouteur UART : {e}")
                time.sleep(1)

    # --- UTILITAIRES ---

    def get_stats(self):
        uptime_sec = time.time() - self.start_time
        debit_moyen = (self.total_bytes_sent / 1024) / uptime_sec if uptime_sec > 0 else 0
        return (f"STATS | Port: {self.port} | Debit: {debit_moyen:.2f} KB/s | "
                f"Total: {self.total_bytes_sent / 1024:.1f} KB | Uptime: {int(uptime_sec)}s")

    def close(self):
        self.running = False
        if self.ser:
            self.ser.close()
            print("Port UART fermé.")