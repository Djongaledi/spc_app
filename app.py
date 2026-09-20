import streamlit as st
import sqlite3
import pandas as pd
from database import DB_NAME
from utils_qr import generer_qr_code

st.set_page_config(page_title="Accueil & Espace Apprenant - SPC", page_icon="🎓", layout="wide")

# CSS personnalisé pour la barre latérale et l'interface
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 3px solid #F59E0B !important;
    }

    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] ul li div a {
        background-color: #1E293B !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-left: 4px solid transparent !important;
    }

    section[data-testid="stSidebar"] ul li div a[aria-current="page"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0F172A !important;
        font-weight: 800 !important;
        border-left: 4px solid #FFFFFF !important;
    }

    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        border: 2px solid #F59E0B;
    }

    .stButton>button {
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

st.subheader("🪪 Obtenir ma Carte & QR Code")
st.write("Entrez votre matricule pour afficher vos informations et votre QR Code de présence.")

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
                st.write(f"**Nom complet :** {nom_app}")
                st.write(f"**Sexe :** {sexe_app}")
                st.write(f"**Niveau / Groupe :** {niv_app}")

            with col_qr:
                qr_img = generer_qr_code(mat)
                st.image(qr_img, caption=f"QR Code de {nom_app}", width=200)
        else:
            st.error("❌ Aucun apprenant trouvé avec ce matricule.")
    else:
        st.warning("Veuillez saisir un matricule.")






