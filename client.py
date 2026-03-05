import serial
import time
import os

ser = serial.Serial('/dev/ttyTHS1', 115200, timeout=0.1)

def send_text(message):
    # On s'assure que TXT: est là une seule fois et qu'il y a un \n à la fin
    payload = f"TXT:{message}\n".encode()
    ser.write(payload)
    ser.flush() # Force l'envoi des données
    print(f"Texte envoyé au PC : {message}")

def send_image(file_path):
    if not os.path.exists(file_path):
        print(f"Erreur : {file_path} introuvable")
        return

    filesize = os.path.getsize(file_path)

    header = f"IMG:{filesize}\n".encode()
    ser.write(header)
    ser.flush()
    time.sleep(0.2) 

    print(f"Envoi de l'image ({filesize} octets)...")
    with open(file_path, "rb") as f:
        # envoi par blocs de 1024 octets
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            ser.write(chunk)
    
    ser.write(b"\n")
    ser.flush()
    print("Image envoyée avec succès.")

def answer_command(command):
    ans = ""
    if command == "photo":
        ans =  "logo_tiphon.jpg"
    elif command == "status":
        ans = "Jetson Orin Nano Online et Connectee"
    elif command == "help":
        ans = "Commandes disponibles : photo, status, help"
    else:
        ans = f"Commande inconnue : {command}"
    return ans

print("Système prêt. En attente de commandes du PC (PHOTO ou STATUS)...")

try:
    while True:
        if ser.in_waiting > 0:
            # On lit la ligne envoyée par le bouton "Envoyer" du PC
            try:
                raw_data = ser.readline()
                commande = raw_data.decode(errors='ignore').strip()
                
                if not commande:
                    continue

                print(f"Commande reçue du Web : {commande}")
                
                response = answer_command(commande)
                if response.endswith(".jpg"):
                    send_image(response)
                else:
                    send_text(response)
                    
            except Exception as e:
                print(f"Erreur lecture UART : {e}")
        
        time.sleep(0.01) # Petit repos CPU

except KeyboardInterrupt:
    print("Arrêt du script...")
    ser.close()