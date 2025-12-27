import os, time, requests, subprocess, sys

# Remplace par ton lien de base GitHub Raw
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
            url = f"{SERVER}/{f}"
            print(f"⬇️ Téléchargement : {url}")
            
            # GitHub accepte les requêtes directes sans User-Agent complexe
            r = requests.get(url)
            
            if r.status_code == 200:
                # Créer les dossiers si besoin
                if "/" in f:
                    os.makedirs(os.path.dirname(f), exist_ok=True)
                    
                with open(f, "wb") as file: 
                    file.write(r.content)
                print(f"✅ OK : {f}")
            else:
                print(f"❌ Erreur {r.status_code} sur {f}")
        except Exception as e: 
            print(f"❌ Erreur : {e}")
    
    print("🔄 Relancement...")
    if sys.platform == "win32": os.system('start python main.py')
    else: os.system('python3 main.py &')
