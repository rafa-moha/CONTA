import customtkinter as ctk
from tkinter import messagebox
import glob
import os
import sys
import subprocess
import requests 
import time
import webbrowser
from datetime import datetime

# --- IMPORTATION DES MODULES LOCAUX ---
# On utilise un try/except pour afficher une erreur claire si les fichiers src manquent
try:
    from src.metier import Comptabilite
    from src.rapports import GenerateurRapport
    from src.ui_effects import NotificationToast, LoadingOverlay
    from src.security import GestionnaireSecurity
except ImportError as e:
    print(f"❌ ERREUR CRITIQUE : Impossible de charger les modules 'src'.\nDétail : {e}")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit()

# --- CONFIGURATION GLOBALE ---
VERSION_ACTUELLE = "2.0.4"

# Configuration Mise à jour (GitHub Raw)
BASE_GITHUB = "https://raw.githubusercontent.com/rafa-moha/CONTA/refs/heads/main" 
URL_VERSION = f"{BASE_GITHUB}/version.txt"
URL_UPDATER = f"{BASE_GITHUB}/updater.py"

# Configuration Site Web pour l'achat
URL_ACHAT = "http://localhost/Compta.php"

# Configuration Dossiers
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- THEME ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- PLAN COMPTABLE (Base pour les menus déroulants) ---
PLAN_COMPTABLE = {
    "1111 - Capital Social": 1111,
    "1481 - Emprunts bancaires": 1481,
    "2111 - Frais préliminaires": 2111,
    "2340 - Matériel transport": 2340,
    "2351 - Mobilier bureau": 2351,
    "2352 - Matériel informatique": 2352,
    "3111 - Marchandises (Stock)": 3111,
    "3421 - Clients": 3421,
    "3455 - État TVA Récupérable": 3455,
    "4411 - Fournisseurs": 4411,
    "4455 - État TVA Facturée": 4455,
    "5141 - Banque (DH)": 5141,
    "5161 - Caisse": 5161,
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
    "7111 - Ventes marchandises": 7111,
    "7121 - Ventes produits finis": 7121
}

