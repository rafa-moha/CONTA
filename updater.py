import os
import time
import requests
import subprocess
import sys

# --- CONFIGURATION ---
SERVER_URL = "https://twinz.ct.ws/compta_update/" # Change ceci !
FILES_TO_UPDATE = [
    "main.py",
    "src/database.py",
    "src/metier.py",
    "src/rapports.py",
    "version.txt"

]
MAIN_APP = "main.py"

def update():
    print("⏳ Attente de la fermeture de l'application...")
    time.sleep(2) # On attend 2 secondes que main.py se ferme complètement

    print("🚀 Démarrage de la mise à jour...")
    
    for filename in FILES_TO_UPDATE:
        url = f"{SERVER_URL}/{filename}"
        print(f"⬇️ Téléchargement : {filename}...")
        
        try:
            # Téléchargement du fichier
            response = requests.get(url)
            if response.status_code == 200:
                # On écrit le fichier (en écrasant l'ancien)
                with open(filename, "wb") as f:
                    f.write(response.content)
            else:
                print(f"❌ Erreur téléchargement {filename} (Code {response.status_code})")
        except Exception as e:
            print(f"❌ Erreur : {e}")

    print("✅ Mise à jour terminée !")
    print("🔄 Relancement de l'application...")
    
    # Relancer l'application principale
    if sys.platform == "win32":
        os.system(f'start python {MAIN_APP}')
    else:
        os.system(f'python3 {MAIN_APP} &')

if __name__ == "__main__":
    update()