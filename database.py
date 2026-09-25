import psycopg2
import streamlit as st

# Liste officielle des niveaux du SPC
NIVEAUX_SPC = [
    "First level down",
    "First level up",
    "Second level down",
    "Second level up",
    "Third level down",
    "Third level up",
    "Teacher"
]

def get_connection():
    """Établit la connexion à la base de données PostgreSQL (Supabase) via st.secrets."""
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

def init_db():
    """Initialise la structure des tables PostgreSQL sur Supabase."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Table des apprenants
    c.execute("""
        CREATE TABLE IF NOT EXISTS apprenants (
            id SERIAL PRIMARY KEY,
            matricule VARCHAR(50) UNIQUE NOT NULL,
            nom VARCHAR(255) NOT NULL,
            sexe VARCHAR(20),
            niveau VARCHAR(100),
            qr_code_path TEXT,
            date_inscription VARCHAR(100)
        );
    """)
    
    # 2. Table des présences
    c.execute("""
        CREATE TABLE IF NOT EXISTS presences (
            id SERIAL PRIMARY KEY,
            matricule VARCHAR(50) REFERENCES apprenants(matricule) ON DELETE CASCADE,
            date_presence VARCHAR(20) NOT NULL,
            heure_presence VARCHAR(20) NOT NULL
        );
    """)
    
    # 3. Table admin (Reconstitution propre avec identifiants personnalisés)
    c.execute("DROP TABLE IF EXISTS admin;")
    c.execute("""
        CREATE TABLE admin (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)
    
    # Insertion de vos identifiants administrateur personnalisés
    c.execute(
        "INSERT INTO admin (username, password) VALUES (%s, %s);",
        ('DJONGALEDI', 'DjongaSime2026')
    )
    
    conn.commit()
    c.close()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de données PostgreSQL/Supabase mise à jour avec succès !")