# =============================================================================
# FENÊTRE 1 : SAISIE SIMPLE (INTELLIGENTE)
# =============================================================================
class FenetreSaisieSimple(ctk.CTkToplevel):
    def __init__(self, parent, titre, mode, callback):
        super().__init__(parent)
        self.title(titre)
        self.geometry("550x720")
        self.callback = callback
        self.mode = mode
        
        # Préparation des listes intelligentes
        tous_comptes = sorted(PLAN_COMPTABLE.keys())
        comptes_finance = [k for k in tous_comptes if k.startswith(('5', '4411', '3421'))]
        comptes_charges = [k for k in tous_comptes if k.startswith('6')]
        comptes_produits = [k for k in tous_comptes if k.startswith('7')]

        # En-tête
        ctk.CTkLabel(self, text=f"SAISIE {mode}", font=("Arial", 22, "bold")).pack(pady=(20, 10))

        # 1. DATE
        ctk.CTkLabel(self, text="Date (AAAA-MM-JJ) :").pack(pady=(5, 2))
        self.entry_date = ctk.CTkEntry(self, width=300)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(pady=5)
        
        # 2. LIBELLÉ
        ctk.CTkLabel(self, text="Libellé / Description :").pack(pady=(10, 2))
        self.entry_lib = ctk.CTkEntry(self, width=300, placeholder_text="Ex: Facture n°...")
        self.entry_lib.pack(pady=5)
        
        # 3. MONTANT
        ctk.CTkLabel(self, text="Montant TTC (DH) :").pack(pady=(10, 2))
        self.entry_mt = ctk.CTkEntry(self, width=300, placeholder_text="0.00")
        self.entry_mt.pack(pady=5)
        
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(pady=20, padx=40, fill="x")
        
        # --- LOGIQUE INTELLIGENTE ---
        if mode == "ACHAT":
            lbl_deb, val_deb = "QUOI ? (Charge/Actif)", comptes_charges + tous_comptes
            lbl_cred, val_cred = "COMMENT ? (Paiement/Dette)", comptes_finance + tous_comptes
            defaut_deb = "6111 - Achats marchandises"
            defaut_cred = "5141 - Banque (DH)"
            c_deb, c_cred = "#E74C3C", "#2ECC71" # Rouge/Vert

        elif mode == "VENTE":
            lbl_deb, val_deb = "OÙ VA L'ARGENT ? (Banque/Client)", comptes_finance + tous_comptes
            lbl_cred, val_cred = "POURQUOI ? (Vente/Produit)", comptes_produits + tous_comptes
            defaut_deb = "5141 - Banque (DH)"
            defaut_cred = "7111 - Ventes marchandises"
            c_deb, c_cred = "#2ECC71", "#3498DB" # Vert/Bleu

        # 4. COMPTES
        ctk.CTkLabel(self, text=f"Compte DÉBIT : {lbl_deb}", text_color=c_deb, font=("Arial", 12, "bold")).pack(pady=(5, 2))
        self.menu_deb = ctk.CTkOptionMenu(self, values=val_deb, width=350)
        self.menu_deb.set(defaut_deb)
        self.menu_deb.pack(pady=5)
        
        ctk.CTkLabel(self, text=f"Compte CRÉDIT : {lbl_cred}", text_color=c_cred, font=("Arial", 12, "bold")).pack(pady=(10, 2))
        self.menu_cred = ctk.CTkOptionMenu(self, values=val_cred, width=350)
        self.menu_cred.set(defaut_cred)
        self.menu_cred.pack(pady=5)
        
        # 5. REF
        ctk.CTkLabel(self, text="Référence (Optionnel) :").pack(pady=(15, 2))
        self.entry_ref = ctk.CTkEntry(self, width=300)
        self.entry_ref.pack(pady=5)
        
        ctk.CTkButton(self, text="VALIDER", command=self.valider, height=45, 
                      font=("Arial", 14, "bold"), fg_color="green").pack(pady=30)

    def valider(self):
        try:
            d = self.entry_date.get()
            l = self.entry_lib.get()
            m = float(self.entry_mt.get().replace(",", ".")) # Fix virgule
            
            nd = self.menu_deb.get()
            nc = self.menu_cred.get()
            cd = PLAN_COMPTABLE.get(nd, int(nd.split(" - ")[0]))
            cc = PLAN_COMPTABLE.get(nc, int(nc.split(" - ")[0]))
            
            ref = self.entry_ref.get()
            
            if not l or m <= 0: raise ValueError
            self.callback(d, l, m, cd, cc, ref)
            self.destroy()
        except: messagebox.showerror("Erreur", "Vérifiez les champs (Montant, Libellé).")

