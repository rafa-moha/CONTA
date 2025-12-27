from src.database import DatabaseManager

class Comptabilite:
    def __init__(self, nom_entreprise):
        self.nom_entreprise = nom_entreprise
        self.db = DatabaseManager(f"{nom_entreprise}.db")

    def saisir_operation(self, date, lib, mt, deb, cred, ref):
        lignes = [
            {"libelle": lib, "compte": deb, "debit": mt, "credit": 0, "ref": ref},
            {"libelle": lib, "compte": cred, "debit": 0, "credit": mt, "ref": ref}
        ]
        return self.saisir_ecriture_complexe(date, lignes)

    def saisir_ecriture_complexe(self, date, lignes):
        td = sum(l['debit'] for l in lignes)
        tc = sum(l['credit'] for l in lignes)
        
        # Vérification équilibre écriture
        if abs(td - tc) > 0.01: 
            return False
            
        try:
            for l in lignes:
                self.db.ajouter_ligne(date, l['libelle'], l['compte'], l['debit'], l['credit'], l.get('ref',''))
            return True
        except: 
            return False

    def calculer_resultat_net(self):
        """ Calcule (Produits - Charges) """
        # Classe 7 (Produits) = Créditeur
        d7, c7 = self.db.solde_compte_commencant_par('7')
        total_produits = c7 - d7
        
        # Classe 6 (Charges) = Débiteur
        d6, c6 = self.db.solde_compte_commencant_par('6')
        total_charges = d6 - c6
        
        return total_produits - total_charges

    def obtenir_donnees_bilan_detaille(self):
        """ 
        Génère le Bilan Actif / Passif équilibré.
        Logique :
        - Actif : Classes 2, 3 et 5 (si solde débiteur)
        - Passif : Classes 1, 4 et 5 (si solde créditeur) + RÉSULTAT NET
        """
        
        # 1. Récupérer tous les comptes de bilan (Classes 1 à 5)
        # On prend tout d'un coup pour trier nous-mêmes
        raw_data = self.db.recuperer_soldes_par_classe(['1', '2', '3', '4', '5'])
        
        lignes_actif = []
        totaux_actif = {"brut": 0, "amort": 0, "net": 0}
        
        lignes_passif = []
        total_passif = 0

        # 2. Trier chaque compte : Est-il Actif ou Passif ?
        for compte, debit, credit in raw_data:
            compte_str = str(compte)
            solde = debit - credit
            
            # --- CAS ACTIF (Solde Débiteur ou Classe 2/3) ---
            # Si c'est classe 2 ou 3, c'est forcément Actif (même si solde 0)
            # Si c'est classe 5 et que le solde est positif (Banque positive), c'est Actif
            if compte_str.startswith(('2', '3')) or (compte_str.startswith('5') and solde >= 0):
                # Actif
                brut = debit
                amort = credit if compte_str.startswith('2') else 0 # Simplification: amortissement souvent au crédit des comptes d'immo
                # Correction pour affichage propre : si compte 28xxx (Amortissement), c'est spécial, mais restons simple
                
                # Pour l'affichage simple : Net = Solde
                net = solde
                
                if abs(net) > 0.001 or brut > 0:
                    lignes_actif.append({
                        "compte": compte,
                        "brut": brut,
                        "amort": amort if solde > 0 else 0, # On affiche amort seulement si pertinent
                        "net": net
                    })
                    totaux_actif["brut"] += brut
                    totaux_actif["amort"] += amort
                    totaux_actif["net"] += net

            # --- CAS PASSIF (Solde Créditeur ou Classe 1/4) ---
            # Si c'est classe 1 ou 4, c'est Passif
            # Si c'est classe 5 et solde négatif (Découvert bancaire), c'est Passif
            elif compte_str.startswith(('1', '4')) or (compte_str.startswith('5') and solde < 0):
                # Passif : Le montant est (Crédit - Débit)
                net_passif = credit - debit
                
                if abs(net_passif) > 0.001:
                    lignes_passif.append({
                        "compte": compte,
                        "net": net_passif
                    })
                    total_passif += net_passif

        # 3. LE POINT CRUCIAL : AJOUTER LE RÉSULTAT AU PASSIF
        resultat_net = self.calculer_resultat_net()
        
        # On l'ajoute toujours au passif (Capitaux propres)
        # S'il est positif (Bénéfice) -> Augmente le passif
        # S'il est négatif (Perte) -> Diminue le passif (apparaît en moins)
        lignes_passif.append({
            "compte": "RÉSULTAT NET", 
            "net": resultat_net
        })
        total_passif += resultat_net

        # 4. Vérification d'équilibre (Optionnel pour debug, mais utile)
        diff = totaux_actif['net'] - total_passif
        if abs(diff) > 0.01:
            print(f"ATTENTION : Écart de bilan détecté : {diff}")
            # On pourrait ajouter une ligne "Écart de conversion" si besoin, mais restons carrés.

        return lignes_actif, totaux_actif, lignes_passif, total_passif

    def fermer(self):
        self.db.close()
