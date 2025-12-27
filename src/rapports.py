from fpdf import FPDF
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
import os

BASE_EXP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
if not os.path.exists(BASE_EXP): os.makedirs(BASE_EXP)

NOMS_COMPTES = {
    1111: "Capital Social", 5141: "Banque (DH)", 5161: "Caisse",
    6111: "Achats marchandises", 6131: "Loyer", 7111: "Ventes marchandises",
    4411: "Fournisseurs", 3421: "Clients", 3455: "TVA Récupérable", 4455: "TVA Facturée"
}

class GenerateurRapport:
    def _dossier(self, nom):
        path = os.path.join(BASE_EXP, nom.strip())
        if not os.path.exists(path): os.makedirs(path)
        return path

    def exporter_journal_excel(self, data, nom):
        try:
            path = os.path.join(self._dossier(nom), f"Journal_{nom}.xlsx")
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Date", "Libellé", "Compte", "Débit", "Crédit", "Référence"])
            
            fill = PatternFill(start_color="203764", end_color="203764", fill_type="solid")
            font = Font(bold=True, color="FFFFFF")
            for c in ws[1]: c.fill = fill; c.font = font
            
            for row in data: ws.append(row)
            ws.column_dimensions['B'].width = 40
            wb.save(path)
            return path
        except: return None

    def generer_bilan_pdf(self, nom, l_act, t_act, l_pas, t_pas):
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            path = os.path.join(self._dossier(nom), f"Bilan_{nom}_{date}.pdf")
            pdf = FPDF()
            
            # Page 1 : Actif
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"BILAN ACTIF - {nom}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_fill_color(220, 220, 220)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(80, 10, "COMPTE", 1, 0, 'C', 1); pdf.cell(35, 10, "BRUT", 1, 0, 'C', 1)
            pdf.cell(35, 10, "AMORT", 1, 0, 'C', 1); pdf.cell(35, 10, "NET", 1, 1, 'C', 1)
            
            pdf.set_font("Arial", size=10)
            for l in l_act:
                n = NOMS_COMPTES.get(l['compte'], str(l['compte']))
                pdf.cell(80, 8, f"{l['compte']} - {n}", 1)
                pdf.cell(35, 8, f"{l['brut']:.2f}", 1, 0, 'R')
                pdf.cell(35, 8, f"{l['amort']:.2f}", 1, 0, 'R')
                pdf.cell(35, 8, f"{l['net']:.2f}", 1, 1, 'R')
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(80, 10, "TOTAL ACTIF", 1, 0, 'C', 1)
            pdf.cell(35, 10, f"{t_act['brut']:.2f}", 1, 0, 'R', 1)
            pdf.cell(35, 10, f"{t_act['amort']:.2f}", 1, 0, 'R', 1)
            pdf.cell(35, 10, f"{t_act['net']:.2f}", 1, 1, 'R', 1)

            # Page 2 : Passif
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"BILAN PASSIF - {nom}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(130, 10, "COMPTE", 1, 0, 'C', 1); pdf.cell(55, 10, "NET", 1, 1, 'C', 1)
            
            pdf.set_font("Arial", size=10)
            for l in l_pas:
                if l['compte'] == "RÉSULTAT NET": n = "RESULTAT NET"
                else: n = NOMS_COMPTES.get(l['compte'], str(l['compte']))
                pdf.cell(130, 8, f"{l['compte']} - {n}", 1)
                pdf.cell(55, 8, f"{l['net']:.2f}", 1, 1, 'R')
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(130, 10, "TOTAL PASSIF", 1, 0, 'C', 1)
            pdf.cell(55, 10, f"{t_pas:.2f}", 1, 1, 'R', 1)
            
            pdf.output(path)
            return path
        except: return None