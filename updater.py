import os
import time
import requests
import subprocess
import sys

# Ton dépôt GitHub (Basé sur ton message d'erreur)
SERVER = "https://raw.githubusercontent.com/rafa-moha/CONTA/refs/heads/main"

FILES = [
    "main.py", 
    "src/metier.py", 
    "src/rapports.py", 
    "src/database.py", 
    "src/ui_effects.py",
    "version.txt"
]

if __name__ == "__main__":
    print("⏳ Fermeture de l'application...")
    time.sleep(2) 
    
    print("🚀 Début de la mise à jour...")
    
    for f in FILES:
        try:
            # 1. On génère le timestamp pour éviter le Cache GitHub
            timestamp = int(time.time())
            
            # 2. On construit l'URL (C'est ici qu'il y avait l'erreur)
            url = f"{SERVER}/{f}?t={timestamp}"
            
            print(f"⬇️ Téléchargement : {url}")
            
            r = requests.get(url)
            
            if r.status_code == 200:
                # Créer les dossiers si besoin (ex: src/)
                if "/" in f:
                    os.makedirs(os.path.dirname(f), exist_ok=True)
                    
                # On écrit le fichier
                with open(f, "wb") as file: 
                    file.write(r.content)
                print(f"✅ OK : {f}")
            else:
                print(f"❌ Erreur {r.status_code} sur {f}")
                
        except Exception as e: 
            print(f"❌ Erreur critique : {e}")
    
    print("🔄 Relancement...")
    if sys.platform == "win32": 
        os.system('start python main.py')
    else: 
        os.system('python3 main.py &')

