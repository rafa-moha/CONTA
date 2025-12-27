import customtkinter as ctk
from tkinter import messagebox
import glob
import os
import sys
import subprocess
import requests 
import time  # <--- AJOUTE CETTE LIGNE ICI (C'EST ELLE QUI MANQUAIT)
from datetime import datetime

# --- IMPORTATION DES MODULES LOCAUX ---
try:
    from src.metier import Comptabilite
    from src.rapports import GenerateurRapport
    from src.ui_effects import NotificationToast, LoadingOverlay
except ImportError as e:
    # On utilise print car messagebox n'est peut-être pas encore chargé si tkinter plante
    print(f"Erreur d'import : {e}")
    sys.exit()

# --- CONFIGURATION MISE À JOUR (GITHUB RAW) ---
# C'est ici que tu mets la version actuelle de ton logiciel
VERSION_ACTUELLE = "2.0.2"

# Remplace ceci par TON lien GitHub RAW (comme vu précédemment)
BASE_URL = "https://raw.githubusercontent.com/rafa-moha/CONTA/refs/heads/main"

URL_VERSION = f"{BASE_URL}/version.txt"
URL_UPDATER = f"{BASE_URL}/updater.py"

# --- CONFIGURATION DOSSIERS ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- CONFIGURATION GUI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- PLAN COMPTABLE ---
PLAN_COMPTABLE = {
    "5141 - Banque (DH)": 5141,
    "5161 - Caisse": 5161,
    "1111 - Capital Social": 1111,
    "1481 - Emprunts bancaires": 1481,
    "2111 - Frais préliminaires": 2111,
    "2340 - Matériel transport": 2340,
    "2351 - Mobilier bureau": 2351,
    "2352 - Matériel informatique": 2352,
    "6111 - Achats marchandises": 6111,
    "6121 - Achats matières premières": 6121,
    "61251 - Achats Électricité": 61251,
    "61252 - Achats Eau": 61252,
    "6131 - Location (Loyer)": 6131,
    "6142 - Transport": 6142,
    "6144 - Publicité": 6144,
    "6147 - Frais bancaires": 6147,
    "6167 - Impôts et taxes": 6167,
    "6171 - Salaires": 6171,
    "3455 - État TVA Récupérable": 3455,
    "4455 - État TVA Facturée": 4455,
    "4411 - Fournisseurs": 4411,
    "3421 - Clients": 3421,
    "7111 - Ventes marchandises": 7111,
    "7121 - Ventes produits finis": 7121
}

# =============================================================================
# FENÊTRE 1 : SAISIE SIMPLE
# =============================================================================
class FenetreSaisieSimple(ctk.CTkToplevel):
    def __init__(self, parent, titre, mode, callback):
        super().__init__(parent)
        self.title(titre)
        self.geometry("500x650")
        self.callback = callback
        self.liste_triee = sorted(PLAN_COMPTABLE.keys())
        
        ctk.CTkLabel(self, text="Date (AAAA-MM-JJ) :").pack(pady=(15, 5))
        self.entry_date = ctk.CTkEntry(self, width=300)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(pady=5)
        
        ctk.CTkLabel(self, text="Libellé / Description :").pack(pady=5)
        self.entry_lib = ctk.CTkEntry(self, width=300)
        self.entry_lib.pack(pady=5)
        
        ctk.CTkLabel(self, text="Montant Total (DH) :").pack(pady=5)
        self.entry_mt = ctk.CTkEntry(self, width=300)
        self.entry_mt.pack(pady=5)
        
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(pady=15, padx=40, fill="x")
        
        ctk.CTkLabel(self, text="Compte DÉBIT (Entrée/Charge)", text_color="#55FF55").pack()
        self.menu_deb = ctk.CTkOptionMenu(self, values=self.liste_triee, width=300, fg_color="#225522", command=self.verifier_type_paiement)
        self.menu_deb.pack(pady=5)
        
        ctk.CTkLabel(self, text="Compte CRÉDIT (Sortie/Produit)", text_color="#FF5555").pack()
        self.menu_cred = ctk.CTkOptionMenu(self, values=self.liste_triee, width=300, fg_color="#552222", command=self.verifier_type_paiement)
        self.menu_cred.pack(pady=5)
        
        self.lbl_ref = ctk.CTkLabel(self, text="N° Reçu / Facture :", text_color="orange")
        self.lbl_ref.pack(pady=(15, 5))
        self.entry_ref = ctk.CTkEntry(self, width=300, placeholder_text="Optionnel")
        self.entry_ref.pack(pady=5)
        
        if mode == "ACHAT":
            self.menu_deb.set("6111 - Achats marchandises")
            self.menu_cred.set("5141 - Banque (DH)")
        elif mode == "VENTE":
            self.menu_deb.set("5141 - Banque (DH)")
            self.menu_cred.set("7111 - Ventes marchandises")
            
        self.verifier_type_paiement(None)
        ctk.CTkButton(self, text="VALIDER", command=self.valider, height=40, font=("Arial", 14, "bold")).pack(pady=30)

    def verifier_type_paiement(self, choix):
        val_deb = self.menu_deb.get()
        val_cred = self.menu_cred.get()
        if "5141" in val_deb or "5141" in val_cred:
            self.lbl_ref.configure(text="Numéro de Chèque / Virement :")
            self.entry_ref.configure(placeholder_text="Ex: CHQ-890221")
        else:
            self.lbl_ref.configure(text="Numéro de Reçu / Facture / Pièce :")
            self.entry_ref.configure(placeholder_text="Ex: FAC-2023-001")

    def valider(self):
        try:
            d = self.entry_date.get()
            l = self.entry_lib.get()
            m = float(self.entry_mt.get())
            cd = PLAN_COMPTABLE[self.menu_deb.get()]
            cc = PLAN_COMPTABLE[self.menu_cred.get()]
            ref = self.entry_ref.get()
            if not l: raise ValueError
            self.callback(d, l, m, cd, cc, ref)
            self.destroy()
        except: messagebox.showerror("Erreur", "Champs invalides (Vérifiez le montant).")


