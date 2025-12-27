import sqlite3
import os

# Chemin dynamique vers le dossier data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class DatabaseManager:
    def __init__(self, db_name):
        self.db_path = os.path.join(DATA_DIR, db_name)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.creer_tables()
        self.verifier_et_maj_schema()

    def creer_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            libelle TEXT,
            compte_num INTEGER,
            debit REAL,
            credit REAL,
            reference TEXT
        )
        """)
        self.conn.commit()

    def verifier_et_maj_schema(self):
        """ Ajoute la colonne reference si elle manque (Migration) """
        try:
            self.cursor.execute("SELECT reference FROM journal LIMIT 1")
        except sqlite3.OperationalError:
            self.cursor.execute("ALTER TABLE journal ADD COLUMN reference TEXT")
            self.conn.commit()

    def ajouter_ligne(self, date, libelle, compte, debit, credit, ref=""):
        self.cursor.execute("""
            INSERT INTO journal (date, libelle, compte_num, debit, credit, reference) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date, libelle, compte, debit, credit, ref))
        self.conn.commit()

    def recuperer_journal(self):
        self.cursor.execute("SELECT date, libelle, compte_num, debit, credit, reference FROM journal ORDER BY date")
        return self.cursor.fetchall()

    def solde_compte_commencant_par(self, prefixe):
        query = f"SELECT SUM(debit), SUM(credit) FROM journal WHERE CAST(compte_num AS TEXT) LIKE '{prefixe}%'"
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        debit = result[0] if result[0] else 0.0
        credit = result[1] if result[1] else 0.0
        return debit, credit

    def recuperer_soldes_par_classe(self, classes):
        """ Pour le bilan détaillé : Groupe les sommes par numéro de compte """
        conditions = " OR ".join([f"CAST(compte_num AS TEXT) LIKE '{c}%'" for c in classes])
        query = f"""
            SELECT compte_num, SUM(debit), SUM(credit)
            FROM journal 
            WHERE {conditions}
            GROUP BY compte_num
            ORDER BY compte_num ASC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()