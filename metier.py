from src.database import DatabaseManager

class Comptabilite:
    def __init__(self, nom_entreprise):
        self.nom_entreprise = nom_entreprise
        self.db = DatabaseManager(f"{nom_entreprise}.db")

    def saisir_operation(self, date_op, libelle, montant, compte_debit, compte_credit, reference):
        """ Saisie simple transformée en multiple """
        lignes = [
            {"libelle": libelle, "compte": compte_debit, "debit": montant, "credit": 0, "ref": reference},
            {"libelle": libelle, "compte": compte_credit, "debit": 0, "credit": montant, "ref": reference}
        ]
        return self.saisir_ecriture_complexe(date_op, lignes)

    def saisir_ecriture_complexe(self, date_op, lignes):
        """ Saisie multiple avec vérification d'équilibre """
        total_debit = sum(l['debit'] for l in lignes)
        total_credit = sum(l['credit'] for l in lignes)

        if abs(total_debit - total_credit) > 0.01:
            return False

        try:
            for l in lignes:
                ref = l.get('ref', '')
                self.db.ajouter_ligne(date_op, l['libelle'], l['compte'], l['debit'], l['credit'], ref)
            return True
        except Exception as e:
            print(f"Erreur SQL: {e}")
            return False

    def obtenir_resultat(self):
        deb_7, cred_7 = self.db.solde_compte_commencant_par('7')
        total_produits = cred_7 - deb_7
        deb_6, cred_6 = self.db.solde_compte_commencant_par('6')
        total_charges = deb_6 - cred_6
        return total_produits, total_charges, (total_produits - total_charges)

    def obtenir_donnees_bilan_detaille(self):
        """ Prépare les données pour le PDF 2 pages """
        
        # --- PAGE 1 : ACTIF ---
        raw_actif = self.db.recuperer_soldes_par_classe(['2', '3', '5'])
        lignes_actif = []
        totaux_actif = {"brut": 0, "amort": 0, "net": 0}

        for compte, debit, credit in raw_actif:
            # Simplification : Débit = Brut, Crédit = Amortissement/Provision (pour l'actif)
            # Sauf pour la banque où tout est net, mais affichons brut/net pour simplifier
            brut = debit
            amort = credit
            net = brut - amort
            
            if abs(net) > 0.01 or brut > 0:
                lignes_actif.append({"compte": compte, "brut": brut, "amort": amort, "net": net})
                totaux_actif["brut"] += brut
                totaux_actif["amort"] += amort
                totaux_actif["net"] += net

        # --- PAGE 2 : PASSIF ---
        raw_passif = self.db.recuperer_soldes_par_classe(['1', '4'])
        lignes_passif = []
        total_passif = 0

        for compte, debit, credit in raw_passif:
            net = credit - debit # Passif = Créditeur
            if abs(net) > 0.01:
                lignes_passif.append({"compte": compte, "net": net})
                total_passif += net

        # Ajout du Résultat
        p, c, resultat = self.obtenir_resultat()
        lignes_passif.append({"compte": "RÉSULTAT NET", "net": resultat})
        total_passif += resultat

        return lignes_actif, totaux_actif, lignes_passif, total_passif
    
    def fermer(self):
        self.db.close()