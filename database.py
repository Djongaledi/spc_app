import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "spc_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table des apprenants
    c.execute('''
        CREATE TABLE IF NOT EXISTS apprenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE,
            nom TEXT,
            sexe TEXT,
            niveau TEXT,
            qr_code_path TEXT,
            date_inscription TEXT
        )
    ''')
    
    # Table des présences
    c.execute('''
        CREATE TABLE IF NOT EXISTS presences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT,
            date_presence TEXT,
            heure_presence TEXT,
            FOREIGN KEY (matricule) REFERENCES apprenants (matricule)
        )
    ''')
    
    # Suppression de l'ancienne table admin si elle existe sans 'id'
    c.execute("DROP TABLE IF EXISTS admin")
    
    # Reconstitution propre de la table Admin
    c.execute('''
        CREATE TABLE admin (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    # Insertion des identifiants personnalisés
    c.execute("INSERT INTO admin (username, password) VALUES ('DJONGALEDI', 'DjongaSime2026')")
    
    conn.commit()
    conn.close()

# Liste des niveaux officiels du SPC
NIVEAUX_SPC = [
    "First level down",
    "First level up",
    "Second level down",
    "Second level up",
    "Third level down",
    "Third level up"
]

if __name__ == "__main__":
    init_db()
    print("Base de données mise à jour avec succès !")
       






