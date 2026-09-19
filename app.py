import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
import os
import sys

# Importation du nom de la BDD et des niveaux
from database import DB_NAME, NIVEAUX_SPC
from utils_qr import generer_qr_code

st.set_page_config(page_title="Accueil & Espace Apprenant - SPC", page_icon="🎓", layout="wide")

# --- STYLES CSS PERSONNALISÉS (BARRE LATÉRALE ET EN-TÊTE) ---
st.markdown("""
    <style>
    /* Fond principal de l'application */
    .stApp { 
        background-color: #F8FAFC; 
    }

    /* Style complet de la Barre Latérale (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }

    /* Couleurs des textes et icônes dans la barre latérale */
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }

    /* Style des liens de navigation dans le menu latéral */
    section[data-testid="stSidebar"] ul li div a {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-left: 4px solid transparent !important;
        transition: all 0.3s ease !important;
    }

    /* Survol des liens du menu latéral */
    section[data-testid="stSidebar"] ul li div a:hover {
        background-color: #334155 !important;
        border-left: 4px solid #F59E0B !important;
    }

    /* Bouton de la PAGE ACTIVE (ACCUEIL & ESPACE APPRENANT) en orange */
    section[data-testid="stSidebar"] ul li div a[aria-current="page"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border-left: 4px solid #FFFFFF !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.25) !important;
    }

    /* En-tête principal */
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #F59E0B;
    }

    /* Boutons globaux */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1 style="margin:0; font-size:2.3rem; font-weight:800;">🎓 SMART PEOPLE CENTER (SPC)</h1>
        <p style="margin:5px 0 0 0; color:#FBBF24;">"if you're reach, be the bridge"</p>
    </div>
""", unsafe_allow_html=True)

tab_inscription, tab_carte = st.tabs(["📝 Formulaire d'Inscription", "🪪 Obtenir ma Carte & QR Code"])

# --- ONGLET 1 : INSCRIPTION AVEC BLOCAGE DES DOUBLONS ---
with tab_inscription:
    st.subheader("📝 Inscription des Apprenants")
    st.write("Veuillez remplir vos informations pour vous inscrire au centre.")

    with st.form("form_apprenant_inscription", clear_on_submit=True):
        nom = st.text_input("Nom complet (Nom, Postnom, Prénom)")
        sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
        niveau = st.selectbox("Niveau d'étude / Groupe", NIVEAUX_SPC)
        submitted = st.form_submit_button("💾 S'inscrire")

    if submitted:
        nom_clean = nom.strip()
        if nom_clean != "":
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            # Vérification stricte si le nom existe déjà dans la base
            c.execute("SELECT matricule FROM apprenants WHERE LOWER(nom) = LOWER(?)", (nom_clean,))
            existe_deja = c.fetchone()

            if existe_deja:
                st.error(f"⚠️ **Inscription impossible** : Un apprenant avec le nom **'{nom_clean}'** est déjà inscrit dans le système avec le matricule **{existe_deja[0]}**.")
                conn.close()
            else:
                matricule = f"SPC-{random.randint(1000, 9999)}"
                date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                c.execute(
                    "INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
                    (matricule, nom_clean, sexe, niveau, matricule, date_inscription)
                )
                conn.commit()
                conn.close()

                st.success(f"🎉 **Félicitations {nom_clean} !** Votre inscription est réussie.")
                st.info(f"📌 Votre matricule est : **{matricule}**. Conservez-le précieusement pour afficher votre carte.")
        else:
            st.error("❌ Veuillez saisir un nom valide avant de valider.")

# --- ONGLET 2 : OBTENIR SA CARTE ET QR CODE ---
with tab_carte:
    st.subheader("🪪 Récupérer sa Carte / QR Code")
    st.write("Entrez votre matricule pour afficher votre QR Code de présence.")

    mat_recherche = st.text_input("Entrez votre Matricule (ex: SPC-4825)").strip()
    if st.button("🔍 Chercher ma Carte"):
        if mat_recherche:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT matricule, nom, sexe, niveau FROM apprenants WHERE UPPER(matricule) = UPPER(?)", (mat_recherche,))
            apprenant = c.fetchone()
            conn.close()

            if apprenant:
                mat, nom_app, sexe_app, niv_app = apprenant
                st.success(f"Bienvenue, **{nom_app}** !")
                
                col_info, col_qr = st.columns(2)
                with col_info:
                    st.write(f"**Matricule :** {mat}")
                    st.write(f"**Nom :** {nom_app}")
                    st.write(f"**Sexe :** {sexe_app}")
                    st.write(f"**Niveau :** {niv_app}")

                with col_qr:
                    qr_img = generer_qr_code(mat)
                    st.image(qr_img, caption=f"QR Code de {nom_app}", width=200)
            else:
                st.error("❌ Aucun apprenant trouvé avec ce matricule.")
        else:
            st.warning("Veuillez saisir un matricule.")






