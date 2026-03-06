import serial
import time
import os

class JetsonBridge:
    def __init__(self, port='/dev/ttyTHS0', baudrate=115200):
        self.baudrate = baudrate
        self.port = port
        self.start_time = time.time()
        self.total_bytes_sent = 0
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            print(f"Liaison UART établie sur {port} à {baudrate} bauds.")
        except Exception as e:
            print(f"Erreur : {e}")
            self.ser = None

    def send_text(self, message):
        if not self.ser: return
        payload = f"TXT:{message}\n".encode()
        self.ser.write(payload)
        self.ser.flush()
        self.total_bytes_sent += len(payload)

    def send_image(self, file_path):
        if not self.ser or not os.path.exists(file_path):
            return
        
        filesize = os.path.getsize(file_path)
        header = f"IMG:{filesize}\n".encode()
        self.ser.write(header)
        self.ser.flush()
        time.sleep(0.3) 

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk: break
                self.ser.write(chunk)
                self.total_bytes_sent += len(chunk)
        
        self.ser.write(b"\n")
        self.ser.flush()

    def get_stats(self):
        uptime_sec = time.time() - self.start_time
        debit_moyen = (self.total_bytes_sent / 1024) / uptime_sec if uptime_sec > 0 else 0
        
        # On construit une chaîne unique avec des séparateurs visibles
        # Au lieu de vrais retours à la ligne qui cassent le protocole UART/PC
        stats = (
            f"STATS | Port: {self.port} | "
            f"Debit: {debit_moyen:.2f} KB/s | "
            f"Total: {self.total_bytes_sent / 1024:.1f} KB | "
            f"Uptime: {int(uptime_sec)}s"
        )
        return stats

    def check_commands(self, callback_dict):
        """
        Vérifie si une commande est reçue et exécute la fonction associée.
        callback_dict: dictionnaire { 'commande': fonction_a_executer }
        """
        if self.ser and self.ser.in_waiting > 0:
            try:
                raw_data = self.ser.readline()
                command = raw_data.decode(errors='ignore').strip().lower()
                
                if not command:
                    return

                print(f"[UART <- CMD] {command}")
                
                if command in callback_dict:
                    callback_dict[command]()
                else:
                    self.send_text(f"Commande inconnue : {command}")
            except Exception as e:
                print(f"Erreur lecture commande : {e}")

    def close(self):
        if self.ser:
            self.ser.close()