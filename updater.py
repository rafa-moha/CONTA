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
            # ASTUCE ANTI-CACHE ICI AUSSI
            timestamp = int(time.time())
            # On construit l'URL avec le fichier ET le paramètre temps
            url = f"{SERVER}/{f}?t={timestamp}"
            
            print(f"⬇️ Téléchargement : {url}")
            
            r = requests.get(url)
            
            if r.status_code == 200:
                # IMPORTANT : On sauvegarde sous le vrai nom 'f' (sans le ?t=...)
                
                # Création dossier si besoin
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
