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
        if abs(td - tc) > 0.01: return False
        try:
            for l in lignes:
                self.db.ajouter_ligne(date, l['libelle'], l['compte'], l['debit'], l['credit'], l.get('ref',''))
            return True
        except: return False

    def obtenir_resultat(self):
        d7, c7 = self.db.solde_compte_commencant_par('7')
        d6, c6 = self.db.solde_compte_commencant_par('6')
        prod = c7 - d7
        charg = d6 - c6
        return prod, charg, (prod - charg)

    def obtenir_donnees_bilan_detaille(self):
        # ACTIF
        raw_actif = self.db.recuperer_soldes_par_classe(['2', '3', '5'])
        l_actif = []
        t_actif = {"brut": 0, "amort": 0, "net": 0}
        for cpt, d, c in raw_actif:
            net = d - c
            if abs(net) > 0.01 or d > 0:
                l_actif.append({"compte": cpt, "brut": d, "amort": c, "net": net})
                t_actif["brut"] += d; t_actif["amort"] += c; t_actif["net"] += net
        
        # PASSIF
        raw_passif = self.db.recuperer_soldes_par_classe(['1', '4'])
        l_passif = []
        t_passif = 0
        for cpt, d, c in raw_passif:
            net = c - d
            if abs(net) > 0.01:
                l_passif.append({"compte": cpt, "net": net})
                t_passif += net
        
        # Résultat
        p, c, res = self.obtenir_resultat()
        l_passif.append({"compte": "RÉSULTAT NET", "net": res})
        t_passif += res
        
        return l_actif, t_actif, l_passif, t_passif

    def fermer(self):
        self.db.close()