import streamlit as st
import datetime
from database import init_db, get_connection

st.set_page_config(page_title="SPC - Pointage", page_icon="📱", layout="centered")

# Initialisation de la base de données PostgreSQL
init_db()

st.title("Smart People Center (SPC)")
st.subheader("Système de Pointage par QR Code")

# Saisie du matricule
matricule = st.text_input("Scannez ou saisissez le matricule :")

if st.button("Enregistrer la présence"):
    if matricule:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Vérification si l'apprenant existe
        cursor.execute("SELECT nom, prenom FROM apprenants WHERE matricule = %s", (matricule,))
        apprenant = cursor.fetchone()
        
        if apprenant:
            maintenant = datetime.datetime.now()
            date_str = maintenant.strftime("%Y-%m-%d")
            heure_str = maintenant.strftime("%H:%M:%S")
            
            # Insertion du pointage
            cursor.execute(
                "INSERT INTO presences (matricule, date, heure, statut) VALUES (%s, %s, %s, %s)",
                (matricule, date_str, heure_str, "Présent")
            )
            conn.commit()
            st.success(f"Présence enregistrée pour {apprenant[1]} {apprenant[0]} à {heure_str} !")
        else:
            st.error("Matricule non reconnu dans le système.")
            
        cursor.close()
        conn.close()
    else:
        st.warning("Veuillez entrer un matricule.")
