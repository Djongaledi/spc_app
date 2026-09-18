import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
from database import DB_NAME, NIVEAUX_SPC
from utils_qr import generer_qr_code

# Configuration de la page
st.set_page_config(
    page_title="Smart People Center (SPC)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Correction CSS : Menu latéral lisible et style global
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    /* MENU LATÉRAL - Visibilité optimale */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] a {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        border-left: 4px solid #F59E0B !important;
        margin-bottom: 10px !important;
    }

    section[data-testid="stSidebar"] a:hover {
        background-color: #F59E0B !important;
        color: #0F172A !important;
    }

    /* Style des boutons principal et téléchargement */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        width: 100%;
    }

    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        padding: 25px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #F59E0B;
    }
    .header-title { font-size: 2.2rem; font-weight: 800; }
    .header-subtitle { font-size: 1.1rem; color: #FBBF24; font-style: italic; }

    /* Cartes */
    .custom-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Barre latérale
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 10px 0;">
            <h2 style="color:#F59E0B !important; margin:0; font-size:1.3rem;">📍 NAVIGATION</h2>
            <p style="font-size:0.8rem; color:#CBD5E1 !important;">Smart People Center</p>
        </div>
        <hr style="border-color:#334155; margin-bottom: 15px;">
    """, unsafe_allow_html=True)

# En-tête principal
st.markdown("""
    <div class="header-banner">
        <div class="header-title">🎓 Smart People Center (SPC)</div>
        <div class="header-subtitle">"if you're reach, be the bridge"</div>
    </div>
""", unsafe_allow_html=True)

# Disposition en 2 colonnes
col_inscription, col_admin_info = st.columns([3, 2])

# --- COLONNE DE GAUCHE : CRÉATION DE PROFIL DIRECTE ---
with col_inscription:
    st.markdown("""
        <div class="custom-card" style="border-left: 5px solid #F59E0B;">
            <h3 style="color:#1E3A8A; margin-top:0;">📝 Créer Mon Profil Apprenant</h3>
            <p style="color:#64748B; font-size:0.9rem;">Remplissez le formulaire ci-dessous pour générer automatiquement votre matricule et votre badge QR Code.</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

    with st.form("form_creation_profil_accueil", clear_on_submit=False):
        nom_apprenant = st.text_input("Nom complet (Prénom et Nom)", placeholder="Ex: Jean Dupont")
        sexe_apprenant = st.selectbox("Sexe", ["Masculin", "Féminin"])
        niveau_apprenant = st.selectbox("Niveau / Classe", NIVEAUX_SPC)
        
        btn_submit = st.form_submit_button("🚀 Valider & Générer Mon QR Code")

    if btn_submit:
        if nom_apprenant.strip() != "":
            # Génération automatique du matricule unique
            matricule_genere = f"SPC-{random.randint(1000, 9999)}"
            date_inscription = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Enregistrement dans SQLite
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO apprenants (matricule, nom, sexe, niveau, qr_code_path, date_inscription) VALUES (?, ?, ?, ?, ?, ?)",
                (matricule_genere, nom_apprenant, sexe_apprenant, niveau_apprenant, matricule_genere, date_inscription)
            )
            conn.commit()
            conn.close()

            st.balloons()
            st.success(f"🎉 Profil créé avec succès ! Votre matricule est : **{matricule_genere}**")

            # Génération du QR code en binaire
            qr_data = generer_qr_code(matricule_genere)

            # Affichage du profil et du bouton de téléchargement
            st.markdown("---")
            col_qr_img, col_qr_details = st.columns([1, 2])
            
            with col_qr_img:
                st.image(qr_data, caption=f"QR Code: {matricule_genere}", width=180)
                st.download_button(
                    label="📥 Télécharger Mon QR Code",
                    data=qr_data,
                    file_name=f"QR_Code_{matricule_genere}.png",
                    mime="image/png"
                )

            with col_qr_details:
                st.markdown(f"### 🪪 Vos Informations :")
                st.markdown(f"- **Nom :** {nom_apprenant}")
                st.markdown(f"- **Matricule :** `{matricule_genere}`")
                st.markdown(f"- **Niveau :** {niveau_apprenant}")
                st.info("💡 Enregistrez votre QR Code sur votre téléphone pour faire scanner votre présence à l'entrée.")
        else:
            st.warning("⚠️ Veuillez entrer votre nom complet avant de valider.")

# --- COLONNE DE DROITE : ESPACE ADMINISTRATION & INFOS ---
with col_admin_info:
    st.markdown("""
        <div class="custom-card" style="border-left: 5px solid #1E3A8A;">
            <h3 style="color:#1E3A8A; margin-top:0;">🔵 Espace Administration</h3>
            <p style="color:#64748B; font-size:0.9rem;">Réservé au personnel et administrateurs pour la gestion des présences.</p>
            <ul style="color:#475569; font-size:0.88rem; padding-left: 20px;">
                <li>Scan automatique des QR Codes à l'entrée</li>
                <li>Consultation et recherche des apprenants</li>
                <li>Statistiques globales et rapports PDF</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)