# =============================================================================
# FENÊTRE 2 : SAISIE MULTIPLE (VENTILATION)
# =============================================================================
class FenetreSaisieComplexe(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Écriture Multiple")
        self.geometry("550x450")
        self.callback = callback
        self.lignes = []
        
        frm_top = ctk.CTkFrame(self)
        frm_top.pack(fill="x", padx=10, pady=10)
        self.entry_date = ctk.CTkEntry(frm_top, width=120)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(side="left", padx=5)
        self.entry_lib_main = ctk.CTkEntry(frm_top, width=400, placeholder_text="Libellé Général")
        self.entry_lib_main.pack(side="left", fill="x", expand=True, padx=5)
        
        frm_add = ctk.CTkFrame(self)
        frm_add.pack(fill="x", padx=10)
        self.menu_cpt = ctk.CTkOptionMenu(frm_add, values=sorted(PLAN_COMPTABLE.keys()), width=300)
        self.menu_cpt.pack(side="left", padx=5, pady=10)
        self.ent_d = ctk.CTkEntry(frm_add, width=100, placeholder_text="Débit")
        self.ent_d.pack(side="left", padx=5)
        self.ent_c = ctk.CTkEntry(frm_add, width=100, placeholder_text="Crédit")
        self.ent_c.pack(side="left", padx=5)
        ctk.CTkButton(frm_add, text="+", width=50, command=self.ajouter).pack(side="left", padx=5)
        
        self.scroll = ctk.CTkScrollableFrame(self, height=300)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        frm_bot = ctk.CTkFrame(self, height=60)
        frm_bot.pack(fill="x", side="bottom")
        self.lbl_stat = ctk.CTkLabel(frm_bot, text="D: 0.00 | C: 0.00", font=("Arial", 14, "bold"))
        self.lbl_stat.pack(side="left", padx=20)
        self.btn_ok = ctk.CTkButton(frm_bot, text="VALIDER", state="disabled", fg_color="gray", command=self.valider_tout)
        self.btn_ok.pack(side="right", padx=20, pady=15)

    def ajouter(self):
        try:
            d = float(self.ent_d.get() or 0)
            c = float(self.ent_c.get() or 0)
            txt = self.menu_cpt.get()
            if d==0 and c==0: return
            
            self.lignes.append({"compte": PLAN_COMPTABLE[txt], "nom": txt, "debit": d, "credit": c, "ref": ""})
            
            row = ctk.CTkFrame(self.scroll, height=30)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{txt} | D: {d} | C: {c}", anchor="w").pack(side="left", padx=10)
            
            self.ent_d.delete(0, "end"); self.ent_c.delete(0, "end"); self.calculer()
        except: pass

    def calculer(self):
        td = sum(l['debit'] for l in self.lignes)
        tc = sum(l['credit'] for l in self.lignes)
        self.lbl_stat.configure(text=f"D: {td:.2f} | C: {tc:.2f}")
        if abs(td-tc) < 0.01 and td > 0:
            self.btn_ok.configure(state="normal", fg_color="green")
        else:
            self.btn_ok.configure(state="disabled", fg_color="gray")

    def valider_tout(self):
        d, l = self.entry_date.get(), self.entry_lib_main.get()
        if not l: return
        final = [{"date": d, "libelle": l, "compte": i['compte'], "debit": i['debit'], "credit": i['credit'], "ref": ""} for i in self.lignes]
        self.callback(d, final)
        self.destroy()

# =============================================================================
# FENÊTRE D'ACTIVATION (SÉCURISÉE)
# =============================================================================
class FenetreActivation(ctk.CTkToplevel):
    def __init__(self, parent, security_manager, callback_succes):
        super().__init__(parent)
        self.title("ACTIVATION REQUISE")
        self.geometry("500x480")
        self.security = security_manager
        self.callback = callback_succes
        
        self.transient(parent); self.grab_set()

        ctk.CTkLabel(self, text="🔒 FONCTIONNALITÉ BLOQUÉE", font=("Arial", 22, "bold"), text_color="#E74C3C").pack(pady=(30, 5))
        ctk.CTkLabel(self, text="Exports réservés à la version PRO.", font=("Arial", 14)).pack(pady=5)
        
        ctk.CTkFrame(self, height=2, fg_color="gray").pack(fill="x", padx=40, pady=20)

        ctk.CTkLabel(self, text="1. Je n'ai pas de clé :", font=("Arial", 12, "bold")).pack()
        ctk.CTkButton(self, text="🛒 ACHETER UNE CLÉ", fg_color="#F39C12", command=lambda: webbrowser.open(URL_ACHAT)).pack(pady=5)
        
        ctk.CTkLabel(self, text="2. J'ai déjà une clé :", font=("Arial", 12, "bold")).pack(pady=(25, 5))
        self.entry_cle = ctk.CTkEntry(self, width=300, justify="center")
        self.entry_cle.pack(pady=5)
        
        ctk.CTkButton(self, text="DÉVERROUILLER", fg_color="green", command=self.verifier_cle).pack(pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.fermer_proprement)

    def verifier_cle(self):
        if self.security.tenter_activation(self.entry_cle.get()):
            messagebox.showinfo("Succès", "✅ Logiciel activé !"); self.callback(); self.fermer_proprement()
        else:
            NotificationToast(self, "Clé incorrecte", "red")
            try: self.entry_cle.delete(0, "end")
            except: pass

    def fermer_proprement(self):
        try: self.grab_release(); self.destroy()
        except: pass

# =============================================================================
# APPLICATION PRINCIPALE
# =============================================================================
class AppManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Compta Pro Maroc v{VERSION_ACTUELLE}") 
        self.geometry("480x680")
        
        self.rapports = GenerateurRapport()
        self.security = GestionnaireSecurity()
        self.compta = None; self.nom_ent = None
        
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.pack(fill="both", expand=True)
        self.accueil()

    # --- ACCUEIL ---
    def accueil(self):
        for w in self.main.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.main, text="LOGICIEL COMPTABLE", font=("Arial", 28, "bold")).pack(pady=(40, 5))
        
        scroll = ctk.CTkScrollableFrame(self.main, height=200, width=400)
        scroll.pack(pady=20)
        files = glob.glob(os.path.join(DATA_DIR, "*.db"))
        if files:
            for f in files:
                n = os.path.basename(f).replace(".db", "")
                ctk.CTkButton(scroll, text=f"📂 {n}", command=lambda x=n: self.charger(x)).pack(pady=5, fill="x")
        else:
            ctk.CTkLabel(scroll, text="Aucun dossier").pack()
            
        self.ent_new = ctk.CTkEntry(self.main, placeholder_text="Nouvelle entreprise...", width=300)
        self.ent_new.pack(pady=10)
        ctk.CTkButton(self.main, text="Créer et Ouvrir", fg_color="green", command=lambda: self.charger(self.ent_new.get())).pack()

        ctk.CTkButton(self.main, text="♻️ Vérifier Mise à jour", fg_color="#444", command=self.verifier_mise_a_jour).pack(side="bottom", pady=20)

    def charger(self, nom):
        if not nom: return
        self.compta = Comptabilite(nom.replace(" ", "_"))
        self.nom_ent = nom.replace(" ", "_")
        self.dashboard()

    # --- DASHBOARD ---
    def dashboard(self):
        for w in self.main.winfo_children(): w.destroy()
        
        # Header
        top = ctk.CTkFrame(self.main, fg_color="#222", corner_radius=0)
        top.pack(fill="x")
        ctk.CTkButton(top, text="< Changer", width=80, fg_color="transparent", border_width=1, command=self.accueil).pack(side="left", padx=15, pady=15)
        
        stat = "VERSION PRO" if self.security.est_active() else "VERSION ESSAI"
        col = "#2ECC71" if self.security.est_active() else "#E74C3C"
        ctk.CTkLabel(top, text=f"{self.nom_ent.upper()}", font=("Arial", 18, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(top, text=stat, text_color=col, font=("Arial", 11, "bold")).pack(side="right", padx=15)

        # Saisie
        ctk.CTkLabel(self.main, text="SAISIE DES OPÉRATIONS", font=("Arial", 14)).pack(pady=(30, 10))
        row_btn = ctk.CTkFrame(self.main, fg_color="transparent")
        row_btn.pack(fill="x", padx=40)
        
        ctk.CTkButton(row_btn, text="ACHAT / DÉPENSE", fg_color="#C0392B", height=50, command=lambda: self.ouvrir_simple("ACHAT")).pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_btn, text="VENTE / RECETTE", fg_color="#27AE60", height=50, command=lambda: self.ouvrir_simple("VENTE")).pack(side="right", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(self.main, text="ÉCRITURE MULTIPLE / OD", height=60, fg_color="#2980B9", command=self.ouvrir_complexe).pack(padx=40, pady=10, fill="x")
        
        ctk.CTkFrame(self.main, height=2, fg_color="gray").pack(pady=30, padx=40, fill="x")
        
        # Exports (Sécurisés)
        ctk.CTkLabel(self.main, text="RAPPORTS & EXPORTS", font=("Arial", 14)).pack(pady=(0, 10))
        row_exp = ctk.CTkFrame(self.main, fg_color="transparent")
        row_exp.pack(fill="x", padx=40)
        
        lock = "" if self.security.est_active() else "🔒 "
        col_btn = "#3B8ED0" if self.security.est_active() else "#555"

        ctk.CTkButton(row_exp, text=f"{lock}Excel", fg_color=col_btn, command=self.export_excel).pack(side="left", fill="x", expand=True, padx=5)
        
        # BOUTON BILAN PRO
        ctk.CTkButton(row_exp, text=f"{lock}Bilan (Pro)", fg_color=col_btn, command=self.export_pdf_bilan).pack(side="left", fill="x", expand=True, padx=5)
        
        # BOUTON JOURNAL PRO (Orange)
        ctk.CTkButton(row_exp, text=f"{lock}Livre Journal (Pro)", fg_color="#F39C12" if self.security.est_active() else "#555", 
                      command=self.export_pdf_journal).pack(side="left", fill="x", expand=True, padx=5)

    # --- ACTIONS ---
    def ouvrir_simple(self, mode):
        FenetreSaisieSimple(self, f"Saisie {mode}", mode, self.sauver_simple)

    def ouvrir_complexe(self):
        FenetreSaisieComplexe(self, self.sauver_complexe)

    def sauver_simple(self, d, l, m, deb, cred, ref):
        ok = self.compta.saisir_operation(d, l, m, deb, cred, ref)
        self.msg(ok, f"Enregistré : {l}")

    def sauver_complexe(self, d, lignes):
        ok = self.compta.saisir_ecriture_complexe(d, lignes)
        self.msg(ok, f"Ventilation enregistrée")

    def msg(self, succes, txt):
        if succes: NotificationToast(self, f"✅ {txt}", "green")
        else: NotificationToast(self, "❌ Erreur / Déséquilibré", "red")

    # --- EXPORTS & SÉCURITÉ ---
    def verifier_droit_export(self):
        if self.security.est_active(): return True
        FenetreActivation(self, self.security, self.rafraichir_apres_activation)
        return False

    def rafraichir_apres_activation(self):
        self.dashboard()
        NotificationToast(self, "Merci ! Exports débloqués.", "green")

    def export_excel(self):
        if not self.verifier_droit_export(): return
        LoadingOverlay(self, "Excel...")
        self.update(); self.after(500)
        
        p = self.rapports.exporter_journal_excel(self.compta.db.recuperer_journal(), self.nom_ent)
        self.fin_export(p)

    def export_pdf_bilan(self):
        if not self.verifier_droit_export(): return
        LoadingOverlay(self, "Génération Bilan Pro...")
        self.update(); self.after(500)
        
        la, ta, lp, tp = self.compta.obtenir_donnees_bilan_detaille()
        p = self.rapports.generer_bilan_pdf(self.nom_ent, la, ta, lp, tp)
        self.fin_export(p)

    def export_pdf_journal(self):
        if not self.verifier_droit_export(): return
        LoadingOverlay(self, "Génération Livre Journal Pro...")
        self.update(); self.after(500)
        
        data = self.compta.db.recuperer_journal()
        p = self.rapports.generer_journal_pdf_style(self.nom_ent, data)
        self.fin_export(p)

    def fin_export(self, path):
        for c in self.winfo_children(): 
            if isinstance(c, LoadingOverlay): c.close()
            
        if path: 
            NotificationToast(self, "Fichier généré !", "blue")
            os.startfile(os.path.dirname(path))
        else: 
            messagebox.showerror("Erreur", "Echec de l'exportation.")

    # --- MISE À JOUR ---
    def verifier_mise_a_jour(self):
        try:
            ts = int(time.time())
            url = f"{URL_VERSION}?t={ts}"
            print(f"Check: {url}")
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                v_serv = r.text.strip()
                if v_serv > VERSION_ACTUELLE:
                    if messagebox.askyesno("Mise à jour", f"Version {v_serv} disponible.\nInstaller ?"):
                        r2 = requests.get(f"{URL_UPDATER}?t={ts}")
                        with open("updater.py", "wb") as f: f.write(r2.content)
                        if sys.platform=="win32": subprocess.Popen(["python", "updater.py"], shell=True)
                        else: subprocess.Popen(["python3", "updater.py"])
                        self.destroy(); sys.exit()
                else: NotificationToast(self, "Vous êtes à jour.", "blue")
            else: NotificationToast(self, f"Erreur Serveur {r.status_code}", "red")
        except Exception as e: messagebox.showerror("Erreur", f"Connexion impossible: {e}")

if __name__ == "__main__":
    app = AppManager()
    app.mainloop()

