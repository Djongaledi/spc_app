import psycopg2
import streamlit as st

def get_connection():
    """Établit la connexion à la base de données PostgreSQL (Supabase)"""
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

def init_db():
    """Initialise les tables PostgreSQL si elles n'existent pas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table Apprenants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apprenants (
            matricule VARCHAR(50) PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            postnom VARCHAR(100),
            prenom VARCHAR(100),
            filiere VARCHAR(100),
            niveau VARCHAR(50),
            photo TEXT
        )
    ''')

    # Table Presences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presences (
            id SERIAL PRIMARY KEY,
            matricule VARCHAR(50) REFERENCES apprenants(matricule) ON DELETE CASCADE,
            date VARCHAR(20) NOT NULL,
            heure VARCHAR(20) NOT NULL,
            statut VARCHAR(20) NOT NULL
        )
    ''')

    # Table Admin
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