# =============================================================================
# FENÊTRE 2 : SAISIE MULTIPLE
# =============================================================================
class FenetreSaisieComplexe(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Écriture Multiple / Ventilation")
        self.geometry("750x650")
        self.callback = callback
        self.lignes = []
        self.liste_triee = sorted(PLAN_COMPTABLE.keys())
        
        frm_top = ctk.CTkFrame(self)
        frm_top.pack(fill="x", padx=10, pady=10)
        
        self.entry_date = ctk.CTkEntry(frm_top, width=120)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(side="left", padx=5)
        self.entry_lib_main = ctk.CTkEntry(frm_top, width=400, placeholder_text="Libellé Général")
        self.entry_lib_main.pack(side="left", fill="x", expand=True, padx=5)
        
        frm_add = ctk.CTkFrame(self)
        frm_add.pack(fill="x", padx=10)
        
        self.menu_cpt = ctk.CTkOptionMenu(frm_add, values=self.liste_triee, width=300)
        self.menu_cpt.pack(side="left", padx=5, pady=10)
        self.ent_d = ctk.CTkEntry(frm_add, width=100, placeholder_text="Débit")
        self.ent_d.pack(side="left", padx=5)
        self.ent_c = ctk.CTkEntry(frm_add, width=100, placeholder_text="Crédit")
        self.ent_c.pack(side="left", padx=5)
        ctk.CTkButton(frm_add, text="+ Ajouter", width=80, command=self.ajouter).pack(side="left", padx=5)
        
        self.scroll = ctk.CTkScrollableFrame(self, height=300)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        frm_bot = ctk.CTkFrame(self, height=60)
        frm_bot.pack(fill="x", side="bottom")
        self.lbl_d = ctk.CTkLabel(frm_bot, text="D: 0.00", font=("Arial", 14, "bold"))
        self.lbl_d.pack(side="left", padx=20)
        self.lbl_c = ctk.CTkLabel(frm_bot, text="C: 0.00", font=("Arial", 14, "bold"))
        self.lbl_c.pack(side="left", padx=20)
        self.btn_ok = ctk.CTkButton(frm_bot, text="VALIDER", state="disabled", fg_color="gray", command=self.valider_tout)
        self.btn_ok.pack(side="right", padx=20, pady=15)

    def ajouter(self):
        try:
            d = float(self.ent_d.get()) if self.ent_d.get() else 0.0
            c = float(self.ent_c.get()) if self.ent_c.get() else 0.0
            txt = self.menu_cpt.get()
            
            if d==0 and c==0: return
            self.lignes.append({"compte": PLAN_COMPTABLE[txt], "nom": txt, "debit": d, "credit": c, "ref": ""})
            
            row = ctk.CTkFrame(self.scroll, height=30)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{txt} | D: {d} | C: {c}", anchor="w").pack(side="left", padx=10)
            
            self.ent_d.delete(0, "end")
            self.ent_c.delete(0, "end")
            self.calculer()
        except ValueError: messagebox.showerror("Erreur", "Montant invalide")

    def calculer(self):
        td = sum(l['debit'] for l in self.lignes)
        tc = sum(l['credit'] for l in self.lignes)
        self.lbl_d.configure(text=f"Total Débit : {td:.2f}")
        self.lbl_c.configure(text=f"Total Crédit : {tc:.2f}")
        
        if abs(td-tc) < 0.01 and td > 0:
            self.btn_ok.configure(state="normal", fg_color="green", text="VALIDER")
        else:
            self.btn_ok.configure(state="disabled", fg_color="gray", text=f"Déséquilibré")

    def valider_tout(self):
        date = self.entry_date.get()
        lib = self.entry_lib_main.get()
        if not lib: 
            messagebox.showerror("Erreur", "Libellé manquant")
            return
        final = []
        for l in self.lignes:
            final.append({"date": date, "libelle": lib, "compte": l['compte'], "debit": l['debit'], "credit": l['credit'], "ref": ""})
        self.callback(date, final)
        self.destroy()


# =============================================================================
# APPLICATION PRINCIPALE
# =============================================================================
class AppManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        # ICI ON UTILISE LA BONNE VARIABLE
        self.title(f"Compta Pro Maroc v{VERSION_ACTUELLE}") 
        self.geometry("450x600")
        
        self.rapports = GenerateurRapport()
        self.compta = None
        self.nom_ent = None
        
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True)
        
        self.accueil()

    # --- ÉCRAN D'ACCUEIL ---
    def accueil(self):
        for w in self.main.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.main, text="LOGICIEL COMPTABLE", font=("Arial", 28, "bold")).pack(pady=(40, 10))
        ctk.CTkLabel(self.main, text=f"Version {VERSION_ACTUELLE}", text_color="gray").pack(pady=(0, 30))
        
        files = glob.glob(os.path.join(DATA_DIR, "*.db"))
        
        if files:
            scroll_home = ctk.CTkScrollableFrame(self.main, height=200, width=400)
            scroll_home.pack(pady=10)
            for f in files:
                nom_fichier = os.path.basename(f)
                n = nom_fichier.replace(".db", "")
                ctk.CTkButton(scroll_home, text=f"📂 {n}", command=lambda x=n: self.charger(x)).pack(pady=5, fill="x")
        else:
            ctk.CTkLabel(self.main, text="Aucune entreprise trouvée.").pack(pady=10)
            
        self.ent_new = ctk.CTkEntry(self.main, placeholder_text="Nom nouvelle entreprise...", width=300)
        self.ent_new.pack(pady=(30, 10))
        ctk.CTkButton(self.main, text="Créer et Ouvrir", fg_color="green", command=lambda: self.charger(self.ent_new.get())).pack()

        # Bouton Mise à jour (GitHub Raw)
        ctk.CTkButton(self.main, text="♻️ Vérifier Mise à jour (En ligne)", fg_color="#444", command=self.verifier_mise_a_jour).pack(side="bottom", pady=20)

    # --- CHARGEMENT ---
    def charger(self, nom):
        if not nom: return
        nom_propre = nom.replace(" ", "_")
        self.compta = Comptabilite(nom_propre)
        self.nom_ent = nom_propre
        self.dashboard()

    # --- DASHBOARD ---
    def dashboard(self):
        for w in self.main.winfo_children(): w.destroy()
        
        top = ctk.CTkFrame(self.main, fg_color="#222", corner_radius=0)
        top.pack(fill="x")
        ctk.CTkButton(top, text="< Changer", width=80, fg_color="transparent", border_width=1, command=self.accueil).pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(top, text=f"SOCIÉTÉ : {self.nom_ent.upper()}", font=("Arial", 18, "bold")).pack(side="left", padx=20)
        
        ctk.CTkLabel(self.main, text="SAISIE DES OPÉRATIONS", font=("Arial", 14)).pack(pady=(30, 10))
        
        row_btn = ctk.CTkFrame(self.main, fg_color="transparent")
        row_btn.pack(fill="x", padx=40)
        
        ctk.CTkButton(row_btn, text="ACHAT / DÉPENSE", fg_color="#C0392B", height=50, hover_color="#E74C3C",
                      command=lambda: self.ouvrir_simple("ACHAT")).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(row_btn, text="VENTE / RECETTE", fg_color="#27AE60", height=50, hover_color="#2ECC71",
                      command=lambda: self.ouvrir_simple("VENTE")).pack(side="right", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(self.main, text="ÉCRITURE MULTIPLE / OD", height=60, fg_color="#2980B9", font=("Arial", 13, "bold"), 
                      command=self.ouvrir_complexe).pack(padx=40, pady=10, fill="x")
        
        ctk.CTkFrame(self.main, height=2, fg_color="gray").pack(pady=30, padx=40, fill="x")
        
        ctk.CTkLabel(self.main, text="RAPPORTS & EXPORTS", font=("Arial", 14)).pack(pady=(0, 10))
        
        row_exp = ctk.CTkFrame(self.main, fg_color="transparent")
        row_exp.pack(fill="x", padx=40)
        
        ctk.CTkButton(row_exp, text="JOURNAL (Excel)", command=self.export_excel).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_exp, text="BILAN (PDF Détaillé)", command=self.export_pdf).pack(side="right", fill="x", expand=True, padx=5)

    # --- ACTIONS ---
    def ouvrir_simple(self, mode):
        FenetreSaisieSimple(self, f"Saisie {mode}", mode, self.sauver_simple)

    def ouvrir_complexe(self):
        FenetreSaisieComplexe(self, self.sauver_complexe)

    def sauver_simple(self, d, l, m, deb, cred, ref):
        ok = self.compta.saisir_operation(d, l, m, deb, cred, ref)
        self.msg(ok, f"Enregistré : {l} ({m} DH)")

    def sauver_complexe(self, d, lignes):
        ok = self.compta.saisir_ecriture_complexe(d, lignes)
        self.msg(ok, f"Écriture multiple enregistrée ({len(lignes)} lignes)")

    def msg(self, succes, txt):
        if succes:
            NotificationToast(self, f"✅ {txt}", "green")
        else:
            NotificationToast(self, "❌ Erreur lors de l'enregistrement", "red")

    def export_excel(self):
        LoadingOverlay(self, "Génération Excel...")
        self.update()
        self.after(500)
        
        data = self.compta.db.recuperer_journal()
        path = self.rapports.exporter_journal_excel(data, self.nom_ent)
        
        # On ferme le loading (Note: Idéalement LoadingOverlay devrait être détruit proprement, 
        # ici on assume qu'il est modal ou on le laisse, mais pour simplifier on le laisse se fermer 
        # avec le prochain rafraichissement ou on utilise une ref. 
        # Pour faire simple dans ce script unique :)
        for child in self.winfo_children():
            if isinstance(child, LoadingOverlay): child.close()

        if path: 
            NotificationToast(self, "Excel exporté !", "blue")
            os.startfile(os.path.dirname(path))
        else: 
            messagebox.showerror("Erreur", "Impossible de créer le fichier.")

    def export_pdf(self):
        LoadingOverlay(self, "Génération PDF...")
        self.update()
        self.after(500)
        
        l_actif, t_actif, l_passif, t_passif = self.compta.obtenir_donnees_bilan_detaille()
        path = self.rapports.generer_bilan_pdf(self.nom_ent, l_actif, t_actif, l_passif, t_passif)

        for child in self.winfo_children():
            if isinstance(child, LoadingOverlay): child.close()

        if path: 
            NotificationToast(self, "PDF généré !", "blue")
            os.startfile(os.path.dirname(path))
        else: 
            messagebox.showerror("Erreur", "Impossible de créer le PDF.")

    # --- MISE À JOUR AUTO (GITHUB) ---
    def verifier_mise_a_jour(self):
        try:
            # ASTUCE ANTI-CACHE : On ajoute "?t=..." à la fin
            timestamp = int(time.time())
            url_fraiche = f"{URL_VERSION}?t={timestamp}"
            
            print(f"Checking: {url_fraiche}")
            
            # On utilise l'URL fraîche
            r = requests.get(url_fraiche, timeout=5) 
            
            if r.status_code == 200:
                v_serv = r.text.strip()
                if v_serv > VERSION_ACTUELLE:
                    if messagebox.askyesno("Mise à jour", f"Version {v_serv} disponible.\nTélécharger maintenant ?"):
                        self.lancer_mise_a_jour()
                else:
                    NotificationToast(self, "Vous êtes à jour.", "blue")
            else:
                messagebox.showerror("Erreur", f"Erreur serveur : {r.status_code}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de joindre GitHub.\n{e}")

    def lancer_mise_a_jour(self):
        try:
            r = requests.get(URL_UPDATER)
            with open("updater.py", "wb") as f:
                f.write(r.content)
            
            if sys.platform == "win32":
                subprocess.Popen(["python", "updater.py"], shell=True)
            else:
                subprocess.Popen(["python3", "updater.py"])
            
            self.destroy()
            sys.exit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec update: {e}")

if __name__ == "__main__":
    app = AppManager()
    app.mainloop()



